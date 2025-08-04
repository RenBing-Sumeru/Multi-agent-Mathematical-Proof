
"""Encapsulates the interaction logic with various large language models"""

import logging
import time
from typing import List, Dict, Any

import openai
import google.generativeai as genai
import anthropic
from tenacity import retry, stop_after_attempt, wait_random_exponential

from config import API_CONFIG

_CLIENT_CACHE = {}

def _get_client(model_name: str):
    """Initializes clients on demand and caches them to avoid repeated initialization"""
    global _CLIENT_CACHE

    if model_name in _CLIENT_CACHE:
        return _CLIENT_CACHE[model_name]

    if "gpt" in model_name or "o3" in model_name or "o4" in model_name:
        client = openai.OpenAI(**API_CONFIG["openai"])
    elif "deepseek" in model_name:
        client = openai.OpenAI(**API_CONFIG["deepseek"])
    elif "qwen" in model_name:
        client = openai.OpenAI(**API_CONFIG["qwen"])
    elif "gemini" in model_name:
        client = openai.OpenAI(**API_CONFIG["google"])
    elif "claude" in model_name:
        client = anthropic.Anthropic(**API_CONFIG["anthropic"])
    else:
        raise ValueError(f"Unknown model provider for: {model_name}")

    _CLIENT_CACHE[model_name] = client
    return client

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def call_llm(model_name: str, messages: List[Dict[str, str]], temperature: float = 0.5) -> str:
    """
    Calls the corresponding API based on the model name and implements automatic retries.

    Args:
        model_name: The name of the model to call.
        messages: A list of messages in OpenAI format.
        temperature: The temperature parameter for generation.

    Returns:
        The text response from the model.
    
    Raises:
        ValueError: If the model provider is unknown.
        Exception: If the API call fails.
    """
    logging.info(f"Calling model: {model_name}...")
    start_time = time.time()
    
    try:
        # OpenAI Compatible (OpenAI, DeepSeek, Qwen)
        if any(key in model_name for key in ["gpt", "o3", "o4", "deepseek", "qwen", "gemini"]):
            client = _get_client(model_name)
            
            response = client.chat.completions.create(
                model=model_name, messages=messages, temperature=temperature
            )
            response_text = response.choices[0].message.content

        # Anthropic Claude
        elif "claude" in model_name:
            client = _get_client(model_name)
            system_prompt = messages[0].get('content', '') if messages and messages[0]['role'] == 'system' else ""
            user_messages = messages[1:] if system_prompt else messages
            response = client.messages.create(
                model=model_name, max_tokens=4096, system=system_prompt, messages=user_messages, temperature=temperature
            )
            response_text = response.content[0].text

        else:
            raise ValueError(f"Unknown model provider for: {model_name}")
    except KeyError as e:
        logging.error(f"Missing API configuration for model: {model_name}. Error: {e}", exc_info=True)
        raise ValueError(f"Missing required API config for model: {model_name}") from e      
    except Exception as e:
        logging.error(f"API call to {model_name} failed. Error: {e}", exc_info=True)
        raise

    duration = time.time() - start_time
    logging.info(f"Response from {model_name} received in {duration:.2f}s.")
    return response_text if response_text else ""