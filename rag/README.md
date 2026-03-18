# RAG 智能问答系统

基于 LangGraph 和 Milvus 的自适应检索增强生成(RAG)系统,支持向量检索、文档评分、查询优化和网络搜索回退。

## 核心特性

- **自适应路由**: 自动判断问题类型,选择向量检索或网络搜索
- **混合检索**: 结合 BM25 稀疏检索和向量密集检索
- **文档评分**: 智能评估检索文档与问题的相关性
- **查询优化**: 自动重写问题以提高检索质量
- **幻觉检测**: 验证生成内容是否基于参考文档
- **流式响应**: 支持实时流式返回处理过程

## 系统架构

```
用户问题 → 问题路由 → [向量检索 / 网络搜索]
              ↓
         文档评分 → 决策节点 → [生成答案 / 查询优化 / 网络搜索]
              ↓
         生成答案 → 质量评估 → [返回结果 / 重新生成 / 查询优化]
```

## 技术栈

- **框架**: FastAPI + LangChain + LangGraph
- **向量数据库**: Milvus (支持混合检索)
- **LLM**: OpenAI GPT-4o-mini / DeepSeek
- **嵌入模型**: Qwen Embedding (1024维)
- **网络搜索**: Tavily API
- **文档解析**: Markdown Parser

## 项目结构

```
rag/
├── app.py                      # FastAPI Web 服务入口
├── graph2/                     # LangGraph 工作流
│   ├── graph_2.py             # 主工作流定义
│   ├── graph_state2.py        # 状态管理
│   ├── retriever_node.py      # 向量检索节点
│   ├── grade_documents_node.py # 文档评分节点
│   ├── generate_node2.py      # 答案生成节点
│   ├── transform_query_node.py # 查询优化节点
│   ├── web_search_node.py     # 网络搜索节点
│   ├── query_route_chain.py   # 问题路由链
│   ├── grader_chain.py        # 文档评分链
│   ├── grade_hallucinations_chain.py # 幻觉检测链
│   └── grade_answer_chain.py  # 答案评估链
├── document/                   # 文档处理
│   ├── markdown_parser.py     # Markdown 解析器
│   ├── milvus_db.py          # Milvus 数据库操作
│   └── write_milvus.py       # 数据写入工具
├── llm_model/                 # 模型配置
│   ├── all_llm.py            # LLM 实例
│   └── embeddings_model.py   # 嵌入模型
├── tools/                     # 工具模块
│   └── retriever_tools.py    # 检索工具
├── utils/                     # 工具函数
│   ├── load_env.py           # 环境变量加载
│   ├── log_utils.py          # 日志工具
│   └── print_utils.py        # 打印工具
├── templates/                 # 前端模板
│   ├── index.html            # 聊天界面
│   └── graph_monitor.html    # 流程监控界面
├── static/                    # 静态资源
├── datas/                     # 数据目录
└── logs/                      # 日志目录
```

## 快速开始

### 1. 环境配置

创建 `.env` 文件并配置以下环境变量:

```bash
# LLM API 配置
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1

DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

QWEN_API_KEY=your_qwen_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 网络搜索 API
TAVILY_API_KEY=your_tavily_key

# Milvus 数据库
MILVUS_URI=./milvus_demo.db
```

### 2. 安装依赖

```bash
pip install fastapi uvicorn[standard]
pip install langchain langchain-openai langchain-milvus
pip install langgraph
pip install pymilvus
pip install python-dotenv
pip install tavily-python
pip install jinja2
```

### 3. 初始化数据库

```bash
# 解析 Markdown 文档并写入 Milvus
python document/write_milvus.py
```

### 4. 启动服务

```bash
# 方式1: 直接运行
python app.py

# 方式2: 使用 uvicorn 命令
uvicorn app:app --host 0.0.0.0 --port 5000 --reload
```

服务将在 `http://localhost:5000` 启动

## API 接口

### 1. 标准问答接口

```http
POST /api/chat
Content-Type: application/json

{
  "question": "你的问题"
}
```

响应:
```json
{
  "answer": "生成的答案",
  "success": true
}
```

### 2. 流式问答接口

```http
POST /api/chat/stream
Content-Type: application/json

{
  "question": "你的问题"
}
```

返回 Server-Sent Events (SSE) 流:
```
data: {"type": "start", "question": "..."}
data: {"type": "node", "node": "retriever", "data": {...}}
data: {"type": "node", "node": "generate", "data": {...}}
data: {"type": "end", "answer": "..."}
```

## 工作流程详解

### 1. 问题路由 (route_question)
- 分析问题类型
- 决策: `vectorstore` (向量检索) 或 `websearch` (网络搜索)

### 2. 向量检索 (retrieve)
- 使用混合检索 (BM25 + 向量相似度)
- 返回 Top-K 相关文档

### 3. 文档评分 (grade_documents)
- 评估每个文档与问题的相关性
- 过滤不相关文档

### 4. 决策节点 (decide_to_generate)
- 有相关文档 → 生成答案
- 无相关文档且未达重试上限 → 查询优化
- 无相关文档且达重试上限 → 网络搜索

### 5. 查询优化 (transform_query)
- 重写问题以提高检索效果
- 返回检索节点重新检索

### 6. 网络搜索 (web_search)
- 使用 Tavily API 搜索最新信息
- 返回搜索结果作为上下文

### 7. 答案生成 (generate)
- 基于文档/搜索结果生成答案
- 使用 LLM 生成自然语言回答

### 8. 质量评估 (grade_generation)
- **幻觉检测**: 验证答案是否基于参考文档
- **答案评估**: 验证答案是否回答了问题
- 决策: `useful` (结束) / `not useful` (查询优化) / `not supported` (重新生成)

## Milvus 数据库设计

### Collection Schema

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT64 | 主键(自增) |
| text | VARCHAR(6000) | 文档文本内容 |
| category | VARCHAR(1000) | 文档类别 |
| source | VARCHAR(1000) | 来源路径 |
| filename | VARCHAR(1000) | 文件名 |
| filetype | VARCHAR(1000) | 文件类型 |
| title | VARCHAR(1000) | 标题 |
| category_depth | INT64 | 类别深度 |
| sparse | SPARSE_FLOAT_VECTOR | BM25 稀疏向量 |
| dense | FLOAT_VECTOR(1024) | 密集向量 |

### 索引配置

- **稀疏索引**: SPARSE_INVERTED_INDEX (BM25, k1=1.6, b=0.75)
- **密集索引**: HNSW (M=16, efConstruction=64, 内积距离)

## 前端界面

### 1. 聊天界面 (`/`)
- 简洁的问答交互界面
- 支持实时对话

### 2. 流程监控界面 (`/monitor`)
- 可视化展示工作流执行过程
- 实时显示每个节点的状态和数据

## 配置说明

### LLM 模型选择

在 `llm_model/all_llm.py` 中配置:
- `openai_llm`: GPT-4o-mini (默认)
- `deepseek_llm`: DeepSeek Chat

### 检索参数调整

在 `tools/retriever_tools.py` 中调整:
- `k`: 检索文档数量
- `rerank_k`: 重排序后保留数量
- 混合检索权重

### 工作流参数

在 `graph2/graph_2.py` 中调整:
- `transform_count`: 查询优化最大次数 (默认2次)
- 条件分支逻辑

## 日志

日志文件保存在 `logs/` 目录:
- 记录每个节点的执行状态
- 记录决策过程和评分结果
- 便于调试和性能分析

## 注意事项

1. 首次运行需要初始化 Milvus 数据库
2. 确保所有 API Key 配置正确
3. Markdown 文档需要放在 `datas/md/` 目录
4. 建议使用 GPU 加速嵌入模型推理
5. 生产环境建议使用独立的 Milvus 服务器

## 许可证

MIT License
