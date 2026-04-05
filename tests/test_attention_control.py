import unittest
from unittest.mock import Mock, patch

from core.attention_control import AttentionController, AlignmentInput
from core.infrastructure import LLMOutput

class TestAttentionController(unittest.TestCase):
    """测试注意力控制器"""
    
    def setUp(self):
        """设置测试环境"""
        # 创建一个模拟的 LLM 客户端
        self.mock_llm_client = Mock()
        # 创建注意力控制器实例
        self.attention_controller = AttentionController(self.mock_llm_client)
    
    def test_check_alignment_high_score(self):
        """测试对齐度高的情况"""
        # 模拟 LLM 客户端返回高得分
        self.mock_llm_client.call.return_value = LLMOutput(
            success=True,
            content='{"score": 95, "reason": "决策与根目标高度相关"}'
        )
        
        # 准备输入数据
        input_data = AlignmentInput(
            decision="完成项目架构设计文档",
            root_goal="开发一个基于 GWT 理论的 Agent 框架",
            current_milestone="完成架构设计"
        )
        
        # 调用 check_alignment 方法
        result = self.attention_controller.check_alignment(input_data)
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["alignment_score"], 95)
        self.assertTrue(result["is_aligned"])
        self.assertIsNone(result["correction_hint"])
    
    def test_check_alignment_medium_score(self):
        """测试对齐度中等的情况"""
        # 模拟 LLM 客户端返回中等得分
        self.mock_llm_client.call.return_value = LLMOutput(
            success=True,
            content='{"score": 75, "reason": "决策与根目标相关，但需要更多细节"}'
        )
        
        # 准备输入数据
        input_data = AlignmentInput(
            decision="完成项目架构设计文档",
            root_goal="开发一个基于 GWT 理论的 Agent 框架",
            current_milestone="完成架构设计"
        )
        
        # 调用 check_alignment 方法
        result = self.attention_controller.check_alignment(input_data)
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["alignment_score"], 75)
        self.assertFalse(result["is_aligned"])
        self.assertIsNotNone(result["correction_hint"])
    
    def test_check_alignment_low_score(self):
        """测试对齐度低的情况"""
        # 模拟 LLM 客户端返回低得分
        self.mock_llm_client.call.return_value = LLMOutput(
            success=True,
            content='{"score": 45, "reason": "决策与根目标不相关"}'
        )
        
        # 准备输入数据
        input_data = AlignmentInput(
            decision="看电影",
            root_goal="开发一个基于 GWT 理论的 Agent 框架",
            current_milestone="完成架构设计"
        )
        
        # 调用 check_alignment 方法
        result = self.attention_controller.check_alignment(input_data)
        
        # 验证结果
        self.assertTrue(result["success"])
        self.assertEqual(result["alignment_score"], 45)
        self.assertFalse(result["is_aligned"])
        self.assertIsNotNone(result["correction_hint"])
    
    def test_check_alignment_llm_failure(self):
        """测试 LLM 调用失败的情况"""
        # 模拟 LLM 客户端调用失败
        self.mock_llm_client.call.return_value = LLMOutput(
            success=False,
            content="",
            error_msg="LLM 调用失败"
        )
        
        # 准备输入数据
        input_data = AlignmentInput(
            decision="完成项目架构设计文档",
            root_goal="开发一个基于 GWT 理论的 Agent 框架",
            current_milestone="完成架构设计"
        )
        
        # 调用 check_alignment 方法
        result = self.attention_controller.check_alignment(input_data)
        
        # 验证结果
        self.assertFalse(result["success"])
        self.assertEqual(result["alignment_score"], 0)
        self.assertFalse(result["is_aligned"])
        self.assertIsNotNone(result["correction_hint"])

if __name__ == "__main__":
    unittest.main()