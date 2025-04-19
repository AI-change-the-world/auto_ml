from ultralytics.data.dataset import YOLODataset

dataset = YOLODataset(
    img_path="/Users/guchengxi/Desktop/projects/auto_ml/frontend/dataset",
    data={"names": {0: "person"}},
    task="detect",
)
print(dataset.get_labels())
