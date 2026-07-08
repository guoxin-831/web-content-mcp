FROM docker.m.daocloud.io/library/python:3.11-slim

WORKDIR /app

# Debian12 专用腾讯镜像源替换
RUN sed -i 's/deb.debian.org/mirrors.tencent.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.tencent.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirement.txt .
# pip清华源加速
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirement.txt

COPY web-content-mcp.py .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "web-content-mcp.py"]