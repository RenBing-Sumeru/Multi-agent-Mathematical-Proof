
"""包含流水线的核心阶段：数据生成和质量筛选。"""

import logging
import random
from typing import List, Dict, Any

import config
from src import prompts, llm_api, utils

def run_generation_stage(seed_file: str, output_file: str) -> None:
    """
    执行阶段一：从种子文件生成包含错误证明/定义的数据。
    """
    logging.info("="*20 + " STAGE 1: DATA GENERATION " + "="*20)
    seed_questions = utils.load_from_json(seed_file)
    if not seed_questions:
        logging.error("No seed questions found. Aborting generation stage.")
        return

    all_generated_data = []
    for seed in seed_questions:
        logging.info(f"--- Processing Seed ID: {seed['id']} ---")
        question_packet = {
            "seed_id": seed['id'], "type": seed['type'],
            "original_correct": {"id": f"{seed['id']}_original", "content": seed['content'], "ground_truth": "Correct"},
            "generated_incorrect": []
        }

        generated_items_from_all_models = []
        for model_name in config.GENERATOR_MODELS:
            system_prompt = prompts.PROOF_GEN_PROMPT if seed['type'] == 'proposition-proof' else prompts.DEFINITION_GEN_PROMPT
            
            if seed['type'] == 'proposition-proof':
                user_content = f"Here's the proposition:\n\n{seed['content']['proposition']}\n\n\nHere's the proof:\n\n{seed['content']['proof']}"
            else:
                user_content = f"Here's the definition:\n\n{seed['content']['text']}"
            
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]
            response_text = llm_api.call_llm(model_name, messages)
            items = [item.strip() for item in utils.parse_generated_items(response_text)]
            logging.info(f"  - Model {model_name} generated {len(items)} items.")
            
            sampled_items = random.sample(items, 2) if len(items) >= 2 else items
            generated_items_from_all_models.extend(sampled_items)

        for i, item_content in enumerate(generated_items_from_all_models):
            content = {"proposition": seed['content']['proposition'], "proof": item_content} if seed['type'] == 'proposition-proof' else {"text": item_content}
            question_packet["generated_incorrect"].append({"id": f"{seed['id']}_gen_{i}", "content": content, "ground_truth": "Wrong"})
        
        all_generated_data.append(question_packet)

    utils.save_to_json(all_generated_data, output_file)

def run_filtering_stage(generated_file: str, output_file: str) -> None:
    """
    执行阶段二：筛选生成的数据，保留高质量题目。
    """
    logging.info("="*20 + " STAGE 2: QUALITY FILTERING " + "="*20)
    all_generated_data = utils.load_from_json(generated_file)
    if not all_generated_data:
        logging.error("No generated data found. Aborting filtering stage.")
        return

    qualified_questions = []
    for packet in all_generated_data:
        logging.info(f"--- Filtering Packet for Seed ID: {packet['seed_id']} ---")
        questions_to_filter = [packet['original_correct']] + packet['generated_incorrect']

        for question in questions_to_filter:
            logging.info(f"  -- Filtering question: {question['id']} (Truth: {question['ground_truth']})")
            judgements = []
            for model_name in config.FILTER_MODELS:
                for _ in range(config.JUDGEMENT_RUNS_PER_MODEL):
                    if packet['type'] == 'proposition-proof':
                        prompt = prompts.PROOF_EVAL_PROMPT + f"\n\n{question['content']['proposition']}\n\n\nHere is the proof:\n\n{question['content']['proof']}"
                    else:
                        prompt = prompts.DEFINITION_EVAL_PROMPT + f"\n\n{question['content']['text']}"
                    
                    messages = [{"role": "user", "content": prompt}]
                    response_text = llm_api.call_llm(model_name, messages)
                    eval_result = utils.parse_eval_result(response_text)
                    
                    model_is_correct = 1 if (question['ground_truth'] == 'Correct' and eval_result == 'T') or \
                                           (question['ground_truth'] == 'Wrong' and eval_result == 'F') else 0
                    judgements.append(model_is_correct)
            
            score = sum(judgements)
            logging.info(f"     - Judgement scores (1=correct): {judgements} | Total Score: {score}")

            if config.QUALIFIED_SCORE_MIN <= score <= config.QUALIFIED_SCORE_MAX:
                logging.info(f"     -> QUALIFIED!")
                qualified_questions.append({**question, "score": score})
            else:
                logging.info(f"     -> DISCARDED.")

    utils.save_to_json(qualified_questions, output_file)