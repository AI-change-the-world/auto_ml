import json
import queue
import threading

from ultralytics import YOLO
from ultralytics.models.yolo.detect.train import DetectionTrainer

log_queue = queue.Queue()


# ---- 新增关键回调函数 ----
def on_train_batch_end(trainer: DetectionTrainer):
    """每个batch结束时触发"""
    metrics = trainer.metrics
    log_data = {
        "type": "batch",
        "epoch": trainer.epoch,
        "loss": str(trainer.loss),
        "tloss": str(trainer.tloss),
        "lr": trainer.optimizer.param_groups[0]["lr"],  # 获取学习率
    }
    log_queue.put(log_data)


def on_train_epoch_end(trainer: DetectionTrainer):
    """每个epoch结束时触发"""
    log_queue.put(
        {
            "type": "epoch",
            "epoch": trainer.epoch,
            # 'loss': trainer.loss,
            "loss": str(trainer.loss),
            "tloss": str(trainer.tloss),
            "mAP": trainer.metrics.get("mAP50-95", 0.0),
        }
    )


# ---- 训练函数 ----
def train_model():
    model = YOLO("yolov8n.pt")
    model.add_callback("on_train_batch_end", on_train_batch_end)  # 手动添加回调
    model.add_callback("on_train_epoch_end", on_train_epoch_end)

    model.train(
        data="coco8.yaml",
        epochs=3,
        batch=16,  # 显式设置batch大小
        # 注意：不要在这里使用callbacks参数，改用add_callback
    )
    log_queue.put({"status": "complete"})


def generate():
    while True:
        log = log_queue.get()
        print(f"data: {json.dumps(log)}\n\n")

        if log.get("status", None) is not None and log["status"] == "complete":
            break


def start_train():
    thread = threading.Thread(target=train_model, daemon=True)
    thread.start()
    return {"status": "training started"}


if __name__ == "__main__":
    start_train()
    generate()
