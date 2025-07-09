
"""
该脚本将按顺序执行整个数学问题生成与筛选流水线。
"""
import logging
import config
from src import stages, utils
import asyncio

def main():
    """执行整个流水线。"""
    
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

    async def async_main():
        # 3. 执行问题生成
        await stages.run_generation_stage(seed_file=config.SEED_FILE, output_file=config.GENERATED_FILE)
        # 4. 执行问题筛选
        await stages.run_filtering_stage(generated_file=config.GENERATED_FILE, output_file=config.QUALIFIED_FILE)

    asyncio.run(async_main())

    logging.info("="*50)
    logging.info("Pipeline finished successfully!")
    logging.info(f"Final qualified questions are saved in: {config.QUALIFIED_FILE}")
    logging.info("="*50)

if __name__ == "__main__":
    main()
