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
: "${AI_PLATFORM_URL:=http://host.docker.internal:45679}"
: "${MODEL_TRAINER_URL:=http://model-trainer:8080}"
: "${MODEL_DEPLOY_URL:=http://model-deploy:8080}"

replace_placeholder() {
  var_name="$1"
  value="$2"
  placeholder="\${${var_name}}"
  escaped_value=$(printf '%s' "$value" | sed 's/[\/&]/\\&/g')
  CONFIG_CONTENT=$(printf '%s' "$CONFIG_CONTENT" | sed "s|${placeholder}|${escaped_value}|g")
}

# 读取配置文件并替换变量
if [ -f "$CONFIG_FILE" ]; then
  CONFIG_CONTENT=$(cat "$CONFIG_FILE")
else
  echo "❌ Config file not found: $CONFIG_FILE"
  exit 1
fi

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
replace_placeholder "AI_PLATFORM_URL" "$AI_PLATFORM_URL"
replace_placeholder "MODEL_TRAINER_URL" "$MODEL_TRAINER_URL"
replace_placeholder "MODEL_DEPLOY_URL" "$MODEL_DEPLOY_URL"

# 发布配置到 Nacos
echo "📤 Publishing config to Nacos..."
RESPONSE=$(curl -s -X POST "http://${NACOS_HOST}:${NACOS_PORT}/nacos/v1/cs/configs" \
  -d "dataId=${DATA_ID}" \
  -d "group=${GROUP}" \
  -d "tenant=${NACOS_NAMESPACE}" \
  -d "type=yaml" \
  --data-urlencode "content=${CONFIG_CONTENT}")

if [ "$RESPONSE" = "true" ]; then
  echo "✅ Config published successfully!"
  echo "   DataId: ${DATA_ID}"
  echo "   Group: ${GROUP}"
else
  echo "❌ Failed to publish config: $RESPONSE"
  exit 1
fi

echo "✅ Nacos initialization completed!"
