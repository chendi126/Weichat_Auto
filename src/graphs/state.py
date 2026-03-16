from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field


class GlobalState(BaseModel):
    """全局状态定义"""
    # 原始搜索结果
    search_results: List[Dict[str, Any]] = Field(default=[], description="搜索到的原始新闻列表")
    # 过滤后的新闻（去重）
    filtered_news: List[Dict[str, Any]] = Field(default=[], description="去重后的新闻列表")
    # 生成的文章
    article_title: str = Field(default="", description="文章标题")
    article_content: str = Field(default="", description="文章内容")
    # 生成的配图
    image_url: str = Field(default="", description="生成的配图URL")
    # 发布结果
    publish_result: Dict[str, Any] = Field(default={}, description="发布结果")
    # 保存结果
    save_result: Dict[str, Any] = Field(default={}, description="保存到数据库的结果")


class GraphInput(BaseModel):
    """工作流的输入"""
    # 无需输入，自动获取当天新闻
    pass


class GraphOutput(BaseModel):
    """工作流的输出"""
    article_title: str = Field(..., description="生成的文章标题")
    article_content: str = Field(..., description="生成的文章内容")
    image_url: str = Field(..., description="配图URL")
    publish_result: Dict[str, Any] = Field(default={}, description="发布结果")
    save_result: Dict[str, Any] = Field(default={}, description="保存结果")


# ==================== 节点输入输出定义 ====================

class SearchNewsInput(BaseModel):
    """新闻搜索节点的输入"""
    pass


class SearchNewsOutput(BaseModel):
    """新闻搜索节点的输出"""
    search_results: List[Dict[str, Any]] = Field(..., description="搜索到的新闻列表，每条包含title、url、snippet、summary等")


class FilterNewsInput(BaseModel):
    """去重过滤节点的输入"""
    search_results: List[Dict[str, Any]] = Field(..., description="搜索到的新闻列表")


class FilterNewsOutput(BaseModel):
    """去重过滤节点的输出"""
    filtered_news: List[Dict[str, Any]] = Field(..., description="去重后的新闻列表")


class WriteArticleInput(BaseModel):
    """文章编写节点的输入"""
    filtered_news: List[Dict[str, Any]] = Field(..., description="去重后的新闻列表")


class WriteArticleOutput(BaseModel):
    """文章编写节点的输出"""
    article_title: str = Field(..., description="生成的文章标题")
    article_content: str = Field(..., description="生成的文章内容（HTML格式）")


class GenerateImageInput(BaseModel):
    """配图生成节点的输入"""
    article_title: str = Field(..., description="文章标题")
    article_content: str = Field(..., description="文章内容")


class GenerateImageOutput(BaseModel):
    """配图生成节点的输出"""
    image_url: str = Field(..., description="生成的配图URL")


class PublishToWechatInput(BaseModel):
    """微信公众号发布节点的输入"""
    article_title: str = Field(..., description="文章标题")
    article_content: str = Field(..., description="文章内容（HTML格式）")
    image_url: str = Field(..., description="配图URL")


class PublishToWechatOutput(BaseModel):
    """微信公众号发布节点的输出"""
    publish_result: Dict[str, Any] = Field(..., description="发布结果，包含media_id、publish_id等")


class SavePublishedInput(BaseModel):
    """保存已发布节点的输入"""
    filtered_news: List[Dict[str, Any]] = Field(..., description="发布的新闻列表")
    article_title: str = Field(..., description="文章标题")
    article_content: str = Field(..., description="文章内容")
    image_url: str = Field(..., description="配图URL")
    publish_result: Dict[str, Any] = Field(..., description="发布结果")


class SavePublishedOutput(BaseModel):
    """保存已发布节点的输出"""
    save_result: Dict[str, Any] = Field(..., description="保存结果，包含保存的新闻ID等")
