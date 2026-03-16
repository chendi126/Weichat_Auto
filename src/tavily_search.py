"""Tavily AI搜索模块 - 获取实时网络信息"""
import logging
import requests
from typing import List, Dict, Any
from src.config import get_config

logger = logging.getLogger(__name__)


def search_with_tavily(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """使用Tavily API搜索网络

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数

    Returns:
        搜索结果列表，每个结果包含 title, url, content, score
    """
    config = get_config()
    tavily_config = config.get("tavily", {})
    api_key = tavily_config.get("api_key", "")

    if not api_key or api_key == "你的tavily-api-key":
        logger.warning("Tavily API key 未配置")
        return []

    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
                "include_images": False
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            # 提取结果
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")[:500],  # 截取内容
                    "score": item.get("score", 0)
                })

            # 尝试获取AI生成的摘要
            answer = data.get("answer", "")
            if answer:
                logger.info(f"Tavily AI摘要: {answer[:200]}...")

            logger.info(f"Tavily搜索成功，返回 {len(results)} 条结果")
            return results
        else:
            logger.error(f"Tavily API错误: {response.status_code} - {response.text}")
            return []

    except Exception as e:
        logger.error(f"Tavily搜索失败: {e}")
        return []


def format_tavily_results(results: List[Dict[str, Any]], max_items: int = 3) -> str:
    """格式化Tavily搜索结果为文本

    Args:
        results: 搜索结果列表
        max_items: 最大显示条数

    Returns:
        格式化的文本
    """
    if not results:
        return "抱歉，未找到相关信息"

    lines = ["🔍 搜索结果：\n"]

    for i, item in enumerate(results[:max_items], 1):
        title = item.get("title", "无标题")
        url = item.get("url", "")
        content = item.get("content", "")[:200]

        lines.append(f"{i}. {title}")
        if content:
            lines.append(f"   {content}...")
        if url:
            lines.append(f"   🔗 {url}")
        lines.append("")

    return "\n".join(lines)
