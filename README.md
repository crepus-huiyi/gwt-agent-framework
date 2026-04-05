# 基于全局工作空间理论的长任务稳定执行 Agent 内核框架

## 项目简介

本项目是一个基于巴尔斯全局工作空间理论（GWT）的长任务稳定执行 Agent 内核框架，通过分层架构设计解决传统 Agent 存在的上下文爆炸、任务跑偏和历史遗忘问题。

## 架构设计

### 整体架构

本框架采用分层架构设计，严格基于巴尔斯全局工作空间理论（GWT）工程化落地：

1. **基础设施层**：提供大模型 API 调用、统一日志、本地存储等基础能力
2. **持久化存储层**：管理自我认知、上下文连续体、目标锚定的持久化读写
3. **潜意识处理层**：对全量上下文进行并行过滤、核心信息提取、优先级排序
4. **意识层（全局工作空间）**：负责全局决策生成、目标对齐校验、全系统广播
5. **执行层**：接收执行指令、完成具体动作、反馈执行结果

### 核心数据流转

用户输入任务 → 持久化层加载根目标与自我认知 → 潜意识层并行过滤全量上下文 → 意识层基于核心信息生成决策 → 目标对齐校验 → 意识层广播执行指令 → 执行层执行并反馈结果 → 潜意识层接收结果并更新上下文 → 循环直至目标达成。

## 快速开始

### 环境要求

- Python 3.10-3.12
- 依赖包：见 requirements.txt

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

复制 `.env.example` 文件为 `.env`，并填写相应的配置：

```env
# 大模型 API 配置（支持 OpenAI 兼容的国内开源模型）
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o-mini  # 推荐用低成本模型验证

# 日志配置
LOG_LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR

# 存储配置
STORAGE_PATH=data/
```

### 运行项目

```bash
python main.py
```

然后按照提示输入任务目标和当前里程碑，系统会自动执行任务。

## 项目结构

```
gwt_agent_framework/
├── core/                          # 核心架构模块（对应5层架构）
│   ├── __init__.py
│   ├── infrastructure.py         # 基础设施层：LLM客户端、存储封装
│   ├── persistence.py            # 持久化存储层：自我认知、上下文连续体、目标锚定
│   ├── subconscious.py           # 潜意识处理层：并行过滤、信息提取、优先级打分
│   ├── global_workspace.py       # 意识层：全局决策生成
│   ├── attention_control.py      # 全局注意力管控机制：目标对齐校验
│   └── executors.py              # 执行层：文本处理、代码执行
├── state/                         # LangGraph状态机相关
│   ├── __init__.py
│   ├── agent_state.py            # 核心状态定义（TypedDict）
│   └── graph.py                  # 状态机构建与编译
├── utils/                         # 工具类
│   ├── __init__.py
│   ├── logger.py                 # 统一日志管理
│   └── storage.py                # 本地文件存储封装
├── data/                          # 本地持久化数据目录（gitignore）
│   ├── self_cognition.json
│   └── context_continuum.json
├── tests/                         # 单元测试
│   ├── __init__.py
│   └── test_attention_control.py
├── .env.example                   # 配置文件模板
├── .gitignore
├── requirements.txt               # 依赖清单
├── main.py                        # 项目入口：命令行交互
└── README.md                      # 项目说明
```

## 核心功能

1. **大模型 API 客户端**：支持 OpenAI 兼容的模型调用，包含重试逻辑
2. **自我认知管理**：从本地文件加载和保存自我认知数据，文件不存在时使用默认模板
3. **上下文连续体管理**：支持追加写入和读取，保持历史上下文的连续性
4. **潜意识并行过滤**：对全量上下文进行冗余剔除、核心信息提取、优先级排序
5. **目标对齐校验**：确保决策与根目标对齐，轻度跑偏返回修正提示，严重跑偏触发回溯
6. **基础执行器**：支持文本处理和代码执行，代码执行器能够拦截高危命令
7. **基于 LangGraph 的状态机**：实现全流程闭环，支持状态流转和异常处理

## 技术栈

- Python 3.10-3.12
- LangGraph 0.2.45
- LangChain 0.3.14
- python-dotenv 1.0.1
- logging（Python 内置）
- json（Python 内置）

## 开发规范

1. **代码注释规范**：所有核心类、函数必须使用 Google 风格注释
2. **日志规范**：统一使用 `utils.logger.get_logger(__name__)` 获取 logger
3. **异常处理规范**：所有可能异常的环节必须有 try-except 处理
4. **Git 提交规范**：提交信息格式：`<type>: <subject>`

## 注意事项

1. 本项目仅用于开发和测试目的，不用于生产环境
2. 代码执行器仅提供基础的安全检查，不支持执行高危命令
3. 运行前需要配置有效的 OpenAI 兼容 API 密钥

## 未来规划

1. 支持更多大模型 API
2. 增强代码执行器的安全性
3. 实现外部工具集成
4. 提供 Web 界面

## 许可证

本项目采用 MIT 许可证。