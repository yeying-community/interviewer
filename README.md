# Yeying面试官 (Yeying Interviewer)

一个基于AI的智能面试系统，支持RAG知识检索和多种大模型集成。

## 项目结构

```
├── app.py                         # Flask应用入口
├── requirements.txt               # Python依赖包
├── config.py                      # 配置文件
├── .env                           # 环境变量
├── .gitignore                     # Git忽略文件
│
├── backend/                       # 后端核心代码
│   ├── models/                    # 数据模型
│   ├── services/                  # 业务逻辑层
│   ├── api/                       # API路由
│   ├── database/                  # 数据库相关
│   └── utils/                     # 工具类
│
├── rag/                           # RAG相关组件
│   ├── embeddings/                # 向量化处理
│   ├── retrieval/                 # 检索模块
│   └── knowledge_base/            # 知识库
│
├── llm/                           # 大模型集成
│   ├── clients/                   # 不同LLM客户端
│   ├── prompts/                   # 提示词模板
│   └── processors/                # 响应处理
│
├── frontend/                      # 前端代码
│   ├── static/                    # 静态资源
│   └── templates/                 # HTML模板
│
├── tests/                         # 测试代码
├── logs/                          # 日志文件
├── data/                          # 数据文件
└── docs/                          # 文档
```

## 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的API密钥
   ```

3. **启动应用**
   ```bash
   python app.py
   ```

4. **访问应用**
   - 应用地址: http://localhost:5000
   - API测试端点:
     - http://localhost:5000/api/interview/test
     - http://localhost:5000/api/room/test
     - http://localhost:5000/api/question/test