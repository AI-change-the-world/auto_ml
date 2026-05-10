# DPO 偏好标注功能设计文档

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.1 | 2026-05-06 | Codex | 基于现有 `dataset / annotation / sample_item / annotation_record` 体系重写，收敛首期实现范围 |

## 1. 目标与范围

本文档定义 AutoML 控制台中 **DPO 偏好标注** 的首期设计方案。

目标不是单独做一套新的“偏好平台”，而是在当前项目已有能力上增量支持：

- 数据集侧继续复用现有 `dataset + sample_item` 结构。
- 标注侧继续复用现有 `annotation + annotation_record` 结构。
- 前端新增一个独立的 DPO 标注工作台，不与现有图像标注页、LLM 对话标注页强行混合。
- 导出结果优先服务于后续偏好训练数据生产，不在首期直接实现完整 DPO 训练链路。

首期解决的问题：

- 能创建 DPO 数据集。
- 能基于同一 prompt 的多个候选回复进行人工偏好标注。
- 能保存结构化偏好结果。
- 能导出标准 `prompt / chosen / rejected` 训练数据。

首期明确不做：

- 不做复杂的多人协作分单系统。
- 不做完整审核流、绩效系统、金标准平台。
- 不做多模型在线生成候选回复。
- 不做排序、多维评分、主动学习等高阶能力。
- 不在首期直接改 `model_trainer` 支持 DPO 训练。

## 2. 为什么这样设计

当前项目已经有几条明确边界：

- 数据集的最小业务单元是 `sample_item`。
- 结构化标注结果通过 `annotation_record` 挂在 `sample_item` 上。
- LLM/MLLM 标注已经证明“文本/对话类数据集 + 独立工作台”的模式可行。
- 微服务职责已经分开，主站负责业务编排，训练服务负责训练执行。

因此 DPO 功能应沿用这条路径，而不是重新设计新的任务域模型。

## 3. 首期产品形态

首期产品拆成三个部分：

1. DPO 数据集
2. DPO 标注项目
3. DPO 导出

用户路径：

1. 创建文本型 DPO 数据集。
2. 导入结构化偏好样本。
3. 创建 DPO 标注项目并绑定该数据集。
4. 在 DPO 工作台中逐条判断 `chosen / rejected`。
5. 导出高质量偏好结果，供后续训练使用。

## 4. 与现有系统的映射

### 4.1 数据集侧

复用现有模型：

- `dataset`
- `sample_item`
- `asset`

需要新增的是 **DPO 场景类型**，而不是新增一套独立表。

建议扩展：

- `DatasetScenarioType.DPO_PREFERENCE = 4`

首期限制：

- `data_type = text`
- `scenario_type = dpo_preference`

不支持图文混合 DPO，不支持音视频 DPO。

### 4.2 标注侧

复用现有模型：

- `annotation`
- `annotation_record`

建议扩展：

- `AnnotationType.DPO = 6`

原因：

- DPO 工作台和现有 `LLM` 对话标注不是一回事。
- `LLM` 标注是“编辑/补全对话内容”，DPO 是“在多个候选回复中做偏好判断”。
- 单独的 annotation type 可以保证路由、校验、存储格式、导出逻辑更清晰。

### 4.3 前端页面

不建议把 DPO 功能塞进现有 `ConversationAnnotationPage`。

建议新增独立页面：

- `frontend_v2/src/pages/annotation/dpo/DpoAnnotationPage.tsx`

并在 `AnnotationWorkbenchRouter` 中单独路由到：

- `/annotations/:annotationId/label/dpo`

原因：

- 工作流明显不同。
- 页面结构不同。
- 保存内容结构不同。
- 强行复用会让现有 LLM/MLLM 标注页变得混乱。

## 5. 数据模型设计

## 5.1 DPO 数据集样本模型

首期每个 `sample_item` 表示一条待偏好判断的样本，`item_type` 固定为：

- `preference`

`sample_item.payload` 存储结构化内容。

推荐结构：

