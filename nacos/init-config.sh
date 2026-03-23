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

# 读取配置文件并替换变量
if [ -f "$CONFIG_FILE" ]; then
  CONFIG_CONTENT=$(cat "$CONFIG_FILE" | sed "s|\${ACCESS_KEY}|$ACCESS_KEY|g" | sed "s|\${SECRET_KEY}|$SECRET_KEY|g")
else
  echo "❌ Config file not found: $CONFIG_FILE"
  exit 1
fi

# 发布配置到 Nacos
echo "📤 Publishing config to Nacos..."
RESPONSE=$(curl -s -X POST "http://${NACOS_HOST}:${NACOS_PORT}/nacos/v1/cs/configs" \
  -d "dataId=${DATA_ID}" \
  -d "group=${GROUP}" \
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
