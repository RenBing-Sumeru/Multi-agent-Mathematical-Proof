
"""Contains the core stages of the pipeline: data generation and quality filtering."""
import json
import logging
import random
from typing import List, Dict, Any
import asyncio
import re


import config
from src import prompts, llm_api, utils

async def run_seed_filtering_stage(seed_file: str, output_file: str) -> None:
    """
    Executes stage zero: Filter seed questions.
    """
    logging.info("=" * 20 + " STAGE 0: SEED FILTERING " + "=" * 20)

    seed_questions = utils.load_from_json(seed_file)
    if not seed_questions:
        logging.error("No seed questions found. Aborting seed filtering stage.")
        return

    async def evaluate_seed(seed):
        logging.info(f"--- Evaluating Seed ID: {seed['id']} ---")
        item_type = seed['type']
        content = seed['content']

        prompt = utils.format_eval_prompt(item_type, content)

        async def judge_one_run(model_name: str) -> int:
            messages = [{"role": "user", "content": prompt}]
            response_text = await asyncio.to_thread(llm_api.call_llm, model_name, messages)
            eval_result = utils.parse_eval_result(response_text)

            if eval_result == "Error":  # Fallback to Judge Model
                logging.warning(f"  ! No valid \\boxed{{}} found. Using Judge Model ({config.JUDGE_MODEL})...")

                if item_type == 'proposition-proof':
                    judge_prompt = prompts.MODEL_JUDGE_PROOF_PROMPT + response_text
                elif item_type == 'definition':
                    judge_prompt = prompts.MODEL_JUDGE_DEFINITION_PROMPT + response_text
                else:
                    raise ValueError(f"Unknown item type: {item_type}")

                judge_messages = [{"role": "user", "content": judge_prompt}]
                judge_response = await asyncio.to_thread(
                    llm_api.call_llm, config.JUDGE_MODEL, judge_messages
                )
                eval_result = utils.parse_eval_result(judge_response)
                logging.info(f"  + Judge Model decision: {eval_result}")
                if eval_result == "Error":
                    logging.error(f"  ! Judge Model also failed to evaluate. Discarding item.")

            return 1 if eval_result == 'F' else 0

        tasks = [
            judge_one_run(model)
            for model in config.FILTER_MODELS
            for _ in range(config.JUDGEMENT_RUNS_PER_MODEL)
        ]
        judgement_scores = await asyncio.gather(*tasks)
        total_score = sum(judgement_scores)

        logging.info(f"  -- Seed ID: {seed['id']} total score: {total_score}")
        if total_score >= config.SEED_QUALITY_THRESHOLD:
            logging.info(f"     -> QUALIFIED (Score: {total_score})")
            seed['quality_score'] = total_score
            return seed
        else:
            logging.info(f"     -> DISCARDED (Score: {total_score})")
            return None

    tasks = [evaluate_seed(seed) for seed in seed_questions]
    results = await asyncio.gather(*tasks)

    qualified_seeds = [result for result in results if result is not None]

    utils.save_to_json(qualified_seeds, output_file)
    logging.info(f"Filtering complete, kept {len(qualified_seeds)} high-quality seed questions in total.")

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
            question_packet["generated_incorrect"].append({"id": f"{seed['id']}_gen_{i}", "content": content, "ground_truth": "Wrong", "generating_model": config.GENERATOR_MODELS[i % len(config.GENERATOR_MODELS)]})
        
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
        original_content_str = json.dumps(packet['original_correct'], sort_keys=True)
        normalized_original = utils.normalize_text(original_content_str)

        seen_normalized_texts = {normalized_original}
        unique_generated_texts = []
        for item in packet['generated_incorrect']:
            item_content_str = json.dumps(item['content'], sort_keys=True)
            normalized_item = utils.normalize_text(item_content_str)

            if normalized_item not in seen_normalized_texts:
                seen_normalized_texts.add(normalized_item)
                unique_generated_texts.append(item)
            else:
                logging.warning(f"  - Discarding duplicate item from model {item['generating_model']}.")

        logging.info(f"  - Original count: {len(packet['generated_incorrect'])}, after deduplication: {len(unique_generated_texts)}.")
        packet['generated_incorrect'] = unique_generated_texts
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
                response_text = await asyncio.to_thread(llm_api.call_llm, model_name, messages)
                eval_result = utils.parse_eval_result(response_text)

                if eval_result == "Error": # Fallback to Judge Model
                    logging.warning(f"  ! No valid \\boxed{{}} found. Using Judge Model ({config.JUDGE_MODEL})...")

                    if item_type == 'proposition-proof':
                        judge_prompt = prompts.MODEL_JUDGE_PROOF_PROMPT + response_text
                    elif item_type == 'definition':
                        judge_prompt = prompts.MODEL_JUDGE_DEFINITION_PROMPT + response_text
                    else:
                        raise ValueError(f"Unknown item type: {item_type}")
                    judge_messages = [{"role": "user", "content": judge_prompt}]
                    judge_response = await asyncio.to_thread(llm_api.call_llm, config.JUDGE_MODEL, judge_messages, temperature=0.0)
                    eval_result = utils.parse_eval_result(judge_response)
                    logging.info(f"  + Judge Model decision: {eval_result}")
                    if eval_result == "Error":
                        logging.error(f"  ! Judge Model also failed to evaluate. Discarding item.")

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

        filter_results = await asyncio.gather(*(filter_one_item(item) for item in packet['generated_incorrect']))
        surviving_incorrect_texts = [res for res in filter_results if res is not None]

        if surviving_incorrect_texts:
            logging.info(f"  => Seed ID {packet['seed_id']} is KEPT with {len(surviving_incorrect_texts)} texts.")
            final_packet = {
                "seed_id": packet['seed_id'], "type": packet['type'],
                "original_correct_text": packet['original_correct'],
                "qualified_incorrect_texts": surviving_incorrect_texts
            }
            final_qualified_packets.append(final_packet)
        else:
            logging.info(f"  => Seed ID {packet['seed_id']} is DISCARDED as no texts passed filtering.")

    utils.save_to_json(final_qualified_packets, output_file)


