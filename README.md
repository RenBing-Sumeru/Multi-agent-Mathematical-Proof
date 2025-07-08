# Multi-agent-Mathematical-Proof

# 数学判断题自动化生成与评测流水线

本项目是一个基于大型语言模型（LLM）的自动化流水线，旨在将数学领域的定义或证明题，转化为高质量的、用于模型评测的判断题。

## ✨ 功能特性

- **数据生成**: 利用多个不同的LLM（如GPT、Gemini、Claude等），将正确的数学定义/证明批量改写为包含细微错误的、具有迷惑性的版本。
- **质量筛选**: 通过一组“评判”LLM对生成的数据进行多轮交叉验证，自动筛选出难度适中、逻辑有效的题目。
- **高度可配置**: 所有的模型、参数、文件路径均可在 `config.py` 中轻松配置。
- **模块化设计**: 代码结构清晰，遵循软件工程最佳实践，易于维护和二次开发。

## 🏛️ 项目结构

```
math_question_pipeline/
├── README.md               # 项目说明书
├── requirements.txt        # 依赖库
├── config.py               # 全局配置文件
├── main.py                 # 主程序入口
└── src/
    ├── __init__.py
    ├── llm_api.py          # LLM API 交互模块
    ├── prompts.py          # Prompt模板模块
    ├── stages.py           # 核心流水线阶段模块
    └── utils.py            # 通用工具函数模块
```

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/RenBing-Sumeru/Multi-agent-Mathematical-Proof.git
cd math_question_pipeline
```

### 2. 创建并激活虚拟环境 (推荐)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置API密钥

本项目需要访问多个LLM的API。请将您的API密钥设置为环境变量：

```bash
# macOS / Linux
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIzaSy..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="..." # 根据需要设置

# Windows (CMD)
set OPENAI_API_KEY="sk-..."
set GOOGLE_API_KEY="AIzaSy..."
# ...
```

### 5. 运行流水线

```bash
python main.py
```

程序将自动创建`data`目录及示例输入文件，并开始执行。最终产出的高质量数据集将保存在 `data/qualified_data.json` 中。

## ⚙️ 配置

如需更换模型或调整参数（如评判次数、筛选分数阈值），请直接修改 `config.py` 文件。