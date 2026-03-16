from typing import List, Dict
from langchain_core.runnables import RunnableConfig
from langgraph.runtime import Runtime
from coze_coding_utils.runtime_ctx.context import Context
from coze_coding_dev_sdk import ImageGenerationClient
from coze_coding_utils.runtime_ctx.context import new_context

from graphs.state import GenerateImageInput, GenerateImageOutput


def generate_image_node(state: GenerateImageInput, config: RunnableConfig, runtime: Runtime[Context]) -> GenerateImageOutput:
    """
    title: 生成文章配图
    desc: 根据文章标题和内容，生成一张适合的科技风格配图
    integrations: image-generation
    """
    ctx = runtime.context
    
    article_title = state.article_title
    article_content = state.article_content
    
    # 根据文章内容生成图片提示词
    # 提取文章主题关键词
    keywords = []
    if "AI" in article_title or "人工智能" in article_title:
        keywords.append("人工智能技术")
    if "科技" in article_title:
        keywords.append("科技前沿")
    if "芯片" in article_title or "芯片" in article_content:
        keywords.append("高科技芯片")
    if "机器人" in article_title or "机器人" in article_content:
        keywords.append("智能机器人")
    if not keywords:
        keywords = ["科技", "创新", "未来"]
    
    # 构建图片提示词
    prompt = f"一张现代化的科技风格配图，展示{', '.join(keywords)}相关的概念。风格：简洁、专业、现代科技感，蓝色和紫色渐变色调，适合微信公众号封面，高质量，清晰锐利"
    
    # 初始化图片生成客户端
    img_ctx = new_context(method="generate")
    client = ImageGenerationClient(ctx=img_ctx)
    
    # 生成图片
    response = client.generate(
        prompt=prompt,
        size="2K",
        watermark=False
    )
    
    # 获取图片URL
    image_url = ""
    if response.success and response.image_urls:
        image_url = response.image_urls[0]
    else:
        # 生成失败，返回占位符
        image_url = "https://via.placeholder.com/800x400?text=AI+Tech+News"
    
    return GenerateImageOutput(image_url=image_url)
