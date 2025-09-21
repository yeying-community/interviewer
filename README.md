# Yeying面试官 (Yeying Interviewer)

一个基于AI的智能面试系统，集成通义千问大模型和MinIO对象存储，支持面试题智能生成和会话管理。

## ✨ 核心功能

- 🤖 **AI智能面试题生成**: 基于简历内容自动生成分类面试题（基础题/项目题/场景题）
- 🏠 **多面试间管理**: 支持创建多个面试间，每个面试间可包含多个面试会话
- 💾 **数据持久化**: 使用SQLite数据库和MinIO对象存储，确保数据安全可靠
- 🔄 **轮次管理**: 每个面试会话可包含多个对话轮次，支持历史回顾
- 🌐 **Web界面**: 提供ChatGPT风格的聊天界面，用户体验友好

## 🏗️ 项目架构

```
yeying-interviewer/
├── app.py                         # Flask应用主入口
├── requirements.txt               # Python依赖包
├── CLAUDE.md                      # Claude Code开发指南
├── DATABASE.md                    # 数据库设计文档
├── .env                           # 环境变量配置
├── .env.example                   # 环境变量示例
│
├── backend/                       # 后端核心模块
│   ├── models/                    # 数据模型 (Peewee ORM)
│   │   └── models.py              # Room/Session/Round数据模型
│   ├── services/                  # 业务逻辑层
│   │   ├── interview_service.py   # 面试管理服务
│   │   └── question_service.py    # 问题生成服务
│   ├── api/                       # API路由
│   │   └── routes.py              # Flask蓝图路由定义
│   └── utils/                     # 工具模块
│       └── minio_client.py        # MinIO对象存储客户端
│
├── llm/                           # 大模型集成
│   ├── clients/                   # LLM客户端
│   │   └── qwen_client.py         # 通义千问API客户端
│   └── prompts/                   # 提示词模板
│       └── question_prompts.py    # 面试题生成提示词
│
├── rag/                           # RAG组件 (预留)
│   ├── embeddings/                # 文本向量化
│   └── retrieval/                 # 检索模块
│
├── frontend/                      # 前端界面
│   ├── static/                    # 静态资源 (CSS/JS)
│   └── templates/                 # Jinja2模板
│       ├── index.html             # 首页 - 面试间列表
│       ├── room.html              # 面试间详情页
│       └── session.html           # 面试会话页面
│
├── tests/                         # 测试代码
│   ├── data/                      # 测试数据
│   ├── test_api.py                # API测试
│   ├── test_database.py           # 数据库测试
│   └── test_minio.py              # MinIO测试
│
└── data/                          # 本地数据目录
    ├── resume.json                # 候选人简历数据
    ├── questions_round_*.json     # 生成的面试题数据
    └── yeying_interviewer.db      # SQLite数据库文件
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd yeying-interviewer

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必要的环境变量
nano .env
```

**必需的环境变量**:
```bash
# 通义千问API配置
API_KEY=your_qwen_api_key_here
MODEL_NAME=qwen-turbo

# Flask应用配置
SECRET_KEY=your_secret_key_here

# 数据库配置 (可选，默认使用SQLite)
DATABASE_PATH=data/yeying_interviewer.db
```

### 3. 初始化数据

```bash
# 上传测试数据到MinIO (可选)
python upload_data_to_minio.py
```

### 4. 启动应用

```bash
# 启动Flask应用
python app.py
```

### 5. 访问应用

- **主应用**: http://localhost:8080
- **API测试端点**: http://localhost:8080/api/minio/test

## 🔧 开发指南

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试文件
python -m pytest tests/test_api.py
```

### 系统概念

- **Room (面试间)**: 具有唯一memory_id的面试空间
- **Session (面试会话)**: 面试间内的具体面试会话
- **Round (对话轮次)**: 会话内的Q&A轮次，每轮生成新的面试题

### 数据流

1. 从MinIO加载简历数据 (`data/resume.json`)，本地文件作为备用
2. 使用分类提示词将格式化简历发送到通义千问API
3. 解析生成的问题并存储到rounds中
4. 将问题保存到MinIO (`data/questions_round_{index}.json`)，本地文件作为备用

## 📋 API文档

### 主要API端点

- `GET /` - 首页，显示面试间列表和统计信息
- `GET /room/<room_id>` - 面试间详情页
- `GET /session/<session_id>` - 面试会话页面
- `POST /generate_questions/<session_id>` - 生成面试题
- `GET /api/rooms` - 获取所有面试间
- `GET /api/sessions/<room_id>` - 获取指定面试间的会话
- `GET /api/rounds/<session_id>` - 获取指定会话的轮次

### MinIO集成

系统默认连接到 `test-minio.yeying.pub`，如果连接失败会自动降级到本地文件存储。

## 🛠️ 技术栈

- **后端**: Flask + Peewee ORM
- **数据库**: SQLite (生产环境可切换到PostgreSQL/MySQL)
- **对象存储**: MinIO
- **大模型**: 通义千问 (Qwen)
- **前端**: Jinja2模板 + 原生JavaScript
- **测试**: pytest

## 📝 注意事项

1. **API密钥安全**: 请勿将API密钥提交到版本控制系统
2. **MinIO配置**: 生产环境需要配置自己的MinIO服务器
3. **数据库**: 默认使用SQLite，生产环境建议使用PostgreSQL
4. **端口配置**: 应用默认运行在8080端口

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情