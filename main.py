
"""
该脚本将按顺序执行整个数学问题生成与筛选流水线。
"""
import logging
import config
from src import stages, utils
import asyncio
import argparse

def main():
    """执行整个流水线。"""
    # 设置命令行参数解析器
    parser = argparse.ArgumentParser(description="Mathematical Question Generation and Filtering Pipeline.")
    parser.add_argument(
        '--stage', 
        type=str, 
        choices=['all', 'generate', 'filter'], 
        default='all',
        help="Run a specific stage: 'generate' (gen+dedup), 'filter', or 'all'."
    )
    args = parser.parse_args()

    # 1. 配置日志记录
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logging.info("="*50)
    logging.info("Starting Mathematical Question Generation Pipeline")
    logging.info("="*50)

    # 2. 准备工作：创建数据目录和示例种子文件
    utils.setup_data_directory_and_seed_file(config.DATA_DIR, config.SEED_FILE)

    # async def async_main():
    #     # 阶段一: 生成
    #     await stages.run_generation_stage(
    #         seed_file=config.SEED_FILE,
    #         output_file=config.GENERATED_FILE
    #     )
    #     # 阶段二: 去重 (这是一个同步函数)
    #     stages.run_deduplication_stage(
    #         generated_file=config.GENERATED_FILE,
    #         output_file=config.DEDUPLICATED_FILE
    #     )
    #     # 阶段三: 筛选
    #     await stages.run_filtering_stage(
    #         deduplicated_file=config.DEDUPLICATED_FILE,
    #         output_file=config.QUALIFIED_FILE
    #     )
        
    async def async_main():
    # 根据命令行参数，选择性地执行不同阶段
    
    # 如果参数是 'all' 或 'generate'，则执行生成和去重阶段
    if args.stage in ['all', 'generate']:
        await stages.run_generation_stage(config.SEED_FILE, config.GENERATED_FILE)
        stages.run_deduplication_stage(config.GENERATED_FILE, config.DEDUPLICATED_FILE)
    
    # 如果参数是 'all' 或 'filter'，则执行筛选阶段
    if args.stage in ['all', 'filter']:
        await stages.run_filtering_stage(config.DEDUPLICATED_FILE, config.QUALIFIED_FILE)
            
 
    # 运行主异步函数
    asyncio.run(async_main())

    logging.info("="*50)
    logging.info("Pipeline finished successfully!")
    logging.info(f"Final qualified questions are saved in: {config.QUALIFIED_FILE}")
    logging.info("="*50)

if __name__ == "__main__":
    main()
