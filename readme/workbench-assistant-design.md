# 工作台助手智能问答方案

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0 | 2026-05-09 | Codex | 基于现有 `frontend_v2 + automl_server + MQ + Nacos` 结构整理首期智能助手方案 |

## 1. 目标

本文档定义 AutoML 平台上层“工作台助手”的首期建设方案。

目标不是先做一个泛化聊天框，而是在当前平台已有能力上，增加一个 **可回答、可导航、可诊断、后续可执行操作** 的智能入口。

首期要解决的问题：

- 工作台助手从“写死规则回复”升级为真实的智能问答入口。
- 明确大模型接入位置与配置方式。
- 明确这一层支持哪些高价值场景。
- 给出与现有 `FastAPI + Nacos + 前端助手弹窗` 一致的落地路径。

首期明确不做：

- 不直接做成独立微服务。
- 不先做“万能 Agent 平台”。
- 不让模型直接连数据库或直接调用外部服务。
- 不把整个平台 API 一次性迁到 GraphQL。

## 2. 结论

推荐方案：

1. 在 `automl_server` 内新增 `assistant` 模块，作为主业务入口上的智能编排层。
2. 首期主接口采用 `REST + SSE`，不要以 `GraphQL + WebSocket` 作为主链路。
3. 大模型接入采用 **OpenAI-compatible provider adapter**，先统一适配一类协议，再按 provider 扩展。
4. 大模型配置优先放在 **Nacos / 环境变量**，前端设置页先做“查看状态 + 掩码展示”，不要一开始就在页面里直接保存明文密钥。
5. 场景分阶段推进：先做 **状态问答、页面跳转、任务诊断、流程指导**，后续再做 **需确认的执行类动作**。

核心判断：

- 你现在最缺的不是 GraphQL，而是 **清晰的助手边界、模型接入层、场景范围和流式交互链路**。
- 从当前项目现状看，`REST + SSE` 比 `GraphQL + WS` 更适合首期落地。
- Strawberry GraphQL 可以试，但更适合作为 **只读聚合查询试点**，不适合作为首期智能问答主通道。

## 3. 为什么不推荐首期以 GraphQL 为主

你提到的判断有一部分是成立的：

- FastAPI 可以集成 Strawberry GraphQL。
- Strawberry 支持 subscription，底层可以走 WebSocket。
- GraphQL 对聚合查询、强类型返回、前端按需取字段是友好的。

但它不是这个场景的首选主方案，原因更现实：

### 3.1 当前助手的核心问题不是“字段查询”，而是“编排”

工作台助手真正要做的是：

- 收到自然语言问题
- 判断问题属于哪类场景
- 拉取平台状态
- 必要时查任务、日志、部署、标注项目
- 组织上下文给模型
- 流式返回答案
- 返回可点击动作

这本质上是 **orchestration**，不是前端自己按字段拼查询。

### 3.2 你们当前系统已经有 SSE 流式模式

现有前端已经通过 `EventSource` 订阅训练任务流，后端也已经有 `task/stream` SSE 实现。

这意味着首期做问答流式返回时：

- 前端可以沿用现有技术心智
- 后端可以沿用已有流式模式
- 代理、日志、排查都更简单

没必要为了“支持流”先引入一整套 GraphQL subscription。

### 3.3 GraphQL 对聊天主链路的收益不大，复杂度却会增加

主要成本：

- 当前后端统一响应是 `Result[...]` 风格，GraphQL 会引入另一套返回语义。
- 聊天流里会有 `token_delta / tool_started / tool_result / final_message / action_suggestions` 这类事件，GraphQL schema 会变重。
- 你们当前前端 API 层是 axios + REST + SSE，若主链路改 GraphQL，前端要同时维护新的客户端栈。
- 对于聊天这类输入输出不稳定的领域，GraphQL 的 schema 优势没有管理列表场景那么明显。

### 3.4 WebSocket 认证与运维成本更高

管理后台场景下，WebSocket 链路在认证、代理、连接治理、断线恢复上都比 SSE 更重。

如果后面一定要试 GraphQL，建议：

