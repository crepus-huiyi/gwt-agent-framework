import os
from dotenv import load_dotenv

from core.infrastructure import create_llm_client
from core.persistence import SelfCognitionManager, ContextContinuumManager
from core.subconscious import SubconsciousProcessor
from core.global_workspace import GlobalWorkspace
from core.attention_control import AttentionController
from core.executors import ExecutionManager, TextProcessor, CodeExecutor
from state.graph import build_agent_graph
from state.agent_state import AgentState
from utils.logger import get_logger

# 加载环境变量
load_dotenv()

logger = get_logger(__name__)

def main():
    """主函数，启动 Agent 框架"""
    logger.info("启动 GWT Agent 框架")
    
    # 1. 初始化各模块
    llm_client = create_llm_client()
    self_cognition_manager = SelfCognitionManager()
    context_continuum_manager = ContextContinuumManager()
    subconscious = SubconsciousProcessor(llm_client)
    global_workspace = GlobalWorkspace(llm_client)
    attention_controller = AttentionController(llm_client)
    text_processor = TextProcessor(llm_client)
    code_executor = CodeExecutor()
    execution_manager = ExecutionManager(text_processor, code_executor)
    
    # 2. 构建状态图
    agent_graph = build_agent_graph(
        subconscious=subconscious,
        global_workspace=global_workspace,
        attention_controller=attention_controller,
        execution_manager=execution_manager,
        self_cognition_manager=self_cognition_manager,
        context_continuum_manager=context_continuum_manager
    )
    
    # 3. 获取用户输入
    print("欢迎使用 GWT Agent 框架！")
    print("请输入您的任务目标：")
    root_goal = input("目标：").strip()
    print("请输入当前里程碑：")
    current_milestone = input("里程碑：").strip()
    
    # 4. 初始化状态
    initial_state: AgentState = {
        "messages": [f"用户目标：{root_goal}", f"当前里程碑：{current_milestone}"],
        "root_goal": root_goal,
        "current_milestone": current_milestone,
        "milestones_completed": [],
        "self_cognition_str": "",
        "context_continuum": [],
        "loop_count": 0,
        "is_finished": False
    }
    
    # 5. 运行状态图
    logger.info("开始执行任务")
    try:
        result = agent_graph.invoke(initial_state)
        logger.info("任务执行完成")
        
        # 6. 输出结果
        print("\n任务执行结果：")
        if result.get("execution_result"):
            print(result["execution_result"])
        else:
            print("任务执行完成，但没有返回结果")
    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}")
        print(f"任务执行失败: {str(e)}")

if __name__ == "__main__":
    main()