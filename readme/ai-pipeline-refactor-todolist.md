# AI Pipeline 重构未完成 TODO

| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| v1.0 | 2026-05-17 | Codex | 基于当前仓库实际落地状态整理 `ai_pipeline` / `ai_pipeline_runtime` 重构剩余事项 |

## 1. 当前状态总结

当前这轮改造已经完成的核心骨架有：

- 已新增 `ai_pipeline_*` 数据库表与 `annotation.default_ai_pipeline_binding_id`
- 已新增主服务 `automl_server/app/modules/ai_pipeline/` 管理模块
- 已支持模板、模板版本、binding、模型资源目录的基础查询与创建/更新
- 已把 annotation 辅助标注链路接到 `default_ai_pipeline_binding_id`
- 已支持 DB template inline definition 下发到运行时服务执行
- 已增加 ONNX 模型资源绑定与 `onnx_detect` capability
- 已完成子服务目录与服务名重命名：`auto_augment_pipeline -> ai_pipeline_runtime`
- 已补最小前端入口：
  - 标注项目列表页入口
  - 标注工作台工具栏入口
  - 项目级 AI Pipeline 配置页

但目前整体仍处于：

- 管理面已初步可用
- 执行面仍以旧 MQ 同步调用链路兼容运行
- 前端仍是“最小可看版本”，不是最终 schema 驱动版本
- 数据库里 `run / step / artifact / event_log` 相关表还没有真正用起来

所以，这次重构还不能算“完成”，只能算：

- **骨架已成**
- **图片辅助标注单场景已接通**
- **平台级 AI Pipeline 执行层仍未完整闭环**

---

## 2. 已完成项

以下事项当前可以视为已完成：

- [x] `ai_pipeline_*` 表结构草案与初始化脚本已落地
- [x] `AiPipelineTemplate / Version / Binding / Run / RunStep / Artifact / EventLog` ORM 已新增
- [x] `annotation.default_ai_pipeline_binding_id` 已接入后端与前端类型
- [x] `automl_server` 已新增 `ai_pipeline` 管理模块与路由注册
- [x] `GET/POST/PUT /ai-pipeline/bindings` 已实现
- [x] `GET/POST /ai-pipeline/templates` 与版本创建已实现
- [x] `GET /ai-pipeline/resources/models` 已实现
- [x] annotation 辅助标注已优先支持 binding 驱动
- [x] 运行时服务支持 inline `definition`
- [x] 已新增 ONNX 模型 capability：`onnx_detect`
- [x] 已有模板导入脚本：`scripts/import_ai_pipeline_templates.py`
- [x] 子服务已重命名为 `ai_pipeline_runtime`
- [x] docker-compose / Nacos / README 基本路径已同步
- [x] 前端已新增项目级 AI Pipeline 配置页

---

## 3. 未完成项总览

以下是当前真正还没做完的部分，按优先级拆分。

---

## 4. P0：必须先补完的闭环项

这些不补，整体仍然只是“半重构”。

### 4.1 管理面接口仍不完整

- [ ] 增加模板发布接口
  - 例如：`POST /ai-pipeline/templates/{template_key}/publish`
- [ ] 增加模板禁用接口
  - 例如：`POST /ai-pipeline/templates/{template_key}/disable`
- [ ] 增加 binding 删除接口
  - 例如：`DELETE /ai-pipeline/bindings/{binding_id}`
- [ ] 增加模板版本详情/列表接口
  - 当前只有模板详情，版本管理能力不完整

验收标准：

- 前端可以完整完成模板生命周期管理，而不是只能创建和更新

### 4.2 前端仍是写死表单，不是 schema 驱动

- [ ] 读取模板 `form_schema_json`
- [ ] 实现字段渲染器注册表
- [ ] 支持最小通用字段集：
  - `text`
  - `textarea`
  - `number`
  - `switch`
  - `select`
  - `resource-select`
- [ ] 当前页面中硬编码字段：
  - `prompt`
  - `score_threshold`
  - `detector_model_id`
  需要替换成 schema 渲染

验收标准：

- 新模板接入时，前端不需要再手写一个新表单页面

### 4.3 模板导入只是脚本级能力，缺少正式迁移策略

- [ ] 明确部署时模板导入策略
  - 是启动前手工执行
  - 还是后台管理手工导入
  - 还是初始化阶段自动导入内置模板
- [ ] 处理旧 Nacos pipeline 到 DB 模板的一次性迁移规范
- [ ] 增加导入幂等说明与回滚说明

验收标准：

- 新环境初始化后，不依赖人工猜测如何把旧模板导入数据库

### 4.4 旧数据兼容还没真正迁移完成

