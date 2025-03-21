import json
from ultralytics import YOLO
import asyncio
from ultralytics.engine.trainer import BaseTrainer


def __train_model(log_queue: asyncio.Queue):
    def on_train_epoch_end(trainer: BaseTrainer):
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

    model = YOLO("yolo11n.pt")  # 加载 YOLO 模型
    model.add_callback("on_train_epoch_end", on_train_epoch_end)  # 监听 epoch 结束
    model.add_callback("on_train_end", lambda _: asyncio.run(log_queue.put({"status": "complete"})))
    model.train(
        data="coco8.yaml",
        epochs=3,
    )



async def train(
    model_name: str = "yolo11n.pt",
    epochs: int = 5,
    imgsz: int = 640,
    batch_size: int = 5,
):
    yield "train starting..."
    log_queue = asyncio.Queue()
    # 在新线程启动训练，防止阻塞 SSE
    import threading

    threading.Thread(
        target=__train_model,
        kwargs={
            "log_queue": log_queue,
            # "data": "coco8.yaml",
            # "epochs": 10,
            # "imgsz": 640,
            # "device": "cpu",
        },
        daemon=True
    ).start()

    # 持续读取日志，推送 SSE
    while True:
        log_entry = await log_queue.get()
        if (
            log_entry.get("status", None) is not None
            and log_entry["status"] == "complete"
        ):
            yield "[DONE]"
            break
        yield json.dumps(log_entry)
        await asyncio.sleep(0.1)
