"""Web模块 - Gradio前端演示页面。

提供基于Gradio的可视化Web界面，用于与GWT Agent框架进行交互。
"""

from .app import create_gradio_app, run_gradio_app

__all__ = ["create_gradio_app", "run_gradio_app"]
