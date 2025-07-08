
"""封装与各类大型语言模型API的交互逻辑"""

import logging
import time
from typing import List, Dict, Any

import openai
import google.generativeai as genai
import anthropic
from tenacity import retry, stop_after_attempt, wait_random_exponential

from config import API_CONFIG

# --- API 客户端初始化 ---
try:
    # OpenAI compatible clients
    client_openai = openai.OpenAI(api_key=API_CONFIG["openai"]["api_key"])
    client_deepseek = openai.OpenAI(**API_CONFIG["deepseek"])
    client_qwen = openai.OpenAI(**API_CONFIG["qwen"])
    
    # Google Gemini
    genai.configure(api_key=API_CONFIG["google"]["api_key"])
    
    # Anthropic Claude
    client_anthropic = anthropic.Anthropic(api_key=API_CONFIG["anthropic"]["api_key"])
    
    logging.info("All API clients initialized successfully.")
except Exception as e:
    logging.error(f"Error initializing API clients: {e}", exc_info=True)
    raise

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def call_llm(model_name: str, messages: List[Dict[str, str]], temperature: float = 0.5) -> str:
    """
    根据模型名称调用对应的API，并实现自动重试。

    Args:
        model_name: 要调用的模型名称。
        messages: 符合OpenAI格式的消息列表。
        temperature: 生成的温度参数。

    Returns:
        模型的文本响应。
    
    Raises:
        ValueError: 如果模型提供商未知。
        Exception: 如果API调用失败。
    """
    logging.info(f"Calling model: {model_name}...")
    start_time = time.time()
    
    try:
        # OpenAI Compatible (OpenAI, DeepSeek, Qwen)
        if any(key in model_name for key in ["gpt", "o3", "deepseek", "qwen"]):
            client = {
                "gpt": client_openai, "o3": client_openai,
                "deepseek": client_deepseek, "qwen": client_qwen
            }[next(key for key in ["gpt", "o3", "deepseek", "qwen"] if key in model_name)]
            
            response = client.chat.completions.create(
                model=model_name, messages=messages, temperature=temperature
            )
            response_text = response.choices[0].message.content

        # Google Gemini
        elif "gemini" in model_name:
            gemini_model = genai.GenerativeModel(model_name)
            system_prompt = messages[0].get('content') if messages and messages[0]['role'] == 'system' else None
            user_prompt = messages[-1]['content']
            response = gemini_model.generate_content(user_prompt, system_instruction=system_prompt)
            response_text = response.text

        # Anthropic Claude
        elif "claude" in model_name:
            system_prompt = messages[0].get('content', '') if messages and messages[0]['role'] == 'system' else ""
            user_messages = messages[1:] if system_prompt else messages
            response = client_anthropic.messages.create(
                model=model_name, max_tokens=4096, system=system_prompt, messages=user_messages, temperature=temperature
            )
            response_text = response.content[0].text

        else:
            raise ValueError(f"Unknown model provider for: {model_name}")
            
    except Exception as e:
        logging.error(f"API call to {model_name} failed. Error: {e}", exc_info=True)
        raise

    duration = time.time() - start_time
    logging.info(f"Response from {model_name} received in {duration:.2f}s.")
    return response_text if response_text else ""