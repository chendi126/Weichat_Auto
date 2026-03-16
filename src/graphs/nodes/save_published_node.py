from typing import List, Dict, Any
from datetime import datetime
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from sqlalchemy import text

from graphs.state import SavePublishedInput, SavePublishedOutput
from storage.database import get_session


def save_published_node(state: SavePublishedInput, config: RunnableConfig, runtime: Runtime[Context]) -> SavePublishedOutput:
    """
    title: 保存已发布新闻
    desc: 将发布的新闻URL和文章内容保存到数据库，用于去重
    integrations: supabase
    """
    ctx = runtime.context
    
    filtered_news: List[Dict[str, Any]] = state.filtered_news
    article_title = state.article_title
    article_content = state.article_content
    image_url = state.image_url
    publish_result = state.publish_result
    
    # 创建表（如果不存在）
    try:
        with get_session() as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS published_news (
                    id SERIAL PRIMARY KEY,
                    url TEXT NOT NULL,
                    title TEXT,
                    article_title TEXT,
                    article_content TEXT,
                    image_url TEXT,
                    publish_result JSONB,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            session.commit()
    except Exception as e:
        return SavePublishedOutput(save_result={"success": False, "error": str(e)})
    
    # 保存每条新闻的URL
    saved_count = 0
    skipped_count = 0
    error_count = 0
    try:
        with get_session() as session:
            for news in filtered_news:
                url = news.get("url", "")
                if not url:
                    skipped_count += 1
                    continue
                
                try:
                    session.execute(
                        text("""
                            INSERT INTO published_news (url, title, article_title, article_content, image_url, publish_result)
                            VALUES (:url, :title, :article_title, :article_content, :image_url, :publish_result)
                        """),
                        {
                            "url": url,
                            "title": news.get("title", ""),
                            "article_title": article_title,
                            "article_content": article_content,
                            "image_url": image_url,
                            "publish_result": publish_result
                        }
                    )
                    saved_count += 1
                except Exception as e:
                    # URL已存在，跳过
                    skipped_count += 1
            session.commit()
    except Exception as e:
        return SavePublishedOutput(save_result={"success": False, "error": str(e)})
    
    save_result = {
        "success": True,
        "saved_count": saved_count,
        "skipped_count": skipped_count,
        "total_news": len(filtered_news),
        "message": f"成功保存 {saved_count} 条新闻记录，跳过 {skipped_count} 条已存在的新闻"
    }
    
    return SavePublishedOutput(save_result=save_result)
