"""
Nacos 配置中心集成
启动时从 Nacos 拉取配置，并监听热更新
"""
import asyncio
import os
import logging

from app_config import AppConfig

logger = logging.getLogger(__name__)

# Nacos 连接参数（仅这几个保留环境变量，其余全走 Nacos）
NACOS_SERVER_ADDR = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
NACOS_DATA_ID = os.getenv("NACOS_DATA_ID", "NACOS_CONFIG")
NACOS_GROUP = os.getenv("NACOS_GROUP", "NACOS_GROUP")

_nacos_service = None


async def init_nacos_config():
    """初始化 Nacos 配置（异步）"""
    global _nacos_service

    try:
        from v2.nacos import ClientConfigBuilder, ConfigParam, GRPCConfig, NacosConfigService
    except ImportError:
        logger.warning("[Nacos] nacos-sdk-python v2 未安装，跳过 Nacos 配置加载")
        return False

    try:
        client_config = (
            ClientConfigBuilder()
            .server_address(NACOS_SERVER_ADDR)
            .log_level("INFO")
            .grpc_config(GRPCConfig(grpc_timeout=5000))
            .build()
        )

        _nacos_service = await NacosConfigService.create_config_service(client_config)

        config_param = ConfigParam(data_id=NACOS_DATA_ID, group=NACOS_GROUP)
        yaml_data = await _nacos_service.get_config(config_param)

        if yaml_data:
            conf = AppConfig.get_instance()
            conf.load_from_yaml(yaml_data)
            logger.info(f"[Nacos] ✅ 配置加载成功: dataId={NACOS_DATA_ID}, group={NACOS_GROUP}")

            # 监听热更新
            asyncio.create_task(_watch_config(_nacos_service, conf, config_param))
            return True
        else:
            logger.warning("[Nacos] 配置为空，将使用环境变量回退")
            return False

    except Exception as e:
        logger.warning(f"[Nacos] 配置加载失败: {e}，将使用环境变量回退")
        return False


async def _watch_config(service, conf: AppConfig, param):
    """监听配置变化"""
    async def on_change(tenant, data_id, group, content):
        logger.info("🔥 [Nacos] 配置变更，重新加载...")
        conf.load_from_yaml(content)

    await service.add_listener(
        data_id=param.data_id, group=param.group, listener=on_change
    )


async def close_nacos_config():
    """关闭 Nacos 连接"""
    if _nacos_service:
        await _nacos_service.shutdown()
