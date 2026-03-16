"""GitHub 热门项目自动发布 - 主入口"""
import argparse
import logging
import sys

# 添加 src 目录到路径
sys.path.insert(0, 'src')

from src.config import get_config
from src.github_trending import search_github_trending
from src.github_writer import write_github_article
from src.wechat_publisher import publish_article

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_github_workflow():
    """执行 GitHub 热门项目工作流"""
    logger.info("=" * 50)
    logger.info("开始执行 GitHub 热门项目工作流")

    try:
        # 1. 获取 GitHub 热门项目
        logger.info("步骤 1: 获取 GitHub 热门项目...")
        project_list = search_github_trending()
        if not project_list:
            logger.warning("未获取到热门项目，跳过发布")
            return

        # 2. 生成文章
        logger.info("步骤 2: 生成文章...")
        article = write_github_article(project_list)

        # 3. 发布到公众号
        logger.info("步骤 3: 发布到公众号...")
        result = publish_article(article["title"], article["content"])

        logger.info(f"工作流执行完成: {result}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"工作流执行失败: {e}", exc_info=True)


def main():
    parser = argparse.ArgumentParser(description="GitHub 热门项目自动发布工具")
    parser.add_argument("--now", action="store_true", help="立即执行一次")

    args = parser.parse_args()

    if args.now:
        logger.info("手动执行模式")
        run_github_workflow()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
