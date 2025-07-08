
"""全局配置文件"""

import os

# --- API密钥和端点配置 ---
# 从环境变量读取密钥是最佳实践
API_CONFIG = {
    "openai": {"api_key": os.environ.get("OPENAI_API_KEY")},
    "deepseek": {
        "api_key": os.environ.get("DEEPSEEK_API_KEY"),
        "base_url": "https://api.deepseek.com/v1"
    },
    "qwen": {
        "api_key": os.environ.get("QWEN_API_KEY"),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    },
    "google": {"api_key": os.environ.get("GOOGLE_API_KEY")},
    "anthropic": {"api_key": os.environ.get("ANTHROPIC_API_KEY")}
}

# --- 模型名称配置 ---
# 阶段一：用于生成错误证明/定义的模型
GENERATOR_MODELS = [
    "deepseek-chat",
    "qwen2-72b-instruct",
    "claude-3-sonnet-20240229",
    "gemini-1.5-flash-latest",
    "gpt-4-turbo",
]

# 阶段二：用于评判和筛选的模型
FILTER_MODELS = [
    "gpt-4o",
    "deepseek-chat",
    "gemini-1.5-pro-latest",
    "qwen2-72b-instruct",
]

# --- 流程参数配置 ---
JUDGEMENT_RUNS_PER_MODEL = 3
QUALIFIED_SCORE_MIN = 8
QUALIFIED_SCORE_MAX = 10

# --- 文件与目录路径配置 ---
DATA_DIR = "data"
SEED_FILE = os.path.join(DATA_DIR, "seed_questions.json")
GENERATED_FILE = os.path.join(DATA_DIR, "generated_data.json")
QUALIFIED_FILE = os.path.join(DATA_DIR, "qualified_data.json")