class VRAMUsage:
    """
    用于表示显存占用估算结果的类
    """

    def __init__(
        self,
        param_memory: float,
        grad_memory: float,
        optimizer_memory: float,
        activation_memory: float,
        total_memory: float,
    ):
        """
        初始化显存占用估算结果
        参数:
            param_memory: 参数显存占用（字节）
            grad_memory: 梯度显存占用（字节）
            optimizer_memory: 优化器状态显存占用（字节）
            activation_memory: 激活值显存占用（字节）
            total_memory: 总显存占用（字节）
        """
        self.param_memory = param_memory
        self.grad_memory = grad_memory
        self.optimizer_memory = optimizer_memory
        self.activation_memory = activation_memory
        self.total_memory = total_memory

    @property
    def param_memory_mb(self):
        """返回参数显存占用（MB）"""
        return self.param_memory / 1e6

    @property
    def grad_memory_mb(self):
        """返回梯度显存占用（MB）"""
        return self.grad_memory / 1e6

    @property
    def optimizer_memory_mb(self):
        """返回优化器状态显存占用（MB）"""
        return self.optimizer_memory / 1e6

    @property
    def activation_memory_mb(self):
        """返回激活值显存占用（MB）"""
        return self.activation_memory / 1e6

    @property
    def total_memory_mb(self):
        """返回总显存占用（MB）"""
        return self.total_memory / 1e6

    def __repr__(self):
        """返回对象的字符串表示"""
        return (
            f"VRAMUsage(\n"
            f"  Parameter Memory (MB): {self.param_memory_mb:.2f},\n"
            f"  Gradient Memory (MB): {self.grad_memory_mb:.2f},\n"
            f"  Optimizer Memory (MB): {self.optimizer_memory_mb:.2f},\n"
            f"  Activation Memory (MB): {self.activation_memory_mb:.2f},\n"
            f"  Total VRAM (MB): {self.total_memory_mb:.2f}\n"
            f")"
        )
