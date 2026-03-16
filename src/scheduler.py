"""定时任务模块"""
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.config import get_config
from src.news_searcher import search_news
from src.article_writer import write_article, write_article_from_tavily
from src.wechat_publisher import publish_article
from src.tavily_search import search_with_tavily

logger = logging.getLogger(__name__)


def run_workflow():
    """执行完整工作流"""
    logger.info("=" * 50)
    logger.info("开始执行工作流")

    try:
        # 1. 使用 Tavily 搜索 AI/科技新闻
        logger.info("步骤 1: 使用 Tavily 搜索 AI 科技新闻...")
        tavily_results = search_with_tavily("AI 科技 今日新闻")

        if tavily_results:
            # 2. 用 Tavily 结果生成文章
            logger.info("步骤 2: 使用 Tavily 结果生成文章...")
            article = write_article_from_tavily(tavily_results, "AI 科技新闻")
        else:
            # 如果 Tavily 失败，回退到 NewsNow
            logger.warning("Tavily 搜索失败，回退到 NewsNow...")
            logger.info("步骤 1: 搜索新闻...")
            news_list = search_news()
            if not news_list:
                logger.warning("未搜索到新闻，跳过本次发布")
                return
            logger.info("步骤 2: 生成文章...")
            article = write_article(news_list)

        if not article:
            logger.warning("文章生成失败，跳过本次发布")
            return

        # 3. 发布到公众号
        logger.info("步骤 3: 发布到公众号...")
        result = publish_article(article["title"], article["html"])

        logger.info(f"工作流执行完成: {result}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"工作流执行失败: {e}", exc_info=True)


def start_scheduler():
    """启动定时任务"""
    config = get_config()
    scheduler_config = config.get("scheduler", {})

    if not scheduler_config.get("enabled", False):
        logger.info("定时任务未启用")
        return

    scheduler = BlockingScheduler()

    # 每天指定时间执行
    trigger = CronTrigger(
        hour=scheduler_config.get("hour", 8),
        minute=scheduler_config.get("minute", 0)
    )

    scheduler.add_job(run_workflow, trigger, name="daily_news_publish")

    logger.info(f"定时任务已启动，每天 {scheduler_config.get('hour')}:{scheduler_config.get('minute'):02d} 执行")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("定时任务已停止")
