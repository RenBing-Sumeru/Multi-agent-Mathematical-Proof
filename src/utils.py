
"""Contains utility functions, such as file operations, content parsing, etc."""

import json
import logging
import os
import re
from typing import List, Dict, Any, Optional, Literal

def save_to_json(data: Any, filepath: str) -> None:
    """Saves data to a JSON file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Data successfully saved to {filepath}")
    except IOError as e:
        logging.error(f"Failed to save data to {filepath}: {e}")

def load_from_json(filepath: str) -> Any:
    """Loads data from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {filepath}: {e}")
        return None

def parse_generated_items(text: str) -> List[str]:
    """Parses all incorrect versions from the output of the generation model."""
    return re.findall(r'\[incorrect_(?:proof|definition)_\d-start\]\s*(.*?)\s*\[incorrect_(?:proof|definition)_\d-end\]', text, re.DOTALL)

def parse_eval_result(text: str) -> str:
    """Parses the content enclosed in boxed{} from the evaluation model's output. Returns the matched string or 'Error'."""
    match = re.search(r'\\boxed\{([^}]*(T|F)[^}]*)\}', text)
    return match.group(1) if match else "Error"

def normalize_text(text: str) -> str:
    """Removes all spaces and newlines for deduplication comparison."""
    return re.sub(r'\s+', '', text)

def setup_data_directory_and_seed_file(dir_path: str, seed_filepath: str) -> None:
    """Ensures the data directory exists, and if the seed file does not exist, creates a sample file."""
    os.makedirs(dir_path, exist_ok=True)
    if not os.path.exists(seed_filepath):
        logging.warning(f"Seed file not found. Creating a dummy seed file at '{seed_filepath}'...")
        dummy_data = [
            {
                "id": "def_001", "type": "definition",
                "content": {"text": "A function f...is called injective...if f(x) = f(y), then x = y."}
            },
            {
                "id": "proof_001", "type": "proposition-proof",
                "content": {
                    "proposition": "For any integer n, if n^2 is odd, then n is odd.",
                    "proof": "We prove the contrapositive..."
                }
            }
        ]
        save_to_json(dummy_data, seed_filepath)
