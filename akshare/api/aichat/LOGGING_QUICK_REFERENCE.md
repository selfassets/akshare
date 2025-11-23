# 日志记录快速参考

## 📋 实现概览

为 `akshare/futures/futures_hist_em.py` 模块中的所有函数添加了完整的日志记录系统。

## 📊 日志统计

- **DEBUG 日志**: 50+ 条 (详细调试信息)
- **INFO 日志**: 15+ 条 (关键流程信息)  
- **WARNING 日志**: 3+ 条 (潜在问题警告)
- **ERROR 日志**: 10+ 条 (异常捕获)

## 🎯 主要改进点

### 1. 流程追踪
```
[INFO] 开始获取交易所品种原始数据
  ↓
[DEBUG] 请求主品种数据, URL: ...
[DEBUG] 成功获取主品种数据, 共 N 个市场
  ↓
[DEBUG] 处理市场 1/N, 市场ID: ...
[DEBUG] 市场 ID 获得 M 组数据
  ↓
[INFO] 成功获取所有交易所品种数据, 总计 X 条记录
```

### 2. 异常处理
所有主要异常都被捕获并记录：
- `requests.exceptions.Timeout` - 请求超时
- `requests.exceptions.RequestException` - HTTP 请求错误
- `KeyError` - 符号映射缺失
- `Exception` - 其他异常

### 3. 数据进度
记录关键数据节点：
- 原始数据行数
- 过滤后数据行数
- 最终数据形状
- 数据摘要

## 🔍 日志示例

### 成功执行
```
2024-11-23 10:30:45,123 - akshare.futures.futures_hist_em - INFO - 开始获取期货行情数据 - 品种: 热卷主连, 周期: daily, 日期范围: 19900101~20500101
2024-11-23 10:30:45,124 - akshare.futures.futures_hist_em - DEBUG - 获取交易所品种映射
2024-11-23 10:30:45,200 - akshare.futures.futures_hist_em - INFO - 成功获取 1000 条原始行情数据
2024-11-23 10:30:45,201 - akshare.futures.futures_hist_em - DEBUG - 原始数据形状: (1000, 14)
2024-11-23 10:30:45,250 - akshare.futures.futures_hist_em - INFO - 期货行情数据获取成功, 最终数据形状: (500, 10)
```

### 错误处理
```
2024-11-23 10:30:45,999 - akshare.futures.futures_hist_em - ERROR - 请求超时 - 品种: 焦煤2506
Traceback (most recent call last):
  ...
requests.exceptions.Timeout: Connection timeout
```

## 💡 配置建议

### 开发环境
```python
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 生产环境
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/akshare_futures.log',
    filemode='a'
)
```

### 同时输出到控制台和文件
```python
import logging

# 创建日志记录器
logger = logging.getLogger('akshare')
logger.setLevel(logging.DEBUG)

# 文件处理器
fh = logging.FileHandler('akshare.log')
fh.setLevel(logging.INFO)

# 控制台处理器
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# 格式化
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)
```

## 📝 日志内容详解

### 符号分离函数
```
[DEBUG] 开始分离符号: 焦煤2506
[DEBUG] 分离结果 - 字符部分: 焦煤, 数字部分: 2506
```

### 映射构建
```
[INFO] 映射构建完成 - 中文合约: 150, 合约代码: 150, 英文符号: 150, 中文符号: 150
[DEBUG] 中文符号映射示例: {'焦煤': 50, '焦炭': 51, ...}
```

### 数据处理
```
[DEBUG] 原始数据形状: (1000, 14)
[DEBUG] 列选择完成
[DEBUG] 时间索引转换完成, 时间范围: 2024-01-01 - 2024-11-23
[DEBUG] 按日期范围过滤: 19900101 到 20500101
[INFO] 过滤后数据行数: 500
[DEBUG] 开始数据类型转换
[DEBUG] 数据类型转换完成
```

## 🚀 最佳实践

1. **在应用启动时配置日志**
   - 在主程序中统一配置，避免重复配置
   - 使用配置文件管理日志设置

2. **不记录敏感信息**
   - 已避免记录完整 API URL 参数
   - 不记录认证令牌或密钥

3. **定期检查日志**
   - 监控 ERROR 级别的日志
   - 分析 WARNING 级别的警告

4. **日志轮转**
   - 在生产环境中使用 RotatingFileHandler
   - 防止日志文件无限增长

## 📞 支持

如有问题或建议，请参考 `LOGGING_IMPLEMENTATION.md` 文档。

