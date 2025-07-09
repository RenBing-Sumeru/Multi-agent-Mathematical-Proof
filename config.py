
"""全局配置文件"""

import os

# --- API密钥和端点配置 ---
# 从环境变量读取密钥是最佳实践
API_CONFIG = {
    "openai": {
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "base_url": "https://jacob.api-store.store/v1/"
    },
    "deepseek": {
        "api_key": os.environ.get("DEEPSEEK_API_KEY"),
        "base_url": "https://jacob.api-store.store/v1/"
    },
    "qwen": {
        "api_key": os.environ.get("QWEN_API_KEY"),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/"
    },
    "google": {
        "api_key": os.environ.get("GOOGLE_API_KEY"),
        "base_url": "https://jacob.api-store.store/v1/"
    },
    "anthropic": {
        "api_key": os.environ.get("ANTHROPIC_API_KEY"),
        "base_url": "https://api.anthropic.com/v1"
    }
}

# --- 模型名称配置 ---
# 阶段一：用于生成错误证明/定义的模型
GENERATOR_MODELS = [
    "deepseek-v3",
    "gpt-4.1",
    "gemini-2.5-flash-preview-05-20",
]

# 阶段二：用于评判和筛选的模型
FILTER_MODELS = [
    "o4-mini",
    "deepseek-r1-0528",
    "gemini-2.5-pro-preview-05-06",
]

# --- 流程参数配置 ---
JUDGEMENT_RUNS_PER_MODEL = 3
# 总分：JUDGEMENT_RUNS_PER_MODEL * len(FILTER_MODELS)
QUALIFIED_SCORE_MIN = 4
QUALIFIED_SCORE_MAX = 7

# --- 文件与目录路径配置 ---
DATA_DIR = "data"
SEED_FILE = os.path.join(DATA_DIR, "seed_questions.json")
GENERATED_FILE = os.path.join(DATA_DIR, "generated_data.json")
QUALIFIED_FILE = os.path.join(DATA_DIR, "qualified_data.json")