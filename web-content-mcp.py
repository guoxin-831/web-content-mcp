#!/usr/bin/env python3
import asyncio
import requests
from bs4 import BeautifulSoup as bs
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

import html2text

# 核心转换逻辑
h = html2text.HTML2Text()
h.ignore_links = False  # 是否保留超链接
h.ignore_images = True  # 过滤图片以节省 token
markdown_content = h.handle(r.text)

import mcp.server.stdio
import mcp.types as types

# 1. 初始化标准 MCP 服务器
server = Server("web-content-fetcher")

# 2. 注册工具
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_web_content",
            description="Get text content from a specific URL, removing HTML tags.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL to fetch content from"}
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
    
    # 【优化】：加入更完善的防反爬 Header 伪装
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    
    try:
        # 发送请求、解析网页、清洗文本
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        
        soup = bs(r.text, "html.parser")
        
        # 【优化】：清洗掉 <script> 和 <style> 标签，避免把前端代码当作纯文本返回
        for script in soup(["script", "style"]):
            script.extract()
            
        text_content = soup.get_text(separator='\n', strip=True)
        
        # 返回符合 MCP 规范的 TextContent 格式（截取前 2000 字给 AI）
        return [types.TextContent(type="text", text=text_content[:2000])]
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
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())