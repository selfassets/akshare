# 使用精简镜像，镜像体积从 1.2G 下降为约 400M，提高启动效率，同时升级到 Python 3.13.x 提高 20% 以上性能
FROM python:3.13-slim-bullseye

# 升级 pip 到最新版
RUN pip install --upgrade pip

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目源码
COPY . .

# 安装项目
RUN pip install --no-cache-dir .

# 默认启动 gunicorn 服务
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "akshare.api.main:app", "-k", "uvicorn.workers.UvicornWorker"]
