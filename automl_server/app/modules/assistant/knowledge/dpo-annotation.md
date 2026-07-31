# DPO 偏好标注操作指南

Keywords: DPO, dpo, 偏好标注, 二选一, 多选一, 参考增强, 多轮对话, chosen, rejected, JSONL, preference

## 什么时候使用 DPO

DPO 标注用于同一个提示词下比较多个候选回复，生产 chosen/rejected 偏好数据。它不是普通 LLM 对话标注：LLM 标注是编辑对话内容，DPO 标注是判断候选回复优劣。

## 从零开始

1. 打开“数据集”，点击“新建数据集”。
2. 数据类型选择“文本”，场景选择一个 DPO 子场景：
   - “DPO 二选一”：每条样本必须有 2 条候选回复。
   - “DPO 多选一”：每条样本有 3 到 6 条候选回复，标注时选择最佳回复。
   - “DPO 参考增强”：除候选回复外必须有 `reference`，用于事实或标准答案判断。
   - “DPO 多轮对话”：`prompt.messages` 必须包含多轮上下文。
3. 进入创建后的数据集详情页，上传 `.jsonl` 文件。DPO 数据集只支持 JSONL 导入，系统会把每一行导入为一个 `preference` 样本。
4. 打开“标注”，点击“新建标注项目”，选择“偏好标注”，再选择与数据集完全匹配的 DPO 类型和数据集。
5. 打开标注项目进入 DPO 工作台。逐条选择左侧/右侧、最佳回复、平局或跳过，可填写理由标签和文本理由。
6. 点击“保存并下一条”完成标注。全部完成后点击“导出 JSONL”，导出文件可用于后续偏好训练。

## JSONL 最小格式

每行必须是一个 JSON 对象，至少包含 `item_key`、`prompt.messages` 和 `responses`。`prompt.messages` 至少要有一条 `user` 消息，`responses` 中每条必须有唯一 `response_id` 和字符串 `content`。

二选一示例：

```json
{"item_key":"case_001","prompt":{"messages":[{"role":"user","content":"解释一下勾股定理"}]},"responses":[{"response_id":"a","content":"候选回答 A"},{"response_id":"b","content":"候选回答 B"}]}
```

参考增强示例需要额外包含：

```json
{"reference":{"content":"标准答案或事实依据"},"rubric":{"focus":["正确性"],"guidance":"优先选择事实准确的回复"}}
```

## 常见校验失败

- 文件扩展名不是 `.jsonl`。
- JSONL 某一行不是合法 JSON 对象。
- `item_key` 缺失或重复。
- `prompt.messages` 为空，或没有 `user` 消息。
- 二选一不是恰好 2 条回复；多选一少于 3 条或多于 6 条。
- `response_id` 重复，回复内容为空，或两条回复内容完全相同。
- 选择的标注类型与数据集 DPO 子场景不匹配。

导入采用整批校验：文件中任意一行失败时，不会保留部分成功结果。修复错误行后重新上传即可。

## 标注结果

保存结果记录在当前 DPO 标注项目中。二选一会记录 `chosen_response_id` 和 `rejected_response_id`；多选一会记录最佳回复，导出时按 `winner_vs_all` 展开。平局和跳过不会生成有效的 chosen/rejected 训练对。