- 只在“只读聚合查询”上试
- 不要一开始就让“工作台助手聊天主链路”走 GraphQL subscription

## 4. 推荐的系统边界

### 4.1 模块归属

推荐把智能助手先放在 `automl_server` 中，新增模块：

- `automl_server/app/modules/assistant/router.py`
- `automl_server/app/modules/assistant/schemas.py`
- `automl_server/app/modules/assistant/service.py`
- `automl_server/app/modules/assistant/providers/`
- `automl_server/app/modules/assistant/tools/`

原因：

- `automl_server` 本身就是主业务入口与编排层。
- 助手需要聚合数据集、标注、训练、部署、首页状态等能力。
- 首期把助手拆成独立服务，只会增加跨服务协议、鉴权和部署复杂度。

后续只有在以下条件明显出现时，才考虑拆服务：

- 问答流量明显高于主站普通 API
- 需要独立扩缩容
- 要接入更多异构知识源与复杂推理链
- 会出现独立的助手运营配置后台

### 4.2 运行职责

`assistant` 模块只做四件事：

1. 会话接入与流式返回
2. 平台上下文聚合
3. 模型调用编排
4. 可执行动作建议生成

不要让它承担：

- 数据集/标注/任务的原始业务实现
- 模型训练或部署能力
- 任意外部 HTTP 的无边界直连

## 5. 首期支持场景

首期不要追求“大而全”，只做高频且边界明确的场景。

### 5.1 P1 场景：状态问答

示例：

- 现在有多少数据集？
- 最近创建的标注项目是什么？
- 当前有没有运行中的训练任务？
- 现在有几个在线部署？

特点：

- 完全依赖结构化平台数据
- 不需要复杂知识库
- 能直接提升当前助手价值

### 5.2 P1 场景：页面跳转与工作台导航

示例：

- 打开最近的数据集
- 带我去部署页
- 打开任务 123
- 去 DPO 标注项目列表

输出不是只有文本，还要包含结构化动作：

- `navigate:/datasets`
- `navigate:/tasks/123`
- `navigate:/annotations/88/label`

### 5.3 P1 场景：流程指导

示例：

- 怎么开始 DPO 标注？
- 训练任务怎么创建？
- 模型部署后怎么调用推理？

这类问题不应该只靠模型自由发挥，建议优先基于平台已知流程模版或内部文档回答。

### 5.4 P2 场景：任务诊断

示例：

- 为什么这个训练任务失败了？
- 这个部署为什么不可用？
- 当前训练服务是不是挂了？

这类能力需要结合：

- 任务状态
- 最近日志
- 服务健康状态
- 常见错误规则

模型在这里更适合做 **解释和归纳**，不是直接代替系统判断。

### 5.5 P3 场景：需确认的执行类操作

示例：

- 帮我创建一个训练任务草稿
- 停掉这个部署
- 重新运行失败任务

这类动作不要在首期直接放开。

推荐方式：

- 先由助手产出结构化 action proposal
- 前端弹出确认
- 用户确认后再调用现有业务接口

## 6. 技术方案

## 6.1 接口形态

推荐主链路：

- 普通请求：REST
- 流式回答：SSE

建议接口：

- `POST /assistant/sessions`
- `POST /assistant/sessions/{session_id}/messages`
- `GET /assistant/sessions/{session_id}/stream`
- `GET /assistant/config`
- `GET /assistant/health`

也可以进一步收敛为：

- `POST /assistant/chat/stream`

但从可追踪性看，建议保留 session 概念。

### 6.2 流式事件格式

建议 SSE 事件统一结构化，不直接只吐文本：

```json
{
  "event": "message_delta",
  "data": {
    "session_id": "sess_xxx",
    "message_id": "msg_xxx",
    "delta": "当前共有"
  }
}
```

建议事件类型：

- `session_created`
- `assistant_started`
- `context_loaded`
- `tool_started`
- `tool_finished`
- `message_delta`
- `action_suggestions`
- `assistant_completed`
- `assistant_error`

这样做的好处是：

