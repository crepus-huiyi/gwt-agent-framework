from langgraph.graph import StateGraph, END

from core.subconscious import SubconsciousProcessor
from core.global_workspace import GlobalWorkspace
from core.attention_control import AttentionController
from core.executors import ExecutionManager
from core.persistence import SelfCognitionManager, ContextContinuumManager
from state.agent_state import AgentState
from utils.logger import get_logger

logger = get_logger(__name__)

def build_agent_graph(
    subconscious: SubconsciousProcessor,
    global_workspace: GlobalWorkspace,
    attention_controller: AttentionController,
    execution_manager: ExecutionManager,
    self_cognition_manager: SelfCognitionManager,
    context_continuum_manager: ContextContinuumManager
) -> StateGraph:
    """构建 Agent 状态图。

    Args:
        subconscious: 潜意识处理器实例
        global_workspace: 全局工作空间实例
        attention_controller: 注意力控制器实例
        execution_manager: 执行管理器实例
        self_cognition_manager: 自我认知管理器实例
        context_continuum_manager: 上下文连续体管理器实例

    Returns:
        StateGraph: 编译后的状态图
    """
    graph = StateGraph(AgentState)

    # 1. 节点定义
    def init_node(state: AgentState) -> AgentState:
        """初始化状态节点"""
        logger.info("初始化状态")
        state["loop_count"] = 0
        state["is_finished"] = False
        # 加载自我认知
        cognition_result = self_cognition_manager.load()
        if cognition_result["success"]:
            cognition = cognition_result["cognition"]
            state["self_cognition_str"] = f"角色：{cognition.role}\n核心能力：{cognition.core_abilities}\n行为准则：{cognition.behavior_rules}\n禁止项：{cognition.prohibitions}"
        else:
            state["self_cognition_str"] = "自我认知加载失败"
        # 加载上下文连续体
        state["context_continuum"] = context_continuum_manager.load()
        return state

    def subconscious_node(state: AgentState) -> AgentState:
        """潜意识处理节点"""
        logger.info(f"潜意识层处理，第{state['loop_count']}轮")
        result = subconscious.process({
            "full_context": state["messages"],
            "root_goal": state["root_goal"]
        })
        if not result["success"]:
            state["is_finished"] = True
            return state
        # 将筛选后的信息存入 messages，供意识层使用
        filtered_info_str = "\n".join([info["content"] for info in result["filtered_info"]])
        state["messages"].append(f"[潜意识筛选] {filtered_info_str}")
        return state

    def conscious_decision_node(state: AgentState) -> AgentState:
        """意识决策生成节点"""
        logger.info("意识层生成决策")
        # 提取筛选后的信息
        filtered_info = []
        for message in state["messages"]:
            if message.startswith("[潜意识筛选]"):
                content = message[len("[潜意识筛选]"):].strip()
                for line in content.split("\n"):
                    if line.strip():
                        filtered_info.append({"content": line.strip()})
        # 生成决策
        from core.persistence import SelfCognition
        # 简单解析自我认知字符串
        cognition_lines = state["self_cognition_str"].split("\n")
        role = ""
        core_abilities = ""
        behavior_rules = ""
        prohibitions = ""
        for line in cognition_lines:
            if line.startswith("角色："):
                role = line[len("角色："):].strip()
            elif line.startswith("核心能力："):
                core_abilities = line[len("核心能力："):].strip()
            elif line.startswith("行为准则："):
                behavior_rules = line[len("行为准则："):].strip()
            elif line.startswith("禁止项："):
                prohibitions = line[len("禁止项："):].strip()
        self_cognition = SelfCognition(
            role=role,
            core_abilities=core_abilities,
            behavior_rules=behavior_rules,
            prohibitions=prohibitions
        )
        result = global_workspace.generate_decision({
            "filtered_info": filtered_info,
            "root_goal": state["root_goal"],
            "current_milestone": state["current_milestone"],
            "self_cognition": self_cognition
        })
        if not result["success"]:
            state["is_finished"] = True
            return state
        state["current_decision"] = result["decision"]
        return state

    def alignment_node(state: AgentState) -> AgentState:
        """目标对齐校验节点"""
        logger.info("目标对齐校验")
        result = attention_controller.check_alignment({
            "decision": state["current_decision"],
            "root_goal": state["root_goal"],
            "current_milestone": state["current_milestone"]
        })
        state["alignment_score"] = result["alignment_score"]
        return state

    def execute_node(state: AgentState) -> AgentState:
        """执行动作节点"""
        logger.info("执行动作")
        # 简单解析决策，提取动作类型和内容
        action_type = "text_process"
        action_content = state["current_decision"]
        # 如果决策包含代码执行指令，切换到代码执行
        if "执行代码" in state["current_decision"] or "运行代码" in state["current_decision"]:
            action_type = "code_execute"
        result = execution_manager.run({
            "action_type": action_type,
            "action_content": action_content
        })
        state["execution_result"] = result["result"] if result["success"] else result["error_msg"]
        return state

    def update_context_node(state: AgentState) -> AgentState:
        """更新上下文节点"""
        logger.info("更新上下文")
        # 追加执行结果到上下文连续体
        if state["execution_result"]:
            context_continuum_manager.append(state["execution_result"])
            state["context_continuum"].append(state["execution_result"])
        # 增加循环次数
        state["loop_count"] += 1
        # 简单判断是否完成（实际项目中需要更复杂的逻辑）
        if state["loop_count"] >= 100:
            state["is_finished"] = True
        return state

    def error_handler_node(state: AgentState) -> AgentState:
        """错误处理节点"""
        logger.error("进入错误处理")
        state["is_finished"] = True
        return state

    # 2. 节点注册
    graph.add_node("init", init_node)
    graph.add_node("subconscious", subconscious_node)
    graph.add_node("conscious_decision", conscious_decision_node)
    graph.add_node("alignment", alignment_node)
    graph.add_node("execute", execute_node)
    graph.add_node("update_context", update_context_node)
    graph.add_node("error_handler", error_handler_node)

    # 3. 边定义
    graph.set_entry_point("init")
    graph.add_edge("init", "subconscious")
    graph.add_edge("subconscious", "conscious_decision")
    graph.add_edge("conscious_decision", "alignment")
    
    # 条件边：对齐校验结果分支
    def alignment_router(state: AgentState) -> str:
        if state["alignment_score"] >= 90:
            return "execute"
        elif 60 <= state["alignment_score"] < 90:
            return "conscious_decision"
        else:
            return "subconscious"
    
    graph.add_conditional_edges(
        "alignment",
        alignment_router,
        {
            "execute": "execute",
            "conscious_decision": "conscious_decision",
            "subconscious": "subconscious"
        }
    )
    
    graph.add_edge("execute", "update_context")
    
    # 条件边：是否完成
    def should_finish(state: AgentState) -> str:
        if state["is_finished"] or state["loop_count"] >= 100:
            return END
        return "subconscious"
    
    graph.add_conditional_edges("update_context", should_finish)

    # 4. 异常处理边
    graph.add_edge("init", "error_handler")
    graph.add_edge("subconscious", "error_handler")
    graph.add_edge("conscious_decision", "error_handler")
    graph.add_edge("alignment", "error_handler")
    graph.add_edge("execute", "error_handler")
    graph.add_edge("update_context", "error_handler")

    return graph.compile()