主服务和ai_pipeline通信，现在是将图像转为 base64的，这个不好，拓展性太差了，后续要考虑传 presigned url



图像链路目前不是 presign URL。主服务在 `automl_server/app/modules/annotation/service.py:449-464` 里先从 S3 `get_file`，再转成 `base64_data` 塞进 `input.image`。runtime 其实已经支持 `ImagePayload.url`（`ai_pipeline_runtime/models.py:8`、`ai_pipeline_runtime/utils.py:36`），但这条辅助标注链路还没切到 URL 方式。


rename to `AutoML Studio`