- 前端更容易显示“正在同步状态 / 正在分析任务 / 回答完成”
- 后续加入工具调用或执行确认时，不需要重写协议

### 6.3 模型接入层

推荐先做一层 provider adapter，不要在业务代码里直接写死某一家 SDK。

建议抽象：

- `AssistantProvider`
- `OpenAICompatibleProvider`
- `MockProvider`

首期先实现：

- `OpenAICompatibleProvider`

原因：

- 能兼容大部分“OpenAI 兼容接口”的模型服务
- 你后面换 OpenAI、阿里、DeepSeek、内部网关时，业务层不需要重写

能力标记建议放在 provider 配置里：

- `supports_stream`
- `supports_tool_call`
- `supports_json_mode`

### 6.4 工具调用模式

不建议让模型直接查数据库。

推荐模式：

1. 后端定义受控工具
2. 工具内部调用现有 service 层
3. 模型只拿结构化结果
4. 最终回答由后端统一落日志与封装

建议首批工具：

- `get_home_stats`
- `list_recent_datasets`
- `list_recent_annotations`
- `list_running_tasks`
- `get_task_detail`
- `get_task_logs_summary`
- `list_running_deployments`
- `get_platform_health`
- `get_workflow_guide`
- `build_navigation_target`

这里要复用现有模块能力，不要新开一套查询逻辑。

### 6.5 文档与知识源

助手回答“怎么做”这类问题时，不应只依赖模型参数知识。

首期建议知识源分两类：

1. 结构化运行时数据
2. 平台内部静态知识

静态知识可先来自：

- `readme/` 下的设计文档
- 平台内置 FAQ
- 人工整理的流程说明

但不要首期就上复杂向量数据库。

更实际的首期做法：

- 先维护少量结构化 FAQ / workflow guide
- 用关键词路由或规则选择对应知识片段
- 真正出现文档规模问题后，再引入检索

## 7. 配置设计

### 7.1 配置原则

大模型配置属于后端基础设施配置，不应该由前端直接持有明文密钥。

首期推荐：

- 配置保存在 Nacos 或环境变量
- `SettingsPage` 只显示掩码后的 provider 信息与健康状态
- 如果以后确实需要在线修改，再单独做受控的配置管理接口

### 7.2 建议配置结构

建议在 `automl_server/app/config/settings.py` 中新增 `AssistantConfig`。

配置示例：

```yaml
assistant:
  enabled: true
  default_provider: primary
  default_model: YOUR_MODEL_ID
  request_timeout_seconds: 90
  stream_keepalive_seconds: 15
  max_history_messages: 12
  max_context_chars: 24000
  allow_actions: false
  providers:
    primary:
      provider_type: openai_compatible
      base_url: https://your-llm-gateway.example.com/v1
      api_key: YOUR_SECRET
      supports_stream: true
      supports_tool_call: true
      supports_json_mode: true
```

这里故意保持扁平直接，不要提前设计多层 profile、fallback、region 路由。

### 7.3 前端设置页入口

推荐在现有 `SettingsPage` 新增一个“智能助手”分区，展示：

- 助手开关状态
- 当前 provider 名称
- 当前默认模型
- 基础地址
- 流式能力
- 工具调用能力
- 连通性检查结果

注意：

- 首期先做“查看状态”
- 不建议首期就做“前端编辑 API Key”

## 8. 会话与数据模型

如果希望后续能做历史会话、问题追踪、故障审计，建议从首期开始保留最小会话表。

建议表：

- `assistant_session`
- `assistant_message`

`assistant_session` 建议字段：

- `id`
- `source`：如 `workbench_modal`
- `page_context`
- `provider_name`
- `model_name`
- `status`
- `created_at`
- `updated_at`

`assistant_message` 建议字段：

- `id`
- `session_id`
- `role`
- `content`
- `tool_trace_json`
- `structured_actions_json`
- `latency_ms`
- `error_message`
- `created_at`

如果你想把首期做得更轻，也可以先不落库，只在前端保留临时会话。

但从平台型产品角度，我更建议至少保留最小审计能力。

## 9. 前端方案

