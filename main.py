
"""
This script will execute the entire mathematical question generation and filtering pipeline in sequence.
"""
import logging
import config
from src import stages, utils
import asyncio
import argparse

def main():
    """Execute the entire pipeline."""
    # Set up the command-line argument parser
    parser = argparse.ArgumentParser(description="Mathematical Question Generation and Filtering Pipeline.")
    parser.add_argument(
        '--stage', 
        type=str, 
        choices=['all', 'generate', 'filter'], 
        default='all',
        help="Run a specific stage: 'generate' (gen+dedup), 'filter', or 'all'."
    )
    args = parser.parse_args()

    # 1. Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logging.info("="*50)
    logging.info("Starting Mathematical Question Generation Pipeline")
    logging.info("="*50)

    # 2. Preparation: Create data directory and example seed file
    utils.setup_data_directory_and_seed_file(config.DATA_DIR, config.SEED_FILE)

    # async def async_main():
    #     # Stage one: Generate
    #     await stages.run_generation_stage(
    #         seed_file=config.SEED_FILE,
    #         output_file=config.GENERATED_FILE
    #     )
    #     # Stage two: Deduplication (this is a synchronous function)
    #     stages.run_deduplication_stage(
    #         generated_file=config.GENERATED_FILE,
    #         output_file=config.DEDUPLICATED_FILE
    #     )
    #     # Stage three: Filter
    #     await stages.run_filtering_stage(
    #         deduplicated_file=config.DEDUPLICATED_FILE,
    #         output_file=config.QUALIFIED_FILE
    #     )
        
    async def async_main():
    # Selectively execute different stages based on command-line arguments
    
    # If the argument is 'all' or 'generate', execute the generation and deduplication stages
    if args.stage in ['all', 'generate']:
        await stages.run_generation_stage(config.SEED_FILE, config.GENERATED_FILE)
        stages.run_deduplication_stage(config.GENERATED_FILE, config.DEDUPLICATED_FILE)
    
    # 如If the argument is 'all' or 'filter', execute the filtering stage
    if args.stage in ['all', 'filter']:
        await stages.run_filtering_stage(config.DEDUPLICATED_FILE, config.QUALIFIED_FILE)
            
 
    # Run the main asynchronous function
    asyncio.run(async_main())

    logging.info("="*50)
    logging.info("Pipeline finished successfully!")
    logging.info(f"Final qualified questions are saved in: {config.QUALIFIED_FILE}")
    logging.info("="*50)

if __name__ == "__main__":
    main()