async def run_combination_stage(qualified_file: str, output_file: str):
    """
    Stage five: Combine into multiple choice questions
    """
    logging.info("=" * 20 + " STAGE 5: COMBINE INTO MULTIPLE CHOICE QUESTIONS " + "=" * 20)

    data_packets = utils.load_from_json(qualified_file)
    if not data_packets:
        logging.warning("No qualified data found. Aborting combination stage.")
        return
    
    # Get the number of options from config (default value is 6).
    num_options = getattr(config, "NUM_OPTIONS_PER_QUESTION", 6)

    # Record the available items for each seed_id (original_correct + generated_incorrect)
    available_items = {}
    for packet in data_packets:
        seed_id = packet['seed_id']
        original = packet['original_correct_text']
        incorrects = packet['qualified_incorrect_texts']
        available_items[seed_id] = [original] + incorrects

    multiple_choice_questions = []

    while True:
        # Select 6 different seed ids from available_items
        remaining_seed_ids = list(available_items.keys())
        if len(remaining_seed_ids) < num_options:
            logging.info(f"Cannot generate new multiple choice questions: remaining seed_id count is less than {num_options}.")
            break

        selected_seed_ids = random.sample(remaining_seed_ids, num_options)

        # Construct the six options for one multiple choice question
        question_options = []
        for seed_id in selected_seed_ids:
            items = available_items[seed_id]
            selected_item = items.pop(random.randint(0, len(items) - 1))
            if seed_id.startswith("def"):
                selected_item["type"] = "definition"
            elif seed_id.startswith("proof"):
                selected_item["type"] = "proposition-proof"
            else:
                logging.error(f"Unknown seed_id format: {seed_id}. Expected 'def_' or 'proof_'.")
                raise ValueError(f"Unknown seed_id format: {seed_id}. Expected 'def_' or 'proof_'.")
            # Randomly select one item
            question_options.append(selected_item)

            # If the items for this seed_id are used up, delete it
            if not items:
                del available_items[seed_id]

        # Determine the correct answer indices (A, B, C, ...)
        correct_indices = [
            idx for idx, option in enumerate(question_options)
            if option.get('ground_truth') == "Correct"
        ]

        # Control the number of correct answers
        if getattr(config, "RANDOM_CORRECT_ANSWERS", False):
            num_correct = random.randint(0, num_options)
            correct_indices = random.sample(range(num_options), num_correct)
        else:
            num_correct = getattr(config, "NUM_CORRECT_ANSWERS", 1)
            if len(correct_indices) < num_correct:
                logging.warning(f"Number of correct answers is less than {num_correct}, skipping this question.")
                continue
            correct_indices = random.sample(correct_indices, num_correct)

        # Construct the multiple choice question
        multiple_choice_questions.append({
            "options": {chr(65 + i): option for i, option in enumerate(question_options)}, 
            "answer": [chr(65 + idx) for idx in sorted(correct_indices)] 
        })

    # Save the results
    utils.save_to_json(multiple_choice_questions, output_file)
    logging.info(f"Successfully generated {len(multiple_choice_questions)} multiple choice questions, saved to {output_file}")

