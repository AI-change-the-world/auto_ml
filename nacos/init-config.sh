#!/bin/sh
set -e

echo "📝 Starting Nacos config initialization..."

# 等待 MinIO 初始化完成并读取凭证
if [ -f "$MINIO_ENV_FILE" ]; then
  echo "📄 Loading MinIO credentials from $MINIO_ENV_FILE"
  . "$MINIO_ENV_FILE"
else
  echo "⚠️ MinIO env file not found, using default credentials"
  ACCESS_KEY="minioadmin"
  SECRET_KEY="minioadmin123"
fi

# 其他配置默认值
: "${MYSQL_HOST:=mysql}"
: "${MYSQL_PORT:=3306}"
: "${MYSQL_USER:=automl}"
: "${MYSQL_PASSWORD:=automl123456}"
: "${MYSQL_DATABASE:=auto_ml}"
: "${NACOS_NAMESPACE:=public}"

: "${RABBITMQ_HOST:=rabbitmq}"
: "${RABBITMQ_PORT:=5672}"
: "${RABBITMQ_USER:=automl}"
: "${RABBITMQ_PASSWORD:=automl123456}"
: "${RABBITMQ_VHOST:=/}"
: "${RABBITMQ_EXCHANGE:=auto_ml_exchange}"
: "${RABBITMQ_EXCHANGE_TYPE:=topic}"

: "${MINIO_ENDPOINT:=http://minio:9000}"
: "${MODEL_TRAINER_URL:=http://model-trainer:8081}"
: "${MODEL_DEPLOY_URL:=http://model-deploy:8082}"
: "${AI_PIPELINE_RUNTIME_URL:=http://ai-pipeline-runtime:8010}"
: "${AUTO_AUGMENT_PIPELINE_URL:=$AI_PIPELINE_RUNTIME_URL}"
: "${TASK_STALE_TIMEOUT_SECONDS:=7200}"

replace_placeholder() {
  var_name="$1"
  value="$2"
  placeholder="\${${var_name}}"
  escaped_value=$(printf '%s' "$value" | sed 's/[\/&]/\\&/g')
  CONFIG_CONTENT=$(printf '%s' "$CONFIG_CONTENT" | sed "s|${placeholder}|${escaped_value}|g")
}

publish_config() {
  file_path="$1"
  data_id="$2"

  if [ ! -f "$file_path" ]; then
    echo "❌ Config file not found: $file_path"
    exit 1
  fi

  CONFIG_CONTENT=$(cat "$file_path")

  replace_placeholder "ACCESS_KEY" "$ACCESS_KEY"
  replace_placeholder "SECRET_KEY" "$SECRET_KEY"
  replace_placeholder "MYSQL_HOST" "$MYSQL_HOST"
  replace_placeholder "MYSQL_PORT" "$MYSQL_PORT"
  replace_placeholder "MYSQL_USER" "$MYSQL_USER"
  replace_placeholder "MYSQL_PASSWORD" "$MYSQL_PASSWORD"
  replace_placeholder "MYSQL_DATABASE" "$MYSQL_DATABASE"
  replace_placeholder "RABBITMQ_HOST" "$RABBITMQ_HOST"
  replace_placeholder "RABBITMQ_PORT" "$RABBITMQ_PORT"
  replace_placeholder "RABBITMQ_USER" "$RABBITMQ_USER"
  replace_placeholder "RABBITMQ_PASSWORD" "$RABBITMQ_PASSWORD"
  replace_placeholder "RABBITMQ_VHOST" "$RABBITMQ_VHOST"
  replace_placeholder "RABBITMQ_EXCHANGE" "$RABBITMQ_EXCHANGE"
  replace_placeholder "RABBITMQ_EXCHANGE_TYPE" "$RABBITMQ_EXCHANGE_TYPE"
  replace_placeholder "MINIO_ENDPOINT" "$MINIO_ENDPOINT"
  replace_placeholder "MODEL_TRAINER_URL" "$MODEL_TRAINER_URL"
  replace_placeholder "MODEL_DEPLOY_URL" "$MODEL_DEPLOY_URL"
  replace_placeholder "AI_PIPELINE_RUNTIME_URL" "$AI_PIPELINE_RUNTIME_URL"
  replace_placeholder "AUTO_AUGMENT_PIPELINE_URL" "$AUTO_AUGMENT_PIPELINE_URL"
  replace_placeholder "TASK_STALE_TIMEOUT_SECONDS" "$TASK_STALE_TIMEOUT_SECONDS"
  replace_placeholder "NANO_BANANA_BASE_URL" "${NANO_BANANA_BASE_URL:-}"
  replace_placeholder "NANO_BANANA_API_KEY" "${NANO_BANANA_API_KEY:-}"
  replace_placeholder "NANO_BANANA_MODEL" "${NANO_BANANA_MODEL:-}"
  replace_placeholder "QWEN_BASE_URL" "${QWEN_BASE_URL:-}"
  replace_placeholder "QWEN_API_KEY" "${QWEN_API_KEY:-}"
  replace_placeholder "QWEN_MODEL" "${QWEN_MODEL:-}"

  echo "📤 Publishing config to Nacos: ${data_id}"
  RESPONSE=$(curl -s -X POST "http://${NACOS_HOST}:${NACOS_PORT}/nacos/v1/cs/configs" \
    -d "dataId=${data_id}" \
    -d "group=${GROUP}" \
    -d "tenant=${NACOS_NAMESPACE}" \
    -d "type=yaml" \
    --data-urlencode "content=${CONFIG_CONTENT}")

  if [ "$RESPONSE" = "true" ]; then
    echo "✅ Config published successfully!"
    echo "   DataId: ${data_id}"
    echo "   Group: ${GROUP}"
  else
    echo "❌ Failed to publish config: $RESPONSE"
    exit 1
  fi
}

publish_config "$CONFIG_FILE" "${DATA_ID}"

echo "✅ Nacos initialization completed!"
