#!/usr/bin/env python3
import asyncio
import json
import urllib.parse
import requests
from bs4 import BeautifulSoup as bs
import html2text

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.shared.exceptions import McpError
from mcp.types import (
    ErrorData,
    ImageContent,
    EmbeddedResource,
    LoggingLevel,
    Prompt,
    PromptMessage,
    Resource,
    TextContent,
    Tool,
)

import mcp.server.stdio
import mcp.types as types

# 1. 初始化标准 MCP 服务器
server = Server("web-content-fetcher")

def configure_html2text():
    """配置 html2text 解析器规则"""
    h = html2text.HTML2Text()
    h.ignore_links = False        # 保留文本中的链接
    h.ignore_images = True       # 忽略图片以节省 Token
    h.ignore_emphasis = False    # 保留加粗/斜体
    h.body_width = 0             # 不自动换行，保持文本段落完整
    return h

# 2. 注册工具（升级了 inputSchema，加入 selector 参数）
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_web_content",
            description="Fetch web page content with CSS selector filtering, structured Markdown formatting, metadata, and extracted links.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string", 
                        "description": "The URL to fetch content from"
                    },
                    "selector": {
                        "type": "string", 
                        "description": "Optional CSS selector to target specific element (e.g., '.article-body', '#content')"
                    }
                },
                "required": ["url"],
            },
        )
    ]

# 3. 处理工具调用逻辑
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name != "get_web_content":
        raise McpError(ErrorData(code=types.INVALID_REQUEST, message=f"Unknown tool: {name}"))
        
    if not arguments or "url" not in arguments:
        raise McpError(ErrorData(code=types.INVALID_REQUEST, message="Missing URL argument"))
        
    url = arguments["url"]
    selector = arguments.get("selector")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        
        soup = bs(r.text, "html.parser")
        
        # ----------------------------------------------------
        # 提取页面元数据 (Title & Description)
        # ----------------------------------------------------
        title = soup.title.string.strip() if soup.title and soup.title.string else "无标题"
        meta_desc = ""
        desc_tag = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
        if desc_tag and desc_tag.get("content"):
            meta_desc = desc_tag["content"].strip()

        # 清洗干扰标签
        for element in soup(["script", "style", "noscript", "iframe"]):
            element.decompose()

        # ----------------------------------------------------
        # 精准提取（CSS 选择器支持）
        # ----------------------------------------------------
        if selector:
            target_node = soup.select_one(selector)
            if target_node:
                content_node = target_node
            else:
                content_node = soup.body if soup.body else soup
                title += f" [警告: 未找到选择器 '{selector}'，已退回全页]"
        else:
            content_node = soup.body if soup.body else soup

        # ----------------------------------------------------
        # 提取区域内的重要超链接（供 AI 决策链使用）
        # ----------------------------------------------------
        extracted_links = []
        for a_tag in content_node.find_all("a", href=True):
            link_text = a_tag.get_text(strip=True)
            raw_href = a_tag["href"]
            full_href = urllib.parse.urljoin(url, raw_href)
            if link_text and full_href.startswith("http"):
                extracted_links.append({"text": link_text, "url": full_href})

        # 去重并截取前 15 个最核心链接
        unique_links = []
        seen = set()
        for item in extracted_links:
            if item["url"] not in seen:
                seen.add(item["url"])
                unique_links.append(item)
                if len(unique_links) >= 15:
                    break

        # ----------------------------------------------------
        # 使用 html2text 转换为漂亮的 Markdown
        # ----------------------------------------------------
        h2t = configure_html2text()
        markdown_body = h2t.handle(str(content_node)).strip()

        # 结构化数据
        result_data = {
            "metadata": {
                "title": title,
                "description": meta_desc,
                "url": url,
                "used_selector": selector if selector else "None (Full Page)"
            },
            "markdown_content": markdown_body,
            "extracted_links": unique_links
        }
        
        # 返回 JSON 字符串结果给 LLM
        return [types.TextContent(type="text", text=json.dumps(result_data, ensure_ascii=False, indent=2))]

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error fetching website: {str(e)}")]

# 4. 服务器启动主函数
async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="web-content-fetcher",
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass