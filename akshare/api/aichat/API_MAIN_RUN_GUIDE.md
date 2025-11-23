# AKShare API 主运行函数说明

## 📝 添加内容

为 `akshare/api/main.py` 添加了完整的主运行函数。

## 📋 文件修改

### 添加的导入
```python
import logging
import uvicorn
```

### 添加的日志配置
```python
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### 添加的主运行函数
```python
if __name__ == "__main__":
    logger.info("启动 AKShare API 服务器...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )
```

## 🚀 使用方法

### 启动 API 服务器
```bash
cd /Users/dwx/Documents/GitHub/akshare
python akshare/api/main.py
```

### 输出示例
```
2024-11-23 10:30:45,123 - __main__ - INFO - 启动 AKShare API 服务器...
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 访问 API
- **根路由**: http://localhost:8000/
- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc
- **期货路由**: http://localhost:8000/futures/...

## 📊 配置详解

| 配置项 | 值 | 说明 |
|--------|-----|------|
| `host` | `0.0.0.0` | 监听所有网络接口 |
| `port` | `8000` | 服务端口号 |
| `log_level` | `info` | 日志级别 |
| `reload` | `False` | 关闭自动重载 (生产模式) |

## 🔧 修改配置

### 开发模式 (启用热重载)
```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    log_level="debug",
    reload=True  # 修改文件时自动重启
)
```

### 指定端口
```python
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8080,  # 修改为 8080
    log_level="info",
    reload=False
)
```

### 仅本地访问
```python
uvicorn.run(
    app,
    host="127.0.0.1",  # 仅本地
    port=8000,
    log_level="info",
    reload=False
)
```

## ✨ 功能说明

1. **日志记录**: 记录服务器启动信息
2. **服务启动**: 使用 uvicorn 启动 FastAPI 应用
3. **路由配置**: 自动加载期货模块的路由
4. **API 文档**: 自动生成 Swagger 和 ReDoc 文档

## 📚 相关文件

- `akshare/api/routers/futures.py` - 期货路由定义
- `akshare/futures/futures_hist_em.py` - 期货数据获取模块

## ✅ 检查清单

- ✓ 日志配置完成
- ✓ 主运行函数已添加
- ✓ uvicorn 服务器启动代码就绪
- ✓ 代码语法检查通过

