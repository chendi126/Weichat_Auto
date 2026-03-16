from typing import List, Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from sqlalchemy import text

from graphs.state import FilterNewsInput, FilterNewsOutput
from storage.database import get_session


def filter_news_node(state: FilterNewsInput, config: RunnableConfig, runtime: Runtime[Context]) -> FilterNewsOutput:
    """
    title: 去重过滤新闻
    desc: 查询数据库中已发布的新闻，排除重复内容
    integrations: supabase
    """
    ctx = runtime.context
    
    search_results: List[Dict[str, Any]] = state.search_results
    
    # 查询数据库中已发布的新闻URL
    published_urls = set()
    try:
        with get_session() as session:
            result = session.execute(text("SELECT url FROM published_news"))
            rows = result.fetchall()
            published_urls = {row[0] for row in rows}
    except Exception as e:
        # 如果表不存在，假设还没有发布过新闻
        pass
    
    # 过滤掉已发布的新闻
    filtered_news: List[Dict[str, Any]] = []
    for news in search_results:
        url = news.get("url", "")
        if url and url not in published_urls:
            filtered_news.append(news)
    
    return FilterNewsOutput(filtered_news=filtered_news)
