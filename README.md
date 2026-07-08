# 🌐 Web Content Fetcher (MCP Server)

[![GitHub Actions CI/CD](https://github.com/你的GitHub用户名/仓库名/actions/workflows/docker-build.yml/badge.svg)](https://github.com/你的GitHub用户名/仓库名/actions)
![Docker Image](https://img.shields.io/badge/Docker-Aliyun%20ACR-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-green)
![MCP](https://img.shields.io/badge/MCP-1.0%2B-purple)

基于 **Model Context Protocol (MCP)** 标准构建的增强型网页内容抓取服务。旨在为大语言模型（LLM）提供精准、去噪、可结构化的网页交互能力。

---

## ✨ 核心特性

- 🎯 **精准 CSS 选择器过滤**：支持指定 `.article-content` 或 `#main` 节点提取，拒绝无用 Token 浪费。
- 📝 **自动转 Markdown**：集成 `html2text`，保留标题、列表、表格等高价值结构化格式。
- 🔗 **链接与元数据提取**：自动解析网页 `Title`、`Description` 及核心超链接列表，支持 LLM 的自主决策链。
- 🛡️ **反爬与去噪**：自动移除 `<script>`、`<style>`、`<iframe>` 等干扰节点，并伪装 Request Headers。
- 🚀 **云原生 CI/CD**：集成 GitHub Actions，自动化构建镜像并同步至阿里云 ACR 个人版/企业版镜像仓库。

---

## 🛠️ 技术栈

- **Language**: Python 3.10+
- **Protocol**: Model Context Protocol (MCP)
- **Parsing**: BeautifulSoup4, html2text, requests
- **DevOps**: Docker, GitHub Actions, Aliyun ACR

---

## 🚀 快速开始

### 1. 本地直接运行 (Local Environment)

#### 克隆仓库与安装依赖
```bash
git clone [https://github.com/你的GitHub用户名/你的仓库名.git](https://github.com/你的GitHub用户名/你的仓库名.git)
cd 你的仓库名

# 安装依赖
pip install -r requirements.txt