现有 `WorkbenchAssistantModal` 已经是合适入口，但要从“本地规则问答”升级为真正的助手客户端。

### 9.1 前端交互建议

保留现有弹窗入口，但调整为三块：

1. 输入区
2. 对话区
3. 建议动作区

对话区支持显示：

- 普通文本回答
- 加载状态
- 工具执行状态
- 可点击跳转动作

不要做成花哨聊天应用，继续保持紧凑、任务导向。

### 9.2 首期前端行为

- 用户输入问题
- 创建或复用 session
- 发起流式请求
- 按 SSE 事件增量更新消息
- 如果收到 `action_suggestions`，渲染为按钮

动作示例：

- `前往数据集`
- `打开最近任务`
- `查看部署页`

### 9.3 不建议首期做的前端能力

- 不要做多标签聊天工作区
- 不要做复杂 Agent 可视化编排图
- 不要做长历史会话管理

## 10. 建议 API 草案

### 10.1 创建会话

`POST /assistant/sessions`

请求：

```json
{
  "source": "workbench_modal",
  "page_context": "/tasks"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "session_id": "sess_001"
  }
}
```

### 10.2 发送消息

`POST /assistant/sessions/{session_id}/messages`

请求：

```json
{
  "content": "现在有运行中的训练任务吗？"
}
```

响应只返回受理结果：

```json
{
  "success": true,
  "data": {
    "message_id": "msg_001",
    "stream_path": "/assistant/sessions/sess_001/stream"
  }
}
```

### 10.3 流式订阅

`GET /assistant/sessions/{session_id}/stream`

事件示例：

```json
{
  "event": "tool_finished",
  "data": {
    "tool_name": "list_running_tasks",
    "summary": {
      "running_count": 2
    }
  }
}
```

```json
{
  "event": "action_suggestions",
  "data": {
    "actions": [
      {
        "type": "navigate",
        "label": "前往训练页",
        "payload": {
          "path": "/tasks"
        }
      }
    ]
  }
}
```

## 11. 如果要试 GraphQL，建议怎么试

GraphQL 不是完全不能用，但建议限定边界。

推荐试点方式：

- 在 `assistant` 模块旁边新增一个只读 `/assistant/graphql`
- 只开放聚合查询
- 不承载首期聊天主链路

适合 GraphQL 的试点能力：

- `workspaceOverview`
- `recentDatasets`
- `recentAnnotations`
- `runningTasks`
- `runningDeployments`
- `platformHealth`

不建议首期拿 GraphQL 承载：

- token 级流式问答
- 工具调用编排
- 动作确认执行

如果后面验证下来 GraphQL 对“工作台聚合读取”确实更顺手，再考虑扩大范围。

## 12. 实施顺序

### Phase 1：把助手链路打通

- 新增 `assistant` 后端模块
- 新增 provider adapter
- 新增 `assistant` 基础配置
- 前端助手弹窗接入真实后端
- 首先支持状态问答与页面跳转

### Phase 2：补齐场景能力

- 加入流程指导知识源
- 加入任务诊断
- 加入模型健康检查与错误解释

### Phase 3：补齐治理能力

- 会话落库
- 追踪日志
- token / latency / error 指标
- provider 健康检查

### Phase 4：受控动作执行

- 生成结构化 action proposal
- 用户确认
- 调用现有业务 API

### Optional：GraphQL 只读试点

- 只做 workspace 聚合查询
- 不影响主问答链路

## 13. 最终建议

如果目标是尽快把“工作台助手”做成真正可用的智能入口，建议采用下面这条路线：

1. 助手先留在 `automl_server`，不要拆服务。
2. 主链路先走 `REST + SSE`，不要先上 `GraphQL + WS`。
3. 模型接入先做 `OpenAI-compatible` 适配层。
4. 配置先落 Nacos / 环境变量，前端设置页先做状态展示，不先做明文编辑。
5. 首期只做高价值场景：状态问答、导航、流程指导、任务诊断。
6. GraphQL 如果要试，只做只读聚合查询试点。

这条路线和你们当前项目结构最一致，改动面最可控，也最容易在短时间内做出真正可用的版本。
