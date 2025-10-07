# Yeying 面试官

基于 AI 的智能面试系统，支持简历解析、面试题自动生成和多轮对话管理。

## 快速开始

### 环境要求

- Python 3.11+

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd yeying-interviewer

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必需的 API Key

# 4. 启动应用
python app.py
```

### 访问应用

打开浏览器访问：http://localhost:8080

## 环境配置

编辑 `.env` 文件，配置以下必需项：

```bash
# 通义千问 API
QWEN_API_KEY=your_qwen_api_key

# Flask 密钥
SECRET_KEY=your_random_secret_key

# MinerU API
MINERU_API_KEY=your_mineru_api_key
```

## 开发指南

```bash
# 运行测试
python -m pytest tests/

# 查看日志
tail -f logs/interviewer.log
```