```json
{
  "version": 2,
  "task_type": "pairwise",
  "prompt": {
    "system_prompt": "你是一个有帮助的助手",
    "messages": [
      { "role": "user", "content": "解释一下勾股定理" }
    ]
  },
  "responses": [
    {
      "response_id": "resp_a",
      "content": "勾股定理是指……",
      "model_id": "qwen2.5-7b",
      "metadata": {
        "temperature": 0.7
      }
    },
    {
      "response_id": "resp_b",
      "content": "在直角三角形中……",
      "model_id": "deepseek-7b",
      "metadata": {
        "temperature": 0.7
      }
    }
  ],
  "reference": {
    "content": "若三角形为直角三角形，则两直角边平方和等于斜边平方"
  },
  "rubric": {
    "focus": ["正确性", "完整性"],
    "guidance": "优先选择事实准确且表达完整的回复"
  },
  "tags": ["math", "zh"]
}
```

字段约束：

- `prompt.messages` 至少包含一条 `user` 消息。
- `task_type`
  - `pairwise`
  - `best_of_n`
- `responses.length` 标准范围为 `2` 到 `6``。
- `response_id` 在当前 sample 内唯一。
- 所有 `response.content` 不能同时为空。
- 任意两个 `response.content` 完全一致时，默认视为无效样本，不进入标注。
- `reference` 可选，仅用于辅助判断，不参与训练导出。
- `rubric` 可选，仅用于辅助判断，不参与训练导出。

### 5.2 为什么首期只支持二元比较

原初稿里有 `N 选 1`、排序、多维评分，这些设计本身没问题，但不能各自长成完全不同的数据集格式。

原因：

- 首期目标是最短路径产出 DPO 训练数据。
- DPO 训练的核心格式本来就是 `chosen / rejected`。
- 当前已经有明确的 `N 选 1` 业务需求，如果底层样本模型只允许两条回复，后续扩展会比较被动。
- 更稳的做法是数据集标准格式统一放宽到 2 到 6 个候选，但导出仍然收敛为训练可消费的 pairwise 结果。

因此标准 DPO 数据集统一为：

- 一条 prompt
- 2 到 6 条候选 response
- 一个 `task_type`
- 一个最终可回收为 `chosen / rejected` 的偏好结果

首轮前端支持：

- `pairwise`
- `best_of_n`

对 `best_of_n` 样本，导出策略建议统一为：

- `winner_vs_all`

即标注员选出一个最佳回复后，导出为多条训练样本：

- `winner vs response_2`
- `winner vs response_3`
- ...

## 5.3 标注结果模型

复用 `annotation_record.content` 存储 JSON。

推荐结构：

```json
{
  "version": 1,
  "format": "dpo_preference",
  "sample_item_id": 101,
  "decision": "left",
  "chosen_response_id": "resp_a",
  "rejected_response_id": "resp_b",
  "tie": false,
  "skip": false,
  "reason": "A 更准确，且表达更完整",
  "reason_tags": ["more_correct", "more_complete"],
  "display_order": ["resp_a", "resp_b"],
  "duration_ms": 12340,
  "annotated_at": "2026-05-06T15:10:00+08:00"
}
```

字段说明：

- `decision`
  - `left`
  - `right`
  - `tie`
  - `skip`
- `chosen_response_id`
  - `decision = left/right` 时必填
- `rejected_response_id`
  - `decision = left/right` 时必填
- `tie`
  - 是否判定平局
- `skip`
  - 是否跳过
- `display_order`
  - 前端真实展示顺序，必须保存，用于消除左右位置偏差
- `duration_ms`
  - 从进入该样本到提交的耗时

首期建议：

- 允许 `tie`
- 允许 `skip`
- `reason` 选填
- `reason_tags` 选填

## 6. 数据集导入设计

## 6.1 导入方式

首期建议支持两种导入方式：

1. 上传 JSONL 文件后由后端解析入库
2. 手动通过样本接口创建 `preference` 类型样本

其中真正面向用户的主路径是 JSONL 导入。

### 6.2 JSONL 格式

每行一条样本：

```json
{
  "item_key": "case_0001",
  "prompt": {
    "system_prompt": "你是一个助手",
    "messages": [
      { "role": "user", "content": "写一个排序算法示例" }
    ]
  },
  "responses": [
    { "response_id": "resp_a", "content": "这是回答 A", "model_id": "model_a" },
    { "response_id": "resp_b", "content": "这是回答 B", "model_id": "model_b" }
  ],
  "reference": {
    "content": "可选参考答案"
  },
  "tags": ["coding"]
}
```

导入后落库逻辑：

- 创建 `sample_item`
- `item_type = preference`
- `item_key = item_key`
- `payload = 整行结构化 JSON`

### 6.3 导入校验

后端需要做最小必要校验：

- `item_key` 非空且在当前数据集中唯一
- `prompt.messages` 合法
- `responses` 恰好 2 条
- 每条 `response_id` 非空
- 每条 `response.content` 为字符串
- 两条回复不能完全相同

校验失败策略：

- 返回错误摘要
- 标明失败行号
- 不做半成功导入

首期不做复杂字段映射 UI。

## 7. 标注项目设计

## 7.1 项目创建约束

创建 DPO 标注项目时：

- `annotation_type = DPO`
- 必须绑定 DPO 数据集

后端校验规则建议与现有 `LLM / MLLM` 一致，放在 `AnnotationService._validate_annotation_dataset_link` 中统一处理。

新增约束：

- `dataset.data_type == text`
- `dataset.scenario_type == dpo_preference`

## 7.2 项目配置

首期项目配置不做复杂模板系统，只保留少量必要字段：

- `name`
- `dataset_id`
- `prompt`
  - 可选，作为标注说明或判定原则

如果后续需要更细配置，再增量扩展为结构化 `annotation_config`，首期不建议提前设计。

## 8. DPO 标注工作台设计

## 8.1 页面目标

页面要解决的是高效做二选一偏好判断，不是展示复杂分析图表。

布局原则：

- 左侧样本列表
- 右侧当前样本工作区
- 顶部只保留必要状态与保存操作
- 不堆解释文本

### 8.2 页面结构

建议结构：

1. 左侧样本列表
2. 中间 prompt 区
3. 下方双栏 response 对比区
4. 底部操作区

工作区内容：

- Prompt 展示
  - system prompt 折叠显示
  - 多轮消息按对话形式展示
- Response A / B
  - 文本按 Markdown 只读渲染
  - 默认掩码显示为 `回答 A`、`回答 B`
  - 不默认暴露模型名
- 操作区
  - `选择左侧`
  - `选择右侧`
  - `平局`
  - `跳过`
  - `保存并下一条`
  - 理由标签
  - 可选文本理由

### 8.3 交互要求

首期必须支持：

- 左右 response 随机交换显示顺序
- 自动恢复该样本已保存记录
- 保存当前记录
- 跳转上一条/下一条
- 未保存变更提示

快捷键建议首期直接支持：

- `A` 选择左侧
- `D` 选择右侧
- `S` 跳过
- `W` 平局
- `Ctrl+Enter` 保存

### 8.4 状态展示

左侧列表建议展示：

- `item_key`
- 是否已保存
- 当前决策摘要

不建议首期做：

- 多层筛选器
- 多人协作状态
- 复杂批量操作

## 9. 存储与接口设计

## 9.1 复用现有接口

优先复用已有接口：

- `GET /dataset/{id}/samples`
- `POST /dataset/{id}/samples`
- `GET /annotation/{id}`
- `GET /annotation/{id}/records`
- `POST /annotation/{id}/record`

如果现有接口路径命名略有差异，以现有 annotation 模块实际 router 为准，原则是不新起一套 DPO 专属保存接口。

### 9.2 需要新增的内容

后端新增点主要有：

- `DatasetScenarioType.DPO_PREFERENCE`
- `AnnotationType.DPO`
- DPO 数据集导入能力
- DPO annotation record 的解析/序列化
- DPO 导出接口

### 9.3 annotation_record 文件格式

因为 DPO 属于结构化文本标注，建议沿用 JSON 文件。

需要扩展：

- `annotation_record_storage.py`

让 `AnnotationType.DPO` 也走 `.json` 序列化路径。

## 10. 导出设计

## 10.1 首期导出目标

首期只做一种核心导出格式：

```json
{
  "prompt": {
    "system_prompt": "你是一个助手",
    "messages": [
      { "role": "user", "content": "解释一下勾股定理" }
    ]
  },
  "chosen": "在直角三角形中……",
  "rejected": "勾股定理是……",
  "chosen_response_id": "resp_b",
  "rejected_response_id": "resp_a",
  "sample_item_id": 101,
  "annotation_id": 12,
  "reason": "B 更准确"
}
```

导出规则：

- 仅导出 `decision = left/right`
- `tie = true` 的样本不导出
- `skip = true` 的样本不导出
- 能根据 `display_order` 还原真实 chosen/rejected

导出文件格式建议：

- JSONL

### 10.2 导出入口

建议在 DPO 标注项目详情页或列表页提供：

- `导出 DPO 数据`

首期不直接投递到 `model_trainer`。

原因：

- 当前 `model_trainer` 主要承载检测/分类/分割任务。
- DPO 训练链路与现有 trainer 差异较大。
- 先把高质量偏好数据生产闭环做通，再决定训练服务如何接入。

## 11. 质量控制设计

原初稿里的质控方向是对的，但首期要收敛。

首期建议只实现轻量质控：

- 重复样本拦截
- 相同 response 拦截
- 保存耗时记录
- 可选理由标签
- 后台导出时过滤 `skip / tie`

首期暂不做：

- Fleiss' Kappa
- 多标注员一致性计算
- 金标准自动封禁
- 绩效仪表盘

这些能力以后可在同一数据模型上继续加，不影响首期结构。

## 12. 对现有代码的影响

## 12.1 automl_server

需要改动的方向：

- `app/common/constants.py`
  - 新增 `DatasetScenarioType.DPO_PREFERENCE`
  - 新增 `AnnotationType.DPO`
- `app/modules/dataset/service.py`
  - 允许文本数据集创建 DPO 场景
  - 增加 DPO 样本导入逻辑
- `app/modules/annotation/service.py`
  - 增加 DPO 数据集绑定校验
- `app/utils/annotation_record_storage.py`
  - 增加 DPO JSON 读写支持
- 新增导出 service / router
  - 从 annotation project 导出 DPO JSONL

### 12.2 frontend_v2

需要改动的方向：

- `src/types/dataset.ts`
  - 新增 `DatasetScenarioType.DPOPreference`
- `src/types/annotation.ts`
  - 新增 `AnnotationType.DPO`
- `src/pages/annotation/AnnotationListPage.tsx`
  - 创建项目时支持 DPO 类型及数据集过滤
- `src/pages/annotation/AnnotationWorkbenchRouter.tsx`
  - 路由到 `dpo`
- 新增 `src/pages/annotation/dpo/*`
  - DPO 工作台页面与子组件
- 数据集页面
  - 需要有 DPO 数据集创建入口和样本导入入口

## 13. 分阶段实现建议

### Phase 1：打通最小闭环

- 新增 DPO dataset scenario
- 新增 DPO annotation type
- 支持创建 `preference` 样本
- 新增 DPO 工作台
- 支持保存偏好结果
- 支持导出 JSONL

验收标准：

- 可以从 0 创建 DPO 数据集和标注项目
- 可以完成一批二元偏好标注
- 可以导出训练数据

### Phase 2：补强可用性

- JSONL 文件导入 UI
- 理由标签配置
- 批量浏览和筛选
- 标注进度显示

### Phase 3：高级能力

- 多人复标
- 一致性统计
- 金标准
- N 选 1 / 排序 / 多维评分
- 与训练链路打通

## 14. 关键设计结论

这版 DPO 设计保留了初稿里几个正确方向：

- 用结构化样本承载 prompt + responses
- 用统一结果格式承载偏好结论
- 导出时对齐 `chosen / rejected`
- 后续可扩展理由标签和质控

同时做了几个必要收敛：

- 首期只做文本 DPO
- 首期只做二元偏好
- 不新起独立任务系统
- 直接复用现有 `sample_item` 和 `annotation_record`
- 单独做 DPO 工作台，不污染现有 LLM/MLLM 页面
- 先打通数据生产闭环，不急着绑定训练服务

这条路径更符合当前项目结构，也更适合分阶段落地。
