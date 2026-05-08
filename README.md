# Fridge-to-Fork

AI 驱动的冰箱食材管理项目：拍摄冰箱照片，识别食材，维护库存，检测临期并推荐菜谱。

## 项目介绍

Fridge-to-Fork 是一个可以真实运行的全栈应用，不是脚本级 Demo。它围绕「减少食材浪费」设计了完整闭环：

- 拍照识别：上传冰箱图片，识别可见食材并估算数量
- 库存管理：按批次入库，事件流记录增减，支持扣减与追溯
- 临期预警：基于保质期规则与缓存策略检测即将过期食材
- 菜谱推荐：按临期紧急程度推荐可执行菜谱并给出推荐原因
- 工程化交付：提供 Web UI、REST API、CLI、Docker 启动方式

## 技术栈

- Python 3.11+
- FastAPI
- OpenAI Vision (`gpt-4o`)
- SQLite
- LangGraph
- Tavily Search

## 项目结构

```text
fridge-to-fork/
├── src/
│   ├── agents/
│   ├── config/
│   ├── db/
│   ├── models/
│   ├── services/
│   ├── tools/
│   ├── web/
│   │   ├── static/
│   │   └── templates/
│   ├── main.py
│   └── server.py
├── data/
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 快速开始

### 1) 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) 配置环境变量

复制 `.env.example` 为 `.env`，并填写：

- `OPENAI_API_KEY`
- `TAVILY_API_KEY`

其余配置可先使用默认值。

### 3) 启动服务

```bash
python -m src.server
```

打开：

- `http://localhost:8000`

## Docker 启动

```bash
docker compose up --build
```

## Web 功能

- 上传冰箱图片并分析
- 查看库存
- 获取临期菜谱推荐
- 标记已烹饪并扣减库存

## CLI 功能

```bash
python -m src.main scan --image path/to/fridge.jpg
python -m src.main inventory
python -m src.main recommend
python -m src.main cooked --ingredient tomato --quantity 1
```

## API

- `GET /api/health`
- `GET /api/inventory`
- `GET /api/recommend`
- `POST /api/scan`
  - body:
  ```json
  {
    "image_base64": "base64...",
    "filename": "fridge.jpg"
  }
  ```
- `POST /api/cooked`
  - body:
  ```json
  {
    "ingredient": "tomato",
    "quantity": 1
  }
  ```

## 说明

- 数据库默认路径：`data/fridge.db`
- API 缓存与预算数据存储在 `data/`
