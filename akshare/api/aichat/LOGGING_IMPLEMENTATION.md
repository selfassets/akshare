# 期货历史数据模块日志记录实现总结

## 文件修改
- **文件路径**: `/Users/dwx/Documents/GitHub/akshare/akshare/futures/futures_hist_em.py`

## 实现内容

### 1. 日志配置
- 导入 `logging` 模块
- 创建模块级别的日志记录器: `logger = logging.getLogger(__name__)`
- 设置日志级别为 `DEBUG`，以记录所有详细信息

```python
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

### 2. 各函数日志记录

#### `__futures_hist_separate_char_and_numbers_em(symbol)`
- **DEBUG**: 记录输入符号和分离结果（字符部分和数字部分）

#### `__fetch_exchange_symbol_raw_em()`
- **INFO**: 记录获取开始和完成信息
- **DEBUG**: 记录每个市场的处理进度、API 请求情况、获取的数据组数
- **ERROR**: 捕获 HTTP 请求异常和其他异常，并记录详细错误信息

#### `__get_exchange_symbol_map()`
- **INFO**: 记录映射构建的开始和完成，以及各个映射字典的大小
- **DEBUG**: 记录映射示例数据
- **ERROR**: 捕获构建过程中的异常

#### `futures_hist_table_em()`
- **INFO**: 记录表获取的开始、完成和行列数信息
- **DEBUG**: 记录待转换记录数和表头信息
- **ERROR**: 捕获处理异常

#### `futures_hist_em(symbol, period, start_date, end_date)`
- **INFO**: 记录函数调用参数、获取数据成功、过滤后行数、最终数据形状
- **DEBUG**: 
  - 记录交易所品种映射的获取过程
  - 记录 sec_id 的获取方式（直接映射或解析符号）
  - 记录 API 请求信息
  - 记录原始数据形状
  - 记录列选择完成
  - 记录时间索引转换及时间范围
  - 记录日期范围过滤过程
  - 记录数据类型转换过程
  - 记录数据摘要（head 数据）
- **WARNING**: 记录未获取到数据或转换后数据为空的情况
- **ERROR**: 
  - HTTP 请求超时
  - HTTP 请求失败
  - 符号映射缺失
  - 其他异常

## 日志级别说明

| 级别 | 用途 | 示例 |
|------|------|------|
| DEBUG | 详细的调试信息 | 循环进度、数据中间状态 |
| INFO | 关键流程信息 | 函数开始/完成、数据行数 |
| WARNING | 潜在问题 | 获取到空数据、未找到结果 |
| ERROR | 错误信息 | 网络异常、数据不一致 |

## 使用日志的好处

1. **调试效率**: 快速定位问题发生的位置和原因
2. **性能监控**: 记录各步骤的数据量，帮助识别性能瓶颈
3. **错误追踪**: 完整的错误堆栈和上下文信息
4. **生产监控**: 在生产环境中记录关键指标

## 配置日志输出

可以在调用代码中配置日志输出:

```python
import logging

# 输出到控制台
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 或输出到文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='akshare_futures.log'
)

from akshare.futures.futures_hist_em import futures_hist_em
df = futures_hist_em(symbol="热卷主连", period="daily")
```

## 测试脚本

已创建测试脚本: `/Users/dwx/Documents/GitHub/akshare/test_logging.py`

使用方法:
```bash
cd /Users/dwx/Documents/GitHub/akshare
python test_logging.py
```

将输出详细的日志信息，包括每个步骤的进度和任何错误信息。

