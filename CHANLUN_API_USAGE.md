# 缠论分析 API 使用示例

## 快速开始

### 1. 启动 API 服务

```bash
cd /Users/dwx/Documents/GitHub/akshare
python start_api.py
```

或者：

```bash
python -m akshare.api.main
```

### 2. 访问 API 文档

在浏览器中打开：

- Swagger UI: http://localhost:8000/docs
- 健康检查: http://localhost:8000/chanlun/health

## API 接口

### 1. 完整缠论分析

**接口**: `GET /chanlun/analyze`

**参数**:

- `symbol`: 期货品种（默认：热卷主连）
- `start_date`: 开始日期 YYYYMMDD（默认：20240101）
- `end_date`: 结束日期 YYYYMMDD（默认：20241231）
- `level`: 分析级别（basic/advanced/full，默认：basic）

**示例**:

```bash
curl "http://localhost:8000/chanlun/analyze?symbol=热卷主连&start_date=20240101&end_date=20240331&level=basic"
```

**响应格式**:

```json
{
  "bars_raw": [...],
  "bars_merged": [...],
  "fractals": [
    {
      "type": "top",
      "dt": "2024-01-05T00:00:00",
      "high": 3050.0,
      "low": 3030.0,
      "price": 3050.0
    }
  ],
  "strokes": [
    {
      "direction": "up",
      "start_dt": "2024-01-01T00:00:00",
      "end_dt": "2024-01-05T00:00:00",
      "start_price": 2995.0,
      "end_price": 3050.0,
      "power": 55.0
    }
  ],
  "stats": {
    "total_fractals": 31,
    "total_strokes": 20
  }
}
```

### 2. 仅获取分型

**接口**: `GET /chanlun/fractals`

**示例**:

```bash
curl "http://localhost:8000/chanlun/fractals?symbol=热卷主连&start_date=20240101&end_date=20240331"
```

### 3. 仅获取笔

**接口**: `GET /chanlun/strokes`

**示例**:

```bash
curl "http://localhost:8000/chanlun/strokes?symbol=热卷主连&start_date=20240101&end_date=20240331"
```

## Python 调用示例

```python
import requests

# 完整分析
response = requests.get(
    "http://localhost:8000/chanlun/analyze",
    params={
        "symbol": "热卷主连",
        "start_date": "20240101",
        "end_date": "20240331",
        "level": "basic"
    }
)

data = response.json()
print(f"识别到 {data['stats']['total_fractals']} 个分型")
print(f"识别到 {data['stats']['total_strokes']} 笔")

# 打印前5个分型
for fractal in data['fractals'][:5]:
    print(f"{fractal['type']}: {fractal['dt']} - 价格: {fractal['price']}")
```

## JavaScript 调用示例

```javascript
const response = await fetch(
  "http://localhost:8000/chanlun/analyze?" +
    new URLSearchParams({
      symbol: "热卷主连",
      start_date: "20240101",
      end_date: "20240331",
      level: "basic",
    })
);

const data = await response.json();
console.log(`识别到 ${data.stats.total_fractals} 个分型`);
console.log(`识别到 ${data.stats.total_strokes} 笔`);
```

## 直接使用 Python 模块

不启动 API 服务，直接调用核心模块：

```python
from akshare.api.analysis.chanlun_core import ChanlunAnalyzer, create_bars_from_dataframe
from akshare.futures_derivative.futures_index_sina import futures_main_sina

# 获取K线数据
df = futures_main_sina(
    symbol="热卷主连",
    start_date="20240101",
    end_date="20240331"
)

# 转换为Bar列表
bars = create_bars_from_dataframe(df, symbol="热卷主连")

# 执行分析
analyzer = ChanlunAnalyzer(bars)

# 查看结果
print(f"原始K线: {len(analyzer.bars_raw)} 根")
print(f"合并后K线: {len(analyzer.bars_merged)} 根")
print(f"识别分型: {len(analyzer.fractals)} 个")
print(f"识别笔: {len(analyzer.strokes)} 笔")

# 查看分型详情
for i, fractal in enumerate(analyzer.fractals[:5]):
    print(f"[{i}] {fractal.fractal_type.value}: {fractal.dt} - {fractal.price}")

# 查看笔详情
for i, stroke in enumerate(analyzer.strokes[:5]):
    print(f"[{i}] {stroke.direction.value}: "
          f"{stroke.start_price:.2f} -> {stroke.end_price:.2f} "
          f"(力度: {stroke.power:.2f})")

# 转换为JSON格式
result = analyzer.to_dict()
```

## 与 czsc 库的对比

新的 `/chanlun` 接口与现有的 `/czsc` 接口并存：

| 特性     | /chanlun       | /czsc        |
| -------- | -------------- | ------------ |
| 依赖     | 无外部依赖     | 依赖 czsc 库 |
| 实现     | 自主实现       | czsc 库实现  |
| 性能     | 轻量级         | 功能更丰富   |
| 可定制性 | 高，可自由扩展 | 受限于库     |

两个接口可以同时使用，互不影响。
