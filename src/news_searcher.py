"""新闻搜索模块 - 使用多种可靠新闻源"""
import logging
from typing import List, Dict, Any
from datetime import datetime
import requests
import re
import json
import random
import time

logger = logging.getLogger(__name__)

# NewsNow API 配置
NEWSNOW_API_URL = "https://newsnow.busiyi.world/api/s"
NEWS_SOURCES = [
    ("toutiao", "今日头条"),
    ("baidu", "百度热搜"),
    ("weibo", "微博"),
    ("zhihu", "知乎"),
    ("douyin", "抖音"),
    ("bilibili-hot-search", "B站热搜"),
]


def search_from_newsnow(keyword: str = "AI") -> List[Dict[str, Any]]:
    """从 NewsNow 聚合 API 获取热门新闻（推荐方式）"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    news_list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    # 使用用户搜索的关键词 + 默认科技关键词
    keywords = [keyword] if keyword else []
    tech_keywords = ["AI", "人工智能", "大模型", "ChatGPT", "OpenAI", "科技", "互联网", "芯片", "算法", "智能", "数码", "手机", "电脑", "英伟达", "NVIDIA", "AMD", "Intel", "微软", "Google", "Meta"]
    # 去重
    all_keywords = list(set(keywords + tech_keywords))

    try:
        # 遍历多个新闻源
        for source_id, source_name in NEWS_SOURCES:
            try:
                url = f"{NEWSNOW_API_URL}?id={source_id}&latest"
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()

                data = resp.json()
                items = data.get("items", [])

                for item in items[:10]:
                    title = item.get("title", "")
                    if not title:
                        continue

                    # 过滤科技相关
                    if not any(kw in title for kw in tech_keywords):
                        continue

                    # 过滤旧新闻
                    if any(kw in title for kw in ["2024", "2023", "2022"]):
                        continue

                    # 去重
                    if title in [n["title"] for n in news_list]:
                        continue

                    news_list.append({
                        "title": title,
                        "summary": item.get("description", "暂无摘要")[:150] if item.get("description") else "暂无摘要",
                        "source": source_name,
                        "time": current_date
                    })

                    if len(news_list) >= 15:
                        break

                # 添加间隔时间
                time.sleep(0.5)

                if len(news_list) >= 15:
                    break

            except Exception as e:
                logger.warning(f"NewsNow {source_name} 获取失败: {e}")
                continue

    except Exception as e:
        logger.warning(f"NewsNow API 整体失败: {e}")

    logger.info(f"从 NewsNow 获取到 {len(news_list)} 条科技新闻")
    return news_list


def search_fromToutiao() -> List[Dict[str, Any]]:
    """从今日头条获取AI科技新闻"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    news_list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    try:
        # 今日头条搜索API
        url = "https://www.toutiao.com/api/pc/feed/"
        params = {
            "category": "news_tech",
            "max_behot_time": 0,
            "utm_source": "toutiao",
        }

        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()

        data = resp.json()
        if data.get("data"):
            for item in data["data"][:15]:
                title = item.get("title", "")
                if not title:
                    continue

                # 过滤AI科技相关
                keywords = ["AI", "人工智能", "大模型", "ChatGPT", "OpenAI", "科技", "互联网", "芯片", "算法"]
                if not any(kw in title for kw in keywords):
                    continue

                # 过滤旧新闻
                if any(kw in title for kw in ["2024", "2023", "2022"]):
                    continue

                news_list.append({
                    "title": title,
                    "summary": item.get("abstract", "暂无摘要")[:150],
                    "source": item.get("source", "今日头条"),
                    "time": current_date
                })

                if len(news_list) >= 10:
                    break

    except Exception as e:
        logger.warning(f"今日头条搜索失败: {e}")

    return news_list


def search_fromSohu() -> List[Dict[str, Any]]:
    """从搜狐网获取科技新闻"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    news_list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        url = "https://v2.sohu.com/public-api/feed"
        params = {
            "scene": "CATEGORY",
            "sceneId": "1460",  # 科技
            "page": 1,
            "size": 20,
        }

        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()

        data = resp.json()
        if data.get("data"):
            for item in data["data"]:
                title = item.get("title", "")
                if not title:
                    continue

                # 过滤旧新闻
                if any(kw in title for kw in ["2024年", "2023年", "2022年"]):
                    continue

                news_list.append({
                    "title": title,
                    "summary": item.get("summary", "暂无摘要")[:150] if item.get("summary") else "暂无摘要",
                    "source": "搜狐科技",
                    "time": current_date
                })

                if len(news_list) >= 10:
                    break

    except Exception as e:
        logger.warning(f"搜狐搜索失败: {e}")

    return news_list


def search_fromWangyi() -> List[Dict[str, Any]]:
    """从网易科技获取新闻"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    news_list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        url = "https://news.163.com/special/cm_yaowen20200213/"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        # 解析网易新闻
        pattern = r'"docurl":"([^"]+)","title":"([^"]+)","source":"([^"]+)".*?"ptime":"([^"]+)"'
        matches = re.findall(pattern, resp.text)

        for docurl, title, source, ptime in matches[:20]:
            title = title.replace("\\", "")
            if not title:
                continue

            # 过滤科技相关
            keywords = ["AI", "人工智能", "科技", "互联网", "大模型", "ChatGPT", "OpenAI", "芯片"]
            if not any(kw in title for kw in keywords):
                continue

            # 过滤旧新闻
            if any(kw in title for kw in ["2024", "2023", "2022"]):
                continue

            news_list.append({
                "title": title,
                "summary": "网易科技新闻",
                "source": "网易科技",
                "time": current_date
            })

            if len(news_list) >= 10:
                break

    except Exception as e:
        logger.warning(f"网易搜索失败: {e}")

    return news_list


