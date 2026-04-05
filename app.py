"""GWT Agent Gradio Web 应用启动入口。

提供基于Gradio的可视化Web界面，用于与GWT Agent框架进行交互。

使用方法:
    python app.py

可选参数:
    --host: 服务器地址 (默认: 0.0.0.0)
    --port: 服务器端口 (默认: 7860)
    --share: 创建公开链接 (默认: False)

示例:
    python app.py --port 8080
    python app.py --share
"""

import argparse
from web.app import run_gradio_app


def main():
    """主函数，解析命令行参数并启动Gradio应用。"""
    parser = argparse.ArgumentParser(
        description="GWT Agent Gradio Web 应用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python app.py                    # 使用默认配置启动
  python app.py --port 8080        # 指定端口
  python app.py --share            # 创建公开链接
  python app.py --host 127.0.0.1   # 仅本地访问
        """
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="服务器地址 (默认: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="服务器端口 (默认: 7860)"
    )

    parser.add_argument(
        "--share",
        action="store_true",
        help="创建公开链接，使外部网络可以访问"
    )

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  GWT Agent Gradio 演示系统                    ║
╠══════════════════════════════════════════════════════════════╣
║  基于全局工作空间理论的长任务稳定执行 Agent 框架               ║
╠══════════════════════════════════════════════════════════════╣
║  服务器地址: {args.host:<20}                       ║
║  服务器端口: {args.port:<20}                       ║
║  公开链接: {'是' if args.share else '否':<20}                       ║
╚══════════════════════════════════════════════════════════════╝
    """)

    run_gradio_app(
        server_name=args.host,
        server_port=args.port,
        share=args.share
    )


if __name__ == "__main__":
    main()
