from typing import List, Dict, Any
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import SearchClient
from coze_coding_utils.runtime_ctx.context import new_context

from graphs.state import SearchNewsInput, SearchNewsOutput


def search_news_node(state: SearchNewsInput, config: RunnableConfig, runtime: Runtime[Context]) -> SearchNewsOutput:
    """
    title: 搜索AI和科技新闻
    desc: 搜索AI和科技行业的最新新闻，获取当天的热门内容
    integrations: web-search
    """
    ctx = runtime.context
    
    # 初始化搜索客户端
    search_ctx = new_context(method="search.web")
    client = SearchClient(ctx=search_ctx)
    
    # 搜索AI和科技新闻，时间范围为3天内
    # 在查询词中明确加上时间限制，确保获取最新内容
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3)
    date_str = start_date.strftime("%Y-%m-%d")
    
    query = f"AI 人工智能 科技 最新 news after:{date_str}"
    response = client.search(
        query=query,
        search_type="web",
        count=15,
        time_range="3d",
        need_summary=True
    )
    
    # 提取搜索结果
    search_results: List[Dict[str, Any]] = []
    if response.web_items:
        for item in response.web_items:
            news_item = {
                "title": item.title,
                "url": item.url,
                "snippet": item.snippet,
                "summary": item.summary if item.summary else "",
                "site_name": item.site_name,
                "publish_time": item.publish_time
            }
            search_results.append(news_item)
    
    return SearchNewsOutput(search_results=search_results)
