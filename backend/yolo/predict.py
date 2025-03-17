from ultralytics import YOLO
import asyncio

model = YOLO("yolo11n.pt")

# res = model.predict('test.jpg', stream=False)
# for r in res:
#     print(r.to_json())


async def fetch_results():
    res = model.predict(["test.jpg", "test.png"], stream=True)
    print("==" * 50)
    for item in res:
        print(item.to_json())


asyncio.run(fetch_results())
