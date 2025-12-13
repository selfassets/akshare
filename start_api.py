#!/usr/bin/env python
"""
快速启动缠论分析API服务的脚本

使用方法:
    python start_api.py
    
然后在浏览器访问:
    http://localhost:8000/docs  (查看API文档)
    http://localhost:8000/chanlun/health  (健康检查)
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    from akshare.api.main import app
    
    print("=" * 80)
    print("启动缠论分析 API 服务")
    print("=" * 80)
    print("\n可用端点:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/docs (Swagger UI)")
    print("  - http://localhost:8000/chanlun/analyze")
    print("  - http://localhost:8000/chanlun/fractals")
    print("  - http://localhost:8000/chanlun/strokes")
    print("  - http://localhost:8000/chanlun/health")
    print("\n按 Ctrl+C 停止服务")
    print("=" * 80)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
