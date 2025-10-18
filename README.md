# Yeying面试官系统

基于RAG的智能面试辅助平台，提供简历解析、智能题目生成、面试过程管理和AI评估报告等功能。

## 快速开始

### 方式一：Docker部署（推荐）

**环境要求**
- Docker 20.10+
- Docker Compose 1.29+

**部署步骤**

```bash
# 1. 克隆项目
git clone <repository-url>
cd interviewer

# 2. 配置环境变量
# 编辑 docker-compose.yml，修改以下配置：
# - QWEN_API_KEY: 通义千问API密钥
# - SECRET_KEY: Flask应用密钥
# - MINERU_API_KEY: MinerU API密钥

# 3. 启动服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f

# 5. 停止服务
docker-compose down
```

访问地址：`http://localhost:8080`

### 方式二：本地开发

**环境要求**
- Python 3.11+
- pip

**安装步骤**

```bash
# 1. 克隆项目
git clone <repository-url>
cd interviewer

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必需的配置项

# 4. 初始化数据库（首次运行）
python app.py

# 5. 启动应用
python app.py
```

访问地址：`http://localhost:8080`

## 配置说明

### 必需配置

在 `.env` 文件中配置以下参数：

```bash
# AI服务配置
QWEN_API_KEY=sk-xxx                    # 通义千问API密钥

# 应用配置
SECRET_KEY=your-random-secret-key      # Flask应用密钥（建议使用随机字符串）

# MinerU配置
MINERU_API_KEY=your-mineru-key        # MinerU API密钥

# MinIO配置（可选）
MINIO_ENDPOINT=localhost:9000          # MinIO服务地址
MINIO_ACCESS_KEY=minioadmin           # MinIO访问密钥
MINIO_SECRET_KEY=minioadmin           # MinIO私钥
MINIO_BUCKET=yeying-interviewer       # 存储桶名称
```

### 可选配置

```bash
# 日志配置
LOG_LEVEL=INFO                        # 日志级别：DEBUG/INFO/WARNING/ERROR

# 调试模式
FLASK_DEBUG=false                     # 生产环境请设置为false

# 服务端口
APP_PORT=8080                         # 应用监听端口
```