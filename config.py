"""全局配置文件"""

import os

# --- API密钥和端点配置 ---
API_CONFIG = {
    "openai": {
        "api_key": os.environ.get("OPENAI_API_KEY", "YOUR_OPENAI_KEY"),
    },
    "deepseek": {
        "api_key": os.environ.get("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_KEY"),
        "base_url": "https://api.deepseek.com/v1"
    },
    "qwen": {
        "api_key": os.environ.get("QWEN_API_KEY", "YOUR_QWEN_KEY"),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    },
    "google": {
        "api_key": os.environ.get("GOOGLE_API_KEY", "YOUR_GOOGLE_KEY"),
    },
    "anthropic": {
        "api_key": os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_KEY"),
    }
}

# --- 模型名称配置 ---
# 阶段一：用于生成错误证明/定义的模型
GENERATOR_MODELS = [
    "deepseek-v3",   #"deepseek-chat"
    "qwen-turbo", # qwen2.5-72b-instruct 
    "claude-3-sonnet-20240229",
    "gemini-2.5-flash-preview-05-20",
    "gpt-4.1",  #"gpt-4-turbo"
]

# 阶段二：用于评判和筛选的模型
FILTER_MODELS = [
    "o4-mini",  
    "deepseek-r1-0528",  
    "gemini-2.5-pro-preview-05-06",
    "qwen-max",  # qwen3-235b-a22b 
]

# 用于“模型裁判”备用方案的模型
JUDGE_MODEL = "qwen-turbo" # qwen2.5-72b-instruct

# --- 流程参数配置 ---
NUM_TO_GENERATE = 6  # 每个生成模型要产出的错误版本数量
NUM_TO_SAMPLE = 2    # 从生成的错误版本中随机抽取的数量

JUDGEMENT_RUNS_PER_MODEL = 3  # 每个评判模型对同一题目的评判次数
QUALIFIED_SCORE_MIN = 4       # 合格题目的最低分 (总计 len(FILTER_MODELS) * JUDGEMENT_RUNS_PER_MODEL 次)
QUALIFIED_SCORE_MAX = 7      # 合格题目的最高分

# --- 文件与目录路径配置 ---
DATA_DIR = "data"
SEED_FILE = os.path.join(DATA_DIR, "seed_questions.json")
GENERATED_FILE = os.path.join(DATA_DIR, "1_generated_data.json")
DEDUPLICATED_FILE = os.path.join(DATA_DIR, "2_deduplicated_data.json")
QUALIFIED_FILE = os.path.join(DATA_DIR, "3_final_qualified_data.json")