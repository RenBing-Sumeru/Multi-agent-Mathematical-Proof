
"""Contains the core stages of the pipeline: data generation and quality filtering."""

import logging
import random
from typing import List, Dict, Any
import asyncio

import config
from src import prompts, llm_api, utils

async def run_generation_stage(seed_file: str, output_file: str) -> None:
    """
    Executes stage one: Generate data containing incorrect proofs/definitions from the seed file.
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
        
        async def get_items(model_name):
            system_prompt = prompts.PROOF_GEN_PROMPT if seed['type'] == 'proposition-proof' else prompts.DEFINITION_GEN_PROMPT
            if seed['type'] == 'proposition-proof':
                user_content = f"Here's the proposition:\n\n{seed['content']['proposition']}\n\n\nHere's the proof:\n\n{seed['content']['proof']}"
            else:
                user_content = f"Here's the definition:\n\n{seed['content']['text']}"
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_content}]
            response_text = await asyncio.to_thread(llm_api.call_llm, model_name, messages)
            items = [item.strip() for item in utils.parse_generated_items(response_text)]
            print(f"  - Model {model_name} generated {len(items)} items.")
            sampled_items = random.sample(items, 2) if len(items) >= 2 else items
            return sampled_items

        tasks = []
        
        async with asyncio.TaskGroup() as tg:
            for model_name in config.GENERATOR_MODELS:
                tasks.append(tg.create_task(get_items(model_name)))
        for task in tasks:
            generated_items_from_all_models.extend(await task)

        for i, item_content in enumerate(generated_items_from_all_models):
            content = {"proposition": seed['content']['proposition'], "proof": item_content} if seed['type'] == 'proposition-proof' else {"text": item_content}
            question_packet["generated_incorrect"].append({"id": f"{seed['id']}_gen_{i}", "content": content, "ground_truth": "Wrong"})
        
        all_generated_data.append(question_packet)

    utils.save_to_json(all_generated_data, output_file)

def run_deduplication_stage(generated_file: str, output_file: str):
    """Stage two: Data deduplication."""
    logging.info("\n" + "="*20 + " STAGE 2: DEDUPLICATION " + "="*20)
    all_generated_data = utils.load_from_json(generated_file)
    if not all_generated_data:
        return

    deduplicated_data = []
    for packet in all_generated_data:
        logging.info(f"--- Deduplicating for Seed ID: {packet['seed_id']} ---")
        original_content_str = json.dumps(packet['original_text'], sort_keys=True)
        normalized_original = utils.normalize_text(original_content_str)

        seen_normalized_texts = {normalized_original}
        unique_generated_texts = []
        for item in packet['generated_texts']:
            item_content_str = json.dumps(item['content'], sort_keys=True)
            normalized_item = utils.normalize_text(item_content_str)

            if normalized_item not in seen_normalized_texts:
                seen_normalized_texts.add(normalized_item)
                unique_generated_texts.append(item)
            else:
                logging.warning(f"  - Discarding duplicate item from model {item['generating_model']}.")

        logging.info(f"  - Original count: {len(packet['generated_texts'])}, after deduplication: {len(unique_generated_texts)}.")
        packet['generated_texts'] = unique_generated_texts
        deduplicated_data.append(packet)

    utils.save_to_json(deduplicated_data, output_file)

async def run_filtering_stage(deduplicated_file: str, output_file: str):
    """Stage three: Quality filtering (using new logic)."""
    logging.info("\n" + "="*20 + " STAGE 3: QUALITY FILTERING " + "="*20)
    all_deduplicated_data = utils.load_from_json(deduplicated_file)
    if not all_deduplicated_data:
        return

    final_qualified_packets = []
    for packet in all_deduplicated_data:
        logging.info(f"\n--- Filtering Packet for Seed ID: {packet['seed_id']} ---")
        surviving_incorrect_texts = []

        async def filter_one_item(item_to_filter):
            content = item_to_filter['content']
            item_type = packet['type']
            prompt = utils.format_eval_prompt(item_type, content)

            async def judge_one_run(model_name: str) -> int:
                messages = [{"role": "user", "content": prompt}]
                response_text = await llm_api.call_llm(model_name, messages)
                eval_result = utils.extract_boxed_answer(response_text)

                if eval_result is None: # Fallback to Judge Model
                    logging.warning(f"  ! No valid \\boxed{{}} found. Using Judge Model ({config.JUDGE_MODEL})...")
                    judge_prompt = prompts.MODEL_JUDGE_PROMPT_TEMPLATE.format(
                        item_type="proof" if item_type == "proposition-proof" else "definition",
                        model_response=response_text
                    )
                    judge_messages = [{"role": "user", "content": judge_prompt}]
                    judge_response = await llm_api.call_llm(config.JUDGE_MODEL, judge_messages, temperature=0.0)
                    eval_result = utils.extract_boxed_answer(judge_response)
                    logging.info(f"  + Judge Model decision: {eval_result}")

                return 1 if eval_result == 'F' else 0

            tasks = [judge_one_run(model) for model in config.FILTER_MODELS for _ in range(config.JUDGEMENT_RUNS_PER_MODEL)]
            judgement_scores = await asyncio.gather(*tasks)
            total_score = sum(judgement_scores)

            logging.info(f"  -- Filtering incorrect text (from {item_to_filter['generating_model']})... Score: {total_score}")
            if config.QUALIFIED_SCORE_MIN <= total_score <= config.QUALIFIED_SCORE_MAX:
                logging.info(f"     -> QUALIFIED!")
                item_to_filter['filter_score'] = total_score
                return item_to_filter
            else:
                logging.info(f"     -> DISCARDED.")
                return None

        filter_results = await asyncio.gather(*(filter_one_item(item) for item in packet['generated_texts']))
        surviving_incorrect_texts = [res for res in filter_results if res is not None]

        if surviving_incorrect_texts:
            logging.info(f"  => Seed ID {packet['seed_id']} is KEPT with {len(surviving_incorrect_texts)} texts.")
            final_packet = {
                "seed_id": packet['seed_id'], "type": packet['type'],
                "original_correct_text": packet['original_text'],
                "qualified_incorrect_texts": surviving_incorrect_texts
            }
            final_qualified_packets.append(final_packet)
        else:
            logging.info(f"  => Seed ID {packet['seed_id']} is DISCARDED as no texts passed filtering.")

    utils.save_to_json(final_qualified_packets, output_file)