async def run_test(input_file: str, output_file: str):
    """
    Test the model's performance on multiple choice questions and calculate the score.
    """
    logging.info("\n" + "=" * 20 + " TESTING MODELS ON MULTIPLE CHOICE QUESTIONS " + "=" * 20)

    # Load questions
    questions = utils.load_from_json(input_file)
    if not questions:
        logging.warning("No questions found. Aborting test stage.")
        return

    # Prepare output structure
    results = []

    # Iterate through each question
    for idx, question in enumerate(questions):
        logging.info(f"\n--- Testing Question {idx} ---")

        # Construct prompt
        options = question["options"]  # dict: {"A": ..., "B": ..., ...}
        correct_answers = set(question["answer"])  # list: ["A", "C"]

        # Construct prompt
        prompt = "Below is a multiple choice question. Each choice is a mathematical definition or proposition-proof pair.\n"
        prompt += "Your task is to determine which choices are mathematically correct.\n"
        prompt += f"Exactly {config.NUM_CORRECT_ANSWERS} choices are correct.\n\n"

        # Add each option
        for key in sorted(options.keys()):
            prompt += f"Choice {key}:\n\n{utils.generate_one_choice(options[key])}\n\n\n"

        prompt += "Output format: Put the labels of all correct choices inside a \\boxed{} at the end of your response.\n"
        prompt += "Example: \\boxed{A,B} if you think A and B are correct."

        # Asynchronously call all models
        messages = [{"role": "user", "content": prompt}]

        async def query_model(model_name: str):
            try:
                response = await asyncio.to_thread(llm_api.call_llm, model_name, messages)
                logging.info(f"  + Response from {model_name}: {response[:100]}...")  # Print the beginning part
                return response
            except Exception as e:
                logging.error(f"  ! Error querying {model_name}: {e}")
                return ""

        # Concurrently query all models
        responses = await asyncio.gather(*[query_model(model) for model in config.TEST_MODELS])

        # Parse responses and calculate scores
        model_responses = dict(zip(config.TEST_MODELS, responses))
        model_scores = {}

        for model_name, response in model_responses.items():
            matches = re.findall(r'\\boxed\{([^}]*)\}', response)
            if not matches:
                logging.warning(f"  ! No boxed answer found in response from {model_name}.")
                model_scores[model_name] = 0.0
                continue

            # Extract the choices from the model's answer
            answer_str = matches[-1].replace(" ", "")  # Remove spaces
            model_answers = set(answer_str.split(','))

            # Calculate the number of matches
            correct_count = sum(1 for ans in model_answers if ans in correct_answers)
            expected_count = getattr(config, "NUM_CORRECT_ANSWERS", 2)

            score = correct_count / expected_count
            model_scores[model_name] = score

            logging.info(f"  => {model_name} score: {score:.2f} (Correct: {correct_count}/{expected_count})")

        # Record results
        results.append({
            "question_index": idx,
            "model_responses": model_responses,
            "score": model_scores
        })

    # Calculate the average score for each model
    total_scores = {model: 0.0 for model in config.TEST_MODELS}
    for result in results:
        for model, score in result["score"].items():
            total_scores[model] += score

    avg_scores = {
        model: round(score / len(questions), 4)
        for model, score in total_scores.items()
    }

    logging.info("\n" + "-" * 40)
    logging.info("Final model average scores:")
    for model, score in avg_scores.items():
        logging.info(f"{model}: {score}")
    logging.info("-" * 40)

    # Save results
    utils.save_to_json(results, output_file)
    logging.info(f"✅ Test results have been saved to {output_file}")