- [ ] 编写 `annotation.assist_pipeline -> default_ai_pipeline_binding_id` 迁移策略
- [ ] 补一份旧标注项目 binding 自动生成脚本或后台工具
- [ ] 明确老项目在未绑定时的兼容行为何时下线

验收标准：

- 平台里的旧标注项目能逐步迁到 binding 模型，而不是长期双轨并存

---

## 5. P1：执行面必须补完的工程项

### 5.1 仍然没有真正切到“短任务 HTTP 同步执行”

当前状态：

- annotation 辅助标注仍主要走 MQ RPC request-reply
- 只是 template 来源从 DB 优先，执行载体还是旧模式

需要补：

- [ ] `ai_pipeline_runtime` 提供正式同步执行接口
  - 建议：`POST /v1/pipeline-runs/sync`
- [ ] `automl_server` 改为 HTTP 调用短任务同步执行
- [ ] MQ request-reply 从主链路退为兼容/兜底

验收标准：

- 单图辅助标注不再依赖同步 MQ RPC 作为主执行路径

### 5.2 `ai_pipeline_run` 相关表完全未启用

当前状态：

- 表结构和 ORM 都有了
- 但没有真正创建 run、step、artifact、event log

需要补：

- [ ] 新增 run service
- [ ] 每次执行创建 `ai_pipeline_run`
- [ ] 每个 step 写 `ai_pipeline_run_step`
- [ ] 中间产物/结果产物写 `ai_pipeline_artifact`
- [ ] 事件写 `ai_pipeline_event_log`

验收标准：

- 平台能查询到一次 pipeline 执行的运行记录，而不是只拿即时返回结果

### 5.3 运行时服务仍未接入数据库模板管理

当前状态：

- `ai_pipeline_runtime` 可以执行 inline definition
- 但它自己不管理 DB 模板查询，也没有 run 概念

需要补：

- [ ] 明确 runtime 是否直接读 DB
  - 当前推荐仍然是不直接读主业务表
- [ ] 如果不直读 DB，则要补“执行请求标准协议”
- [ ] 让 runtime 基于统一 request 执行，而不是继续围绕旧 `run_pipeline` MQ payload

验收标准：

- runtime 的输入协议清晰稳定，不再依赖旧 `pipeline_name + request` 兼容格式

### 5.4 资源抽象还不完整

当前已完成：

- [x] ONNX 模型资源目录

未完成：

- [ ] provider 资源目录抽象
- [ ] OCR / 规则执行器是否资源化的边界定义
- [ ] 按 slot filter 精细过滤资源
  - 如 `model_type`
  - `runtime_template`
  - `deployed_only`
  - `scene_type`

验收标准：

- 模板声明的资源槽位都能从统一 API 获取可选项

---

## 6. P1：前端产品面未完成项

### 6.1 当前项目级配置页还只是最小版

需要补：

- [ ] binding 删除能力
- [ ] binding 复制能力
- [ ] 默认 binding 快速切换
- [ ] 当前默认值与项目 prompt 的差异展示
- [ ] 资源摘要展示优化

### 6.2 缺少平台级模板管理页

需要补：

- [ ] 新增模板列表页
- [ ] 模板详情页
- [ ] 版本管理页
- [ ] 发布/禁用操作页

推荐入口：

- `Settings -> AI Pipeline 模板`

### 6.3 工作台里的入口还不够完整

当前状态：

- Toolbar 里已经能快速切换 binding
- 也有跳转配置页按钮

未完成：

- [ ] 根据当前选中 binding 展示资源摘要
- [ ] 显示当前 binding 的模板名/版本
- [ ] 显示“此 binding 与当前 shape/type 不兼容”的提示

### 6.4 缺少资源选择器的通用组件

需要补：

- [ ] `resource-select` 组件
- [ ] 支持按资源类型统一拉取
- [ ] 支持 slot 过滤条件
- [ ] 支持显示已部署状态、设备、模板等辅助信息

---

## 7. P2：为视频/批量能力准备的未完成项

### 7.1 输入模型仍然偏图片特化

当前状态：

- `TaskPayload` 仍主要围绕：
  - `image`
  - `overlay_image`
  - `classes`
  - `prompt`

需要补：

- [ ] 引入 `data_inputs / runtime_inputs / resource_bindings` 标准执行请求结构
- [ ] 设计 `video` 输入 schema
- [ ] 设计 `content_items` 或等价的多模态输入模型

### 7.2 异步 run 模型尚未落地

需要补：

- [ ] `POST /v1/pipeline-runs`
- [ ] `GET /v1/pipeline-runs/{run_id}`
- [ ] `GET /v1/pipeline-runs/{run_id}/steps`
- [ ] `GET /v1/pipeline-runs/{run_id}/artifacts`
- [ ] `POST /v1/pipeline-runs/{run_id}/cancel`

### 7.3 视频 pipeline 首期支撑能力未开始

需要补：

- [ ] 视频资源输入
- [ ] 帧采样器
- [ ] 帧级 step 执行模型
- [ ] 时序聚合
- [ ] 视频 artifact 输出

---

## 8. P2：配置中心与旧链路清理项

### 8.1 仍保留了较多旧兼容配置

当前状态：

- 保留了旧环境变量兼容：
  - `AUTO_AUGMENT_PIPELINE_URL`
- 保留了旧 Nacos key fallback：
  - `auto-augment-pipeline`

这些是合理的短期兼容，但后续要清理。

需要补：

- [ ] 设定兼容期截止版本
- [ ] 新旧变量切换说明
- [ ] 最终移除旧 key fallback

### 8.2 Nacos 里仍有业务模板残留兼容逻辑

当前状态：

- annotation 服务仍可能 fallback 到运行时 `list_pipelines`

需要补：

- [ ] 彻底移除 Nacos/旧 runtime pipeline catalog 作为业务模板来源
- [ ] 仅保留数据库模板目录

验收标准：

- 平台模板目录完全 DB-first，且不再需要从运行时扫描旧模板

---

## 9. 测试与验证未完成项

这部分当前明显缺口最大。

### 9.1 后端测试

- [ ] `ai_pipeline` 模块 CRUD/service 单测
- [ ] annotation 与 binding 联动测试
- [ ] ONNX resource binding 解析测试
- [ ] DB template inline execution 测试
- [ ] 旧字段兼容测试

### 9.2 前端测试 / 页面验证

- [ ] AI Pipeline 配置页基本交互验证
- [ ] 标注列表入口验证
- [ ] Toolbar 快捷入口验证
- [ ] 创建 / 编辑 / 默认切换 smoke test

### 9.3 部署链路验证

- [ ] `docker-compose up` 下验证 `ai_pipeline_runtime` 新名字可正常启动
- [ ] Nacos 初始化后新 data id 可正常发布
- [ ] 主服务能连通 `ai_pipeline_runtime`
- [ ] ONNX 资源调用端到端验证

---

## 10. 文档与运维未完成项

### 10.1 文档还没完全跟上代码现状

当前状态：

- 已新增多份设计文档
- 但部分历史文档仍引用旧名或旧阶段目标

需要补：

- [ ] 统一整理 `readme/` 下设计文档状态
- [ ] 标明哪些文档是历史方案，哪些是当前方案
- [ ] 补一份“部署与迁移说明”

### 10.2 缺少运维侧操作文档

需要补：

- [ ] 新环境初始化顺序
- [ ] 模板导入顺序
- [ ] 旧项目迁移顺序
- [ ] 出问题时的回滚路径

---

## 11. 推荐执行顺序

建议下一阶段按下面顺序推进，而不是并行乱改。

### Step 1：先把管理面补完整

- [ ] 模板 publish / disable / delete
- [ ] binding delete
- [ ] 平台级模板管理页

### Step 2：把前端改成 schema 驱动

- [ ] `form_schema_json` 读取
- [ ] 动态字段渲染器
- [ ] 通用 `resource-select`

### Step 3：切换短任务执行主链路

- [ ] HTTP 同步执行接口
- [ ] annotation assist 改成 HTTP 主调
- [ ] MQ request-reply 降级为兼容

### Step 4：启用 run / step / artifact / event_log

- [ ] run service
- [ ] 事件与产物落库
- [ ] 查询接口

### Step 5：再进入视频与批量阶段

- [ ] async run
- [ ] video input schema
- [ ] batch / video UI

---

## 12. 最终完成标准

只有下面这些都满足，才能认为这次重构真正完成：

- [ ] 平台模板目录完全数据库化
- [ ] 前端配置页完全 schema 驱动
- [ ] 单图辅助标注主链路不再依赖同步 MQ RPC
- [ ] `ai_pipeline_run / step / artifact / event_log` 真正投入使用
- [ ] binding 成为项目默认 AI 配置的唯一主模型
- [ ] 模型资源选择不再写死字段
- [ ] 视频 / batch 有明确异步 run 模型和接口骨架
- [ ] 旧 `auto_augment_pipeline` 兼容入口进入明确下线周期

---

## 13. 一句话结论

当前这次改造的真实进度是：

- **数据库骨架：已完成**
- **管理面基础接口：已完成**
- **前端最小入口：已完成**
- **短任务执行架构升级：未完成**
- **run 持久化体系：未完成**
- **schema 驱动前端：未完成**
- **视频/异步 run：未开始**

如果按工程优先级排序，下一步最该做的是：

1. **补完整管理面接口**
2. **把前端改成 schema 驱动**
3. **把同步执行从 MQ 切到 HTTP**
4. **正式启用 run/step/artifact/event_log**