def search_fromQQ() -> List[Dict[str, Any]]:
    """从腾讯网获取科技新闻"""
    current_date = datetime.now().strftime("%Y年%m月%d日")
    news_list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://new.qq.com/",
    }

    try:
        # 腾讯科技频道
        url = "https://r.inews.qq.com/gw/event/hot_ranking?chlid=108756"
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        data = resp.json()
        items = data.get("idlist", [])

        if items and len(items) > 0:
            news_data = items[0].get("news", [])
            for item in news_data[:20]:
                title = item.get("title", "")
                if not title:
                    continue

                # 过滤科技相关
                keywords = ["AI", "人工智能", "科技", "互联网", "大模型", "ChatGPT", "OpenAI", "芯片", "数码", "手机", "电脑", "智能"]
                if not any(kw in title for kw in keywords):
                    continue

                # 过滤旧新闻
                if any(kw in title for kw in ["2024年", "2023年", "2022年"]):
                    continue

                news_list.append({
                    "title": title,
                    "summary": item.get("summary", item.get("desc", "暂无摘要"))[:150],
                    "source": item.get("source", "腾讯科技"),
                    "time": current_date
                })

                if len(news_list) >= 10:
                    break

    except Exception as e:
        logger.warning(f"腾讯网搜索失败: {e}")

    return news_list


def search_news(keyword: str = "AI") -> List[Dict[str, Any]]:
    """综合多个新闻源获取最新AI科技新闻"""
    current_date = datetime.now().strftime("%Y年%m月%d日")

    logger.info(f"开始搜索新闻，关键字: {keyword}...")

    all_news = []
    seen_titles = set()

    # 优先尝试 NewsNow 聚合 API（支持关键词搜索）
    logger.info("尝试从 NewsNow 聚合API获取新闻...")
    newsnow_news = search_from_newsnow(keyword)
    if newsnow_news:
        logger.info(f"从 NewsNow 获取到 {len(newsnow_news)} 条新闻")
        all_news.extend(newsnow_news)
    else:
        # NewsNow 失败，回退到原来的方式
        logger.info("NewsNow 获取失败，回退到传统新闻源...")

        # 尝试多个新闻源
        sources = [
            ("腾讯网", search_fromQQ),
            ("今日头条", search_fromToutiao),
            ("搜狐", search_fromSohu),
            ("网易", search_fromWangyi),
        ]

        for source_name, search_func in sources:
            logger.info(f"尝试从 {source_name} 获取新闻...")
            news_list = search_func()

            for news in news_list:
                if news["title"] not in seen_titles:
                    seen_titles.add(news["title"])
                    all_news.append(news)

            logger.info(f"从 {source_name} 获取到 {len(news_list)} 条新闻")

            if len(all_news) >= 10:
                break

        # 如果都没成功，尝试百度网页搜索（更简单的方法）
        if len(all_news) < 5:
            logger.info("新闻源结果不足，尝试百度搜索...")
            baidu_news = search_fromBaidu(current_date)
            for news in baidu_news:
                if news["title"] not in seen_titles:
                    seen_titles.add(news["title"])
                    all_news.append(news)

    logger.info(f"共获取到 {len(all_news)} 条新闻")
    return all_news[:10]


def search_fromBaidu(current_date: str) -> List[Dict[str, Any]]:
    """从百度获取科技新闻（简单方法）"""
    news_list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    queries = [
        "AI 科技 今日新闻",
        "人工智能 最新 2026",
    ]

    for query in queries:
        try:
            url = "https://www.baidu.com/s"
            params = {"wd": query, "rn": 10}

            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()

            # 简单提取标题
            pattern = r'<h3 class="c-title.*?"><a[^>]*>([^<]+)</a></h3>'
            matches = re.findall(pattern, resp.text)

            for title in matches:
                title = re.sub(r'<[^>]+>', '', title)
                title = title.replace('<em>', '').replace('</em>', '').strip()

                if not title:
                    continue

                # 过滤旧新闻
                if any(kw in title for kw in ["2024", "2023", "2022"]):
                    continue

                news_list.append({
                    "title": title,
                    "summary": "百度搜索结果",
                    "source": "百度",
                    "time": current_date
                })

                if len(news_list) >= 10:
                    break

        except Exception as e:
            logger.warning(f"百度搜索失败: {e}")
            continue

        if len(news_list) >= 10:
            break

    return news_list


def get_fallback_news() -> List[Dict[str, Any]]:
    """备用新闻（当所有搜索失败时）"""
    logger.error("所有新闻源均失败，请检查网络连接")
    current_date = datetime.now().strftime("%Y年%m月%d日")

    # 返回空列表，让工作流跳过
    return []
