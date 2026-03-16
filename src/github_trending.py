"""GitHub 热门项目搜索模块"""
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
import requests
import re

logger = logging.getLogger(__name__)


def search_github_trending() -> List[Dict[str, Any]]:
    """从 GitHub 官方 API 获取热门项目（最可靠）"""
    current_date = datetime.now().strftime("%Y年%m月%d日")

    # 直接使用 GitHub 官方 API，最可靠
    news_list = search_github_official(current_date)

    if news_list:
        return news_list

    # 如果 API 失败，使用备用
    return get_fallback_github_news(current_date)


def search_github_official(current_date: str) -> List[Dict[str, Any]]:
    """从 GitHub 官方获取热门项目（按星标排序）"""
    news_list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        # 动态计算一周前的日期
        today = datetime.utcnow()
        one_week_ago = today - timedelta(days=7)
        one_week_ago_str = one_week_ago.strftime("%Y-%m-%d")

        logger.info(f"查询一周内创建的项目: {one_week_ago_str} 至今")

        # GitHub 官方 API - 获取一周内新创建的热门仓库
        url = "https://api.github.com/search/repositories"
        params = {
            "q": f"stars:>500 created:>{one_week_ago_str}",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }

        resp = requests.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()

        data = resp.json()
        items = data.get("items", [])

        logger.info(f"GitHub API 返回 {len(items)} 个项目")

        for item in items[:10]:
            full_name = item.get("full_name", "")
            description = item.get("description", "")
            stars = item.get("stargazers_count", 0)
            language = item.get("language", "")

            if not description:
                description = f"GitHub 热门开源项目，⭐ {stars} stars"

            news_list.append({
                "title": full_name,
                "summary": f"{description} (⭐ {stars})",
                "source": f"GitHub · {language}" if language else "GitHub",
                "time": current_date,
                "raw_data": item  # 保留原始数据供AI提取
            })

        logger.info(f"成功获取 {len(news_list)} 个 GitHub 热门项目")

    except Exception as e:
        logger.warning(f"GitHub 官方 API 失败: {e}")
        # 尝试备用数据源
        news_list = search_github_gitee(current_date)

    return news_list


def get_github_raw_data() -> str:
    """获取GitHub原始JSON数据（供DeepSeek分析）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        # 动态计算一周前的日期
        today = datetime.utcnow()
        one_week_ago = today - timedelta(days=7)
        one_week_ago_str = one_week_ago.strftime("%Y-%m-%d")

        url = "https://api.github.com/search/repositories"
        params = {
            "q": f"stars:>500 created:>{one_week_ago_str}",
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }

        resp = requests.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()

        data = resp.json()
        items = data.get("items", [])

        # 提取关键信息
        result = []
        for item in items[:10]:
            result.append({
                "name": item.get("full_name", ""),
                "description": item.get("description", ""),
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language", ""),
                "url": item.get("html_url", ""),
                "forks": item.get("forks_count", 0)
            })

        import json
        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.warning(f"获取GitHub原始数据失败: {e}")
        return ""


def search_github_gitee(current_date: str) -> List[Dict[str, Any]]:
    """从 Gitee 获取热门项目（国内备用）"""
    news_list = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        # Gitee 热门项目 API
        url = "https://gitee.com/api/v5/repositories"
        params = {
            "sort": "star",
            "direction": "desc",
            "page": 1,
            "per_page": 10
        }

        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()

        items = resp.json()

        for item in items:
            full_name = item.get("full_name", "")
            description = item.get("description", "") or "热门开源项目"
            stars = item.get("stargazers_count", 0)

            news_list.append({
                "title": full_name,
                "summary": f"{description[:100]} (⭐ {stars})",
                "source": "Gitee",
                "time": current_date
            })

    except Exception as e:
        logger.warning(f"Gitee API 失败: {e}")

    return news_list


def get_fallback_github_news(current_date: str) -> List[Dict[str, Any]]:
    """备用 GitHub 新闻"""
    return [
        {
            "title": "microsoft/vscode",
            "summary": "Visual Studio Code - 微软开源的代码编辑器",
            "source": "GitHub",
            "time": current_date
        },
        {
            "title": "facebook/react",
            "summary": "用于构建用户界面的 JavaScript 库",
            "source": "GitHub",
            "time": current_date
        },
        {
            "title": "vercel/next.js",
            "summary": "React 框架，用于生产环境的 SSR 应用",
            "source": "GitHub",
            "time": current_date
        },
        {
            "title": "twbs/bootstrap",
            "summary": "最流行的 HTML、CSS 和 JS 响应式框架",
            "source": "GitHub",
            "time": current_date
        },
        {
            "title": "microsoft/TypeScript",
            "summary": "TypeScript 是 JavaScript 的超集，添加了类型系统",
            "source": "GitHub",
            "time": current_date
        },
        {
            "title": "torvalds/linux",
            "summary": "Linux 内核源码",
            "source": "GitHub",
            "time": current_date
        },
        {
            "title": "tensorflow/tensorflow",
            "summary": "Google 开源的机器学习框架",
            "source": "GitHub",
            "time": current_date
        },
        {
            "title": "shadcn-ui/shadcn-ui",
            "summary": "Beautiful, accessible components for React",
            "source": "GitHub",
            "time": current_date
        },
        {
            "title": "oven-sh/bun",
            "summary": "快速 JavaScript 运行时",
            "source": "GitHub",
            "time": current_date
        },
        {
            "title": "oven-sh/packages",
            "summary": "Bun 的包管理器",
            "source": "GitHub",
            "time": current_date
        }
    ]
