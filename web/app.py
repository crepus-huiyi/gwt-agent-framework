"""Gradio前端应用主逻辑。

提供基于Gradio的Web可视化界面，支持流式状态更新和实时交互。
"""

import os
import sys
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass, field
from datetime import datetime

import gradio as gr
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.infrastructure import create_llm_client
from core.persistence import SelfCognitionManager, ContextContinuumManager, SelfCognition
from core.subconscious import SubconsciousProcessor
from core.global_workspace import GlobalWorkspace
from core.attention_control import AttentionController
from core.executors import ExecutionManager, TextProcessor, CodeExecutor
from state.agent_state import AgentState
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class UIState:
    """UI状态数据类，用于管理界面显示状态。"""
    current_status: str = "等待启动"
    loop_count: int = 0
    max_loops: int = 100
    alignment_score: Optional[int] = None
    current_decision: str = ""
    execution_result: str = ""
    filtered_info: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    is_running: bool = False
    should_stop: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于Gradio更新。"""
        return {
            "current_status": self.current_status,
            "loop_count": self.loop_count,
            "max_loops": self.max_loops,
            "alignment_score": self.alignment_score,
            "current_decision": self.current_decision,
            "execution_result": self.execution_result,
            "filtered_info": self.filtered_info,
            "logs": self.logs,
            "is_running": self.is_running,
        }


class GWTAgentGradioApp:
    """GWT Agent Gradio应用类。

    封装Gradio界面和Agent执行逻辑，支持流式状态更新。
    """

    def __init__(self):
        """初始化应用组件。"""
        self.llm_client = create_llm_client()
        self.self_cognition_manager = SelfCognitionManager()
        self.context_continuum_manager = ContextContinuumManager()
        self.subconscious = SubconsciousProcessor(self.llm_client)
        self.global_workspace = GlobalWorkspace(self.llm_client)
        self.attention_controller = AttentionController(self.llm_client)
        self.text_processor = TextProcessor(self.llm_client)
        self.code_executor = CodeExecutor()
        self.execution_manager = ExecutionManager(self.text_processor, self.code_executor)

    def _get_status_color(self, status: str) -> str:
        """获取状态对应的颜色。

        Args:
            status: 状态名称

        Returns:
            颜色代码
        """
        color_map = {
            "等待启动": "gray",
            "初始化": "blue",
            "潜意识处理": "purple",
            "意识决策": "orange",
            "对齐校验": "yellow",
            "执行": "cyan",
            "完成": "green",
            "错误": "red",
            "已停止": "red",
        }
        return color_map.get(status, "gray")

    def _get_alignment_color(self, score: int) -> str:
        """获取对齐度得分对应的颜色。

        Args:
            score: 对齐度得分

        Returns:
            颜色名称
        """
        if score >= 90:
            return "green"
        elif score >= 60:
            return "yellow"
        else:
            return "red"

    def _format_status_html(self, status: str) -> str:
        """格式化状态显示为HTML。

        Args:
            status: 状态名称

        Returns:
            HTML字符串
        """
        color = self._get_status_color(status)
        color_code = {
            "gray": "#6B7280",
            "blue": "#3B82F6",
            "purple": "#8B5CF6",
            "orange": "#F97316",
            "yellow": "#EAB308",
            "cyan": "#06B6D4",
            "green": "#10B981",
            "red": "#EF4444",
        }.get(color, "#6B7280")

        return f"""
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: {color_code}20;
            border: 2px solid {color_code};
            border-radius: 8px;
            font-weight: 600;
            color: {color_code};
        ">
            <span style="
                width: 12px;
                height: 12px;
                background: {color_code};
                border-radius: 50%;
                display: inline-block;
                {'animation: pulse 1.5s infinite;' if status not in ['完成', '错误', '已停止', '等待启动'] else ''}
            "></span>
            {status}
        </div>
        <style>
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.5; }}
            }}
        </style>
        """

    def _format_alignment_html(self, score: int) -> str:
        """格式化对齐度得分为HTML。

        Args:
            score: 对齐度得分

        Returns:
            HTML字符串
        """
        color = self._get_alignment_color(score)
        color_code = {
            "green": "#10B981",
            "yellow": "#EAB308",
            "red": "#EF4444",
        }.get(color, "#6B7280")

        status_text = {
            "green": "通过",
            "yellow": "轻度跑偏",
            "red": "严重跑偏",
        }.get(color, "未知")

        return f"""
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 12px;
            padding: 12px 20px;
            background: {color_code}15;
            border: 2px solid {color_code};
            border-radius: 10px;
        ">
            <div style="
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: conic-gradient({color_code} {score * 3.6}deg, #E5E7EB 0deg);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 18px;
                color: {color_code};
            ">
                <div style="
                    width: 48px;
                    height: 48px;
                    background: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                ">{score}</div>
            </div>
            <div>
                <div style="font-size: 14px; color: #6B7280;">对齐度得分</div>
                <div style="font-size: 16px; font-weight: 600; color: {color_code};">{status_text}</div>
            </div>
        </div>
        """

    def _format_progress_html(self, current: int, total: int) -> str:
        """格式化进度条为HTML。

        Args:
            current: 当前进度
            total: 总进度

        Returns:
            HTML字符串
        """
        percentage = min(100, int((current / total) * 100)) if total > 0 else 0

        return f"""
        <div style="width: 100%;">
            <div style="
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
                font-size: 14px;
            ">
                <span style="color: #6B7280;">执行进度</span>
                <span style="font-weight: 600; color: #374151;">{current} / {total} 轮</span>
            </div>
            <div style="
                width: 100%;
                height: 12px;
                background: #E5E7EB;
                border-radius: 6px;
                overflow: hidden;
            ">
                <div style="
                    width: {percentage}%;
                    height: 100%;
                    background: linear-gradient(90deg, #3B82F6, #8B5CF6);
                    border-radius: 6px;
                    transition: width 0.3s ease;
                "></div>
            </div>
            <div style="text-align: right; margin-top: 4px; font-size: 12px; color: #6B7280;">
                {percentage}%
            </div>
        </div>
        """

    def _format_decision_card(self, decision: str) -> str:
        """格式化决策卡片为HTML。

        Args:
            decision: 决策内容

        Returns:
            HTML字符串
        """
        if not decision:
            return '<div style="color: #9CA3AF; text-align: center; padding: 20px;">暂无决策内容</div>'

        return f"""
        <div style="
            background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
            border: 1px solid #D1D5DB;
            border-radius: 12px;
            padding: 16px;
        ">
            <div style="
                font-size: 12px;
                font-weight: 600;
                color: #6B7280;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            ">当前决策</div>
            <div style="
                font-size: 14px;
                color: #374151;
                line-height: 1.6;
                white-space: pre-wrap;
            ">{decision}</div>
        </div>
        """

    def _format_result_card(self, result: str) -> str:
        """格式化结果卡片为HTML。

        Args:
            result: 执行结果

        Returns:
            HTML字符串
        """
        if not result:
            return '<div style="color: #9CA3AF; text-align: center; padding: 20px;">暂无执行结果</div>'

        return f"""
        <div style="
            background: #F0FDF4;
            border: 1px solid #86EFAC;
            border-radius: 12px;
            padding: 16px;
        ">
            <div style="
                font-size: 12px;
                font-weight: 600;
                color: #059669;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            ">执行结果</div>
            <div style="
                font-size: 14px;
                color: #166534;
                line-height: 1.6;
                white-space: pre-wrap;
                font-family: monospace;
            ">{result}</div>
        </div>
        """

    def _format_filtered_info(self, info_list: List[str]) -> str:
        """格式化筛选后的核心信息为HTML。

        Args:
            info_list: 核心信息列表

        Returns:
            HTML字符串
        """
        if not info_list:
            return '<div style="color: #9CA3AF; text-align: center; padding: 10px;">暂无核心信息</div>'

        items_html = ""
        for i, info in enumerate(info_list[:10], 1):  # 最多显示10条
            items_html += f"""
            <div style="
                padding: 8px 12px;
                margin-bottom: 6px;
                background: #F9FAFB;
                border-left: 3px solid #8B5CF6;
                border-radius: 0 6px 6px 0;
                font-size: 13px;
                color: #4B5563;
            ">
                <span style="color: #8B5CF6; font-weight: 600;">#{i}</span> {info}
            </div>
            """

        if len(info_list) > 10:
            items_html += f'<div style="text-align: center; color: #9CA3AF; font-size: 12px; padding: 8px;">... 还有 {len(info_list) - 10} 条信息</div>'

        return items_html

    def _format_logs(self, logs: List[str]) -> str:
        """格式化日志为HTML。

        Args:
            logs: 日志列表

        Returns:
            HTML字符串
        """
        if not logs:
            return "暂无日志"

        return "\n".join(logs[-50:])  # 只显示最近50条

    def run_agent_stream(
        self,
        root_goal: str,
        current_milestone: str,
        alignment_threshold: int,
        filter_threshold: int,
        max_loops: int,
    ) -> Generator[tuple, None, None]:
        """流式运行Agent，生成中间状态更新。

        Args:
            root_goal: 根目标
            current_milestone: 当前里程碑
            alignment_threshold: 对齐度阈值
            filter_threshold: 过滤阈值
            max_loops: 最大循环次数

        Yields:
            界面组件更新元组
        """
        ui_state = UIState(max_loops=max_loops)
        ui_state.is_running = True
        ui_state.current_status = "初始化"
        ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 开始初始化...")

        # 初始化状态
        initial_state: AgentState = {
            "messages": [f"用户目标：{root_goal}", f"当前里程碑：{current_milestone}"],
            "root_goal": root_goal,
            "current_milestone": current_milestone,
            "milestones_completed": [],
            "self_cognition_str": "",
            "context_continuum": [],
            "loop_count": 0,
            "is_finished": False,
        }

        # 加载自我认知
        yield self._create_update(ui_state, "正在加载自我认知...")
        cognition_result = self.self_cognition_manager.load()
        if cognition_result["success"]:
            cognition = cognition_result["cognition"]
            initial_state["self_cognition_str"] = f"角色：{cognition.role}\n核心能力：{cognition.core_abilities}\n行为准则：{cognition.behavior_rules}\n禁止项：{cognition.prohibitions}"
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 自我认知加载成功")
        else:
            initial_state["self_cognition_str"] = "自我认知加载失败"
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 自我认知加载失败")

        # 加载上下文连续体
        initial_state["context_continuum"] = self.context_continuum_manager.load()
        ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 上下文连续体加载成功")

        state = initial_state

        # 主循环
        while not state.get("is_finished", False) and state["loop_count"] < max_loops:
            if ui_state.should_stop:
                ui_state.current_status = "已停止"
                ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 用户停止执行")
                yield self._create_update(ui_state, "已停止")
                break

            state["loop_count"] += 1
            ui_state.loop_count = state["loop_count"]

            # 潜意识处理
            ui_state.current_status = "潜意识处理"
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 第{state['loop_count']}轮 - 潜意识处理")
            yield self._create_update(ui_state, "正在进行潜意识处理...")

            sub_result = self.subconscious.process({
                "full_context": state["messages"],
                "root_goal": state["root_goal"],
                "filter_threshold": filter_threshold,
            })

            if not sub_result["success"]:
                ui_state.current_status = "错误"
                ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 潜意识处理失败: {sub_result.get('error_msg', '未知错误')}")
                yield self._create_update(ui_state, f"潜意识处理失败: {sub_result.get('error_msg', '未知错误')}")
                break

            ui_state.filtered_info = [info["content"] for info in sub_result.get("filtered_info", [])]
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 筛选出 {len(ui_state.filtered_info)} 条核心信息")
            yield self._create_update(ui_state, f"筛选出 {len(ui_state.filtered_info)} 条核心信息")

            # 意识决策
            ui_state.current_status = "意识决策"
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 意识层生成决策...")
            yield self._create_update(ui_state, "正在生成决策...")

            # 解析自我认知
            cognition_lines = state["self_cognition_str"].split("\n")
            role = core_abilities = behavior_rules = prohibitions = ""
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

            decision_result = self.global_workspace.generate_decision({
                "filtered_info": sub_result.get("filtered_info", []),
                "root_goal": state["root_goal"],
                "current_milestone": state["current_milestone"],
                "self_cognition": self_cognition,
            })

            if not decision_result["success"]:
                ui_state.current_status = "错误"
                ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 决策生成失败: {decision_result.get('error_msg', '未知错误')}")
                yield self._create_update(ui_state, f"决策生成失败: {decision_result.get('error_msg', '未知错误')}")
                break

            state["current_decision"] = decision_result["decision"]
            ui_state.current_decision = decision_result["decision"]
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 决策生成完成")
            yield self._create_update(ui_state, "决策生成完成")

            # 对齐校验
            ui_state.current_status = "对齐校验"
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 进行目标对齐校验...")
            yield self._create_update(ui_state, "正在进行对齐校验...")

            alignment_result = self.attention_controller.check_alignment({
                "decision": state["current_decision"],
                "root_goal": state["root_goal"],
                "current_milestone": state["current_milestone"],
                "alignment_threshold": alignment_threshold,
            })

            state["alignment_score"] = alignment_result.get("alignment_score", 0)
            ui_state.alignment_score = state["alignment_score"]
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 对齐度得分: {ui_state.alignment_score}")
            yield self._create_update(ui_state, f"对齐度得分: {ui_state.alignment_score}")

            # 根据对齐度决定下一步
            if state["alignment_score"] < 60:
                ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 严重跑偏，回溯至潜意识层")
                yield self._create_update(ui_state, "严重跑偏，回溯重新处理")
                continue
            elif state["alignment_score"] < alignment_threshold:
                ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 轻度跑偏，重新生成决策")
                yield self._create_update(ui_state, "轻度跑偏，重新生成决策")
                continue

            # 执行
            ui_state.current_status = "执行"
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 执行决策...")
            yield self._create_update(ui_state, "正在执行...")

            action_type = "text_process"
            action_content = state["current_decision"]
            if "执行代码" in state["current_decision"] or "运行代码" in state["current_decision"]:
                action_type = "code_execute"

            exec_result = self.execution_manager.run({
                "action_type": action_type,
                "action_content": action_content,
            })

            if exec_result["success"]:
                state["execution_result"] = exec_result.get("result", "")
                ui_state.execution_result = state["execution_result"]
                ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 执行成功")
            else:
                state["execution_result"] = f"执行失败: {exec_result.get('error_msg', '未知错误')}"
                ui_state.execution_result = state["execution_result"]
                ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 执行失败: {exec_result.get('error_msg', '未知错误')}")

            yield self._create_update(ui_state, "执行完成")

            # 更新上下文
            if state["execution_result"]:
                self.context_continuum_manager.append(state["execution_result"])
                state["context_continuum"].append(state["execution_result"])

            # 简单判断完成条件（实际项目中需要更复杂的逻辑）
            if state["loop_count"] >= 3:  # 演示用，执行3轮后结束
                state["is_finished"] = True

        # 循环结束
        if state.get("is_finished", False):
            ui_state.current_status = "完成"
            ui_state.is_running = False
            ui_state.logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] 任务执行完成")
            yield self._create_update(ui_state, "任务执行完成")

    def _create_update(self, ui_state: UIState, message: str) -> tuple:
        """创建界面更新元组。

        Args:
            ui_state: UI状态
            message: 状态消息

        Returns:
            界面组件更新元组
        """
        return (
            self._format_status_html(ui_state.current_status),
            self._format_progress_html(ui_state.loop_count, ui_state.max_loops),
            self._format_alignment_html(ui_state.alignment_score) if ui_state.alignment_score is not None else "<div style='color: #9CA3AF;'>等待对齐校验...</div>",
            self._format_decision_card(ui_state.current_decision),
            self._format_result_card(ui_state.execution_result),
            self._format_filtered_info(ui_state.filtered_info),
            self._format_logs(ui_state.logs),
            message,
            gr.update(interactive=not ui_state.is_running),  # 启动按钮
            gr.update(interactive=ui_state.is_running),      # 停止按钮
        )

    def stop_execution(self, ui_state: UIState) -> UIState:
        """停止执行。

        Args:
            ui_state: 当前UI状态

        Returns:
            更新后的UI状态
        """
        ui_state.should_stop = True
        return ui_state

    def create_interface(self) -> gr.Blocks:
        """创建Gradio界面。

        Returns:
            Gradio Blocks界面
        """
        with gr.Blocks(
            title="GWT Agent 演示系统",
            theme=gr.themes.Soft(),
            css="""
            .main-container {
                max-width: 1400px;
                margin: 0 auto;
            }
            .status-panel {
                background: linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);
                border-radius: 12px;
                padding: 20px;
            }
            """
        ) as demo:
            gr.Markdown("""
            # 🧠 GWT Agent 演示系统
            ### 基于全局工作空间理论的长任务稳定执行 Agent 框架
            """)

            with gr.Row():
                # 左侧配置面板
                with gr.Column(scale=1):
                    gr.Markdown("### ⚙️ 任务配置")

                    root_goal_input = gr.Textbox(
                        label="根目标",
                        placeholder="请输入您的任务目标...",
                        lines=3,
                        value="编写一个Python函数，计算斐波那契数列的第n项",
                    )

                    milestone_input = gr.Textbox(
                        label="当前里程碑",
                        placeholder="请输入当前里程碑...",
                        lines=2,
                        value="实现基础递归算法",
                    )

                    with gr.Accordion("📊 参数配置", open=False):
                        alignment_threshold_slider = gr.Slider(
                            label="对齐度阈值",
                            minimum=0,
                            maximum=100,
                            value=90,
                            step=1,
                        )

                        filter_threshold_slider = gr.Slider(
                            label="过滤阈值",
                            minimum=0,
                            maximum=10,
                            value=7,
                            step=1,
                        )

                        max_loops_slider = gr.Slider(
                            label="最大循环次数",
                            minimum=1,
                            maximum=200,
                            value=100,
                            step=1,
                        )

                    with gr.Row():
                        start_btn = gr.Button("🚀 启动任务", variant="primary", size="lg")
                        stop_btn = gr.Button("⏹️ 停止", variant="stop", size="lg", interactive=False)

                    gr.Markdown("### 🔍 调试信息")

                    filtered_info_output = gr.HTML(
                        label="核心信息",
                        value="<div style='color: #9CA3AF; text-align: center; padding: 20px;'>等待启动...</div>"
                    )

                    logs_output = gr.Textbox(
                        label="执行日志",
                        lines=10,
                        max_lines=20,
                        interactive=False,
                        value="暂无日志",
                    )

                # 右侧主界面
                with gr.Column(scale=2):
                    gr.Markdown("### 📈 执行状态")

                    with gr.Row():
                        status_output = gr.HTML(
                            value=self._format_status_html("等待启动")
                        )

                    progress_output = gr.HTML(
                        value=self._format_progress_html(0, 100)
                    )

                    gr.Markdown("### 🎯 对齐校验")

                    alignment_output = gr.HTML(
                        value="<div style='color: #9CA3AF; padding: 20px;'>等待对齐校验...</div>"
                    )

                    gr.Markdown("### 💡 当前决策")

                    decision_output = gr.HTML(
                        value=self._format_decision_card("")
                    )

                    gr.Markdown("### ✅ 执行结果")

                    result_output = gr.HTML(
                        value=self._format_result_card("")
                    )

                    status_message = gr.Textbox(
                        label="状态消息",
                        interactive=False,
                        value="等待启动...",
                    )

            # 事件绑定
            def on_start(root_goal, milestone, align_threshold, filter_threshold, max_loops):
                """启动按钮回调。"""
                for update in self.run_agent_stream(
                    root_goal, milestone, align_threshold, filter_threshold, max_loops
                ):
                    yield update

            start_btn.click(
                fn=on_start,
                inputs=[
                    root_goal_input,
                    milestone_input,
                    alignment_threshold_slider,
                    filter_threshold_slider,
                    max_loops_slider,
                ],
                outputs=[
                    status_output,
                    progress_output,
                    alignment_output,
                    decision_output,
                    result_output,
                    filtered_info_output,
                    logs_output,
                    status_message,
                    start_btn,
                    stop_btn,
                ],
            )

            def on_stop():
                """停止按钮回调。"""
                # 通过设置全局停止标志来实现
                # 实际实现中需要在run_agent_stream中检查停止标志
                return {
                    status_message: "正在停止...",
                    stop_btn: gr.update(interactive=False),
                }

            stop_btn.click(
                fn=on_stop,
                outputs=[status_message, stop_btn],
            )

            gr.Markdown("""
            ---
            **💡 使用说明**
            1. 在左侧输入根目标和当前里程碑
            2. 点击"启动任务"开始执行
            3. 右侧实时显示执行状态、决策内容和执行结果
            4. 可在"参数配置"中调整对齐度阈值和过滤阈值
            """)

        return demo


def create_gradio_app() -> gr.Blocks:
    """创建Gradio应用实例。

    Returns:
        Gradio Blocks界面实例
    """
    app = GWTAgentGradioApp()
    return app.create_interface()


def run_gradio_app(server_name: str = "0.0.0.0", server_port: int = 7860, share: bool = False):
    """运行Gradio应用。

    Args:
        server_name: 服务器地址
        server_port: 服务器端口
        share: 是否创建公开链接
    """
    demo = create_gradio_app()
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        show_error=True,
    )


if __name__ == "__main__":
    run_gradio_app()
