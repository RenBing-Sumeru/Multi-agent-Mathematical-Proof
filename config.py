"""Global configuration file"""

import os

# --- API Key and Endpoint Configuration ---
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

# --- Model Name Configuration ---
# Stage 1: Models used for generating error explanations/definitions
GENERATOR_MODELS = [
    "deepseek-v3",   #"deepseek-chat"
    "qwen-turbo", # qwen2.5-72b-instruct 
    "claude-3-sonnet-20240229",
    "gemini-2.5-flash-preview-05-20",
    "gpt-4.1",  #"gpt-4-turbo"
]

# Stage 2: Models used for judging and filtering
FILTER_MODELS = [
    "o4-mini",  
    "deepseek-r1-0528",  
    "gemini-2.5-pro-preview-05-06",
    "qwen-max",  # qwen3-235b-a22b 
]

# Model for the "model judge" fallback plan
JUDGE_MODEL = "qwen-turbo" # qwen2.5-72b-instruct

# --- Pipeline Parameter Configuration ---
NUM_TO_GENERATE = 6  # Number of error versions to be produced by each generation model
NUM_TO_SAMPLE = 2    # Number to be randomly sampled from the generated error versions

JUDGEMENT_RUNS_PER_MODEL = 3  # Number of judgment runs for the same question by each filter model
QUALIFIED_SCORE_MIN = 4       # Minimum score for a qualified question (total of len(FILTER_MODELS) * JUDGEMENT_RUNS_PER_MODEL runs)
QUALIFIED_SCORE_MAX = 7      # Maximum score for a qualified question

# --- File and Directory Path Configuration ---
DATA_DIR = "data"
SEED_FILE = os.path.join(DATA_DIR, "seed_questions.json")
GENERATED_FILE = os.path.join(DATA_DIR, "1_generated_data.json")
DEDUPLICATED_FILE = os.path.join(DATA_DIR, "2_deduplicated_data.json")
QUALIFIED_FILE = os.path.join(DATA_DIR, "3_final_qualified_data.json")