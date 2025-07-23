from utils.estimate_vram import estimate_vram
from utils.vram_usage import VRAMUsage


class YOLOModel:
    def __init__(self, name, num_params, layer_count, hidden_dim, input_size):
        self.name = name
        self.num_params = num_params  # 以百万 (M) 计
        self.layer_count = layer_count
        self.hidden_dim = hidden_dim
        self.input_size = input_size

    def estimate_vram(self, batch_size=1, optimizer="adam", precision="fp32"):
        v: VRAMUsage = estimate_vram(
            num_params=self.num_params,
            batch_size=batch_size,
            layer_count=self.layer_count,
            hidden_dim=self.hidden_dim,
            optimizer=optimizer,
            precision=precision,
        )
        return v.total_memory_mb
