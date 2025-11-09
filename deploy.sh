set -x
export MINIO_ENDPOINT=127.0.0.1:9000
export MINIO_ACCESS_KEY=H9zLWI2iXRGIeO46QmLW
export MINIO_SECRET_KEY=gQyqHBJpyWI0CJ3jdOi8K3vI41JLctuFPFCCuWtE
export MINIO_BUCKET=public-bucket
export MINIO_SECURE=false


# ==================== Flask 配置 ====================
export SECRET_KEY=your_secret_key_here_please_change_in_production
export FLASK_DEBUG=false  # 生产环境务必设为 false
export LOG_LEVEL=INFO     # 日志级别: DEBUG(开发) / INFO(生产) / WARNING / ERROR

# ==================== 数据库配置 ====================
export DATABASE_PATH=data/yeying_interviewer.db

# ==================== Qwen API 配置 ====================
export QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
export QWEN_API_KEY=your_qwen_api_key_here
export MODEL_NAME=qwen-turbo

# ==================== MinerU API 配置 ====================
export MINERU_API_KEY=your_mineru_api_key_here
export MINERU_API_URL=https://mineru.net/api/v4


# ==================== RAG 服务配置 ====================
export RAG_API_URL=http://localhost:8000
export RAG_TIMEOUT=30

# ==================== DigitalHub 配置 ====================
export PUBLIC_HOST=your_public_host_here
export LLM_PORT=8011

# ==================== 应用配置 ====================
export APP_HOST=0.0.0.0
export APP_PORT=8088


export JWT_SECRET=e802e988a02546cc47415e4bc76346aae7ceece97a0f950319c861a5de38b20d
python app.py

# 钱包登录和校验接口 swagger ui
# http://0.0.0.0:8088/ui/
set +x