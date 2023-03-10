# https://hub.docker.com/_/python/, 镜像名说明: 前缀python可选自url; 后缀:3.6-alpine为网页上的tag, 如不指定后缀, 则为:latest
FROM python:3.7.3-slim-stretch

# 一. 安装 linux package. (使用: 阿里云 alpine 镜像)
ADD requirements/sources.list.tencent /app/requirements/sources.list.tencent

RUN ln -snf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo Asia/Shanghai > /etc/timezone \
    && cp /app/requirements/sources.list.tencent  /etc/apt/sources.list \
    && apt-get update

# 二. 安装 python package.
ADD requirements/requirements.txt /app/requirements/requirements.txt

RUN pip3 install --no-cache-dir --upgrade pip --trusted-host mirrors.tencent.com --index-url https://mirrors.tencent.com/pypi/simple/ \
    && pip3 install --no-cache-dir -r /app/requirements/requirements.txt --trusted-host mirrors.tencent.com --index-url https://mirrors.tencent.com/pypi/simple/


# WORKDIR: 如果目录不存在, 则自动创建
WORKDIR /app/
ENV PYTHONPATH="/app/src:${PYTHONPATH}"
