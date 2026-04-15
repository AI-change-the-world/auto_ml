"""
Runtime Manager
管理模型运行时实例的启动、停止和健康检查
"""
import os
import signal
import socket
import subprocess
import time
from typing import Dict, List, Optional

from utils.config import get_deploy_config
from utils.logger import logger


class RuntimeInstance:
    """运行时实例"""

    def __init__(self, model_id: int, model_path: str, port: int, device: str = "cpu"):
        self.model_id = model_id
        self.model_path = model_path
        self.port = port
        self.device = device
        self.pid: Optional[int] = None
        self.process: Optional[subprocess.Popen] = None
        self.status = "stopped"

    def start(self) -> bool:
        """启动运行时实例"""
        try:
            # 构建启动命令
            cmd = [
                "python", "-m", "runtime.runtime_server",
                f"--model={self.model_path}",
                f"--port={self.port}",
                f"--device={self.device}",
            ]

            # 启动子进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None,
            )

            self.pid = self.process.pid
            self.status = "starting"

            # 等待服务启动
            time.sleep(2)

            # 健康检查
            if self.health_check():
                self.status = "running"
                logger.info(
                    f"Runtime instance started: model_id={self.model_id}, port={self.port}, pid={self.pid}")
                return True
            else:
                self.status = "error"
                logger.error(
                    f"Runtime instance failed health check: model_id={self.model_id}")
                self.stop()
                return False

        except Exception as e:
            self.status = "error"
            logger.error(f"Failed to start runtime instance: {e}")
            return False

    def stop(self) -> bool:
        """停止运行时实例"""
        try:
            if self.process:
                if os.name != 'nt':
                    # Unix/Linux: 发送信号到进程组
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    # Windows: 终止进程
                    self.process.terminate()

                self.process.wait(timeout=5)
                self.status = "stopped"
                logger.info(
                    f"Runtime instance stopped: model_id={self.model_id}, port={self.port}")
                return True
        except Exception as e:
            logger.error(f"Error stopping runtime instance: {e}")
            # 强制终止
            if self.process:
                self.process.kill()
            return False

    def health_check(self) -> bool:
        """健康检查"""
        try:
            import urllib.request
            req = urllib.request.Request(
                f"http://localhost:{self.port}/health", method="GET")
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False

    def is_running(self) -> bool:
        """检查进程是否仍在运行"""
        if self.process is None:
            return False
        return self.process.poll() is None


class RuntimeManager:
    """运行时管理器"""

    def __init__(self):
        # model_id -> RuntimeInstance
        self.instances: Dict[int, RuntimeInstance] = {}
        self.port_pool: List[int] = []
        self._init_port_pool()

    def _init_port_pool(self):
        """初始化端口池"""
        config = get_deploy_config()
        self.port_pool = list(
            range(config.runtime_base_port, config.runtime_max_port + 1))

    def _allocate_port(self) -> Optional[int]:
        """分配可用端口"""
        self._init_port_pool()
        for port in self.port_pool:
            if not self._is_port_in_use(port):
                return port
        return None

    def _is_port_in_use(self, port: int) -> bool:
        """检查端口是否被占用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def _release_port(self, port: int):
        """释放端口（实际不需要操作，端口在实例停止后自动释放）"""
        pass

    def deploy_model(
        self,
        model_id: int,
        model_path: str,
        device: str = "cpu"
    ) -> Optional[RuntimeInstance]:
        """
        部署模型

        Args:
            model_id: 模型ID
            model_path: 模型本地路径
            device: 运行设备 (cpu/cuda)

        Returns:
            RuntimeInstance 或 None
        """
        # 检查是否已部署
        if model_id in self.instances:
            instance = self.instances[model_id]
            if instance.is_running():
                logger.info(
                    f"Model {model_id} already deployed on port {instance.port}")
                return instance
            else:
                # 进程已停止，清理旧实例
                del self.instances[model_id]

        # 分配端口
        port = self._allocate_port()
        if not port:
            logger.error("No available port")
            return None

        # 创建并启动实例
        instance = RuntimeInstance(model_id, model_path, port, device)
        if instance.start():
            self.instances[model_id] = instance
            return instance
        else:
            return None

    def undeploy_model(self, model_id: int) -> bool:
        """
        卸载模型

        Args:
            model_id: 模型ID

        Returns:
            是否成功
        """
        if model_id not in self.instances:
            logger.warning(f"Model {model_id} not deployed")
            return False

        instance = self.instances[model_id]
        success = instance.stop()
        if success:
            del self.instances[model_id]
        return success

    def get_instance(self, model_id: int) -> Optional[RuntimeInstance]:
        """获取运行时实例"""
        return self.instances.get(model_id)

    def get_all_instances(self) -> Dict[int, RuntimeInstance]:
        """获取所有运行时实例"""
        return self.instances.copy()

    def health_check_all(self) -> Dict[int, bool]:
        """对所有实例进行健康检查"""
        results = {}
        for model_id, instance in self.instances.items():
            is_healthy = instance.health_check()
            results[model_id] = is_healthy
            if not is_healthy:
                logger.warning(f"Instance for model {model_id} is unhealthy")
        return results

    def restart_instance(self, model_id: int) -> bool:
        """重启实例"""
        if model_id not in self.instances:
            logger.warning(f"Model {model_id} not deployed")
            return False

        instance = self.instances[model_id]
        model_path = instance.model_path
        device = instance.device
        port = instance.port

        # 停止旧实例
        instance.stop()

        # 创建新实例
        new_instance = RuntimeInstance(model_id, model_path, port, device)
        if new_instance.start():
            self.instances[model_id] = new_instance
            return True
        return False


# 全局运行时管理器实例
runtime_manager = RuntimeManager()
