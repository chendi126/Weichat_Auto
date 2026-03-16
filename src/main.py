"""AI 科技新闻自动发布 - 主入口"""
import argparse
import logging
import sys
from src.config import get_config
from src.scheduler import start_scheduler, run_workflow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="AI 科技新闻自动发布工具")
    parser.add_argument("--now", action="store_true", help="立即执行一次")
    parser.add_argument("--daemon", action="store_true", help="以守护进程模式运行（定时执行）")

    args = parser.parse_args()

    if args.now:
        # 立即执行
        logger.info("手动执行模式")
        run_workflow()
    elif args.daemon:
        # 定时执行
        logger.info("守护进程模式")
        start_scheduler()
    else:
        # 默认显示帮助
        parser.print_help()


if __name__ == "__main__":
    main()
