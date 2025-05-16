package org.xiaoshuyui.automl.module.aether;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.xiaoshuyui.automl.common.PageRequest;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.common.SseResponse;
import org.xiaoshuyui.automl.module.aether.entity.Agent;
import org.xiaoshuyui.automl.module.aether.service.AgentService;
import org.xiaoshuyui.automl.module.aether.workflow.Pipeline;
import org.xiaoshuyui.automl.module.aether.workflow.PipelineParser;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowContext;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowEngine;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowStep;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.dataset.service.DatasetService;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse;
import org.xiaoshuyui.automl.module.task.entity.Task;
import org.xiaoshuyui.automl.module.task.service.TaskLogService;
import org.xiaoshuyui.automl.module.task.service.TaskService;
import org.xiaoshuyui.automl.module.tool.entity.FindSimilarObjectRequest;
import org.xiaoshuyui.automl.module.tool.entity.MultipleClassAnnotateRequest;
import org.xiaoshuyui.automl.util.SseUtil;

@RestController
@RequestMapping("/aether")
@Slf4j
public class AetherController {
  private final AetherClient aetherClient;
  private final AgentService agentService;
  private final DatasetService datasetService;
  private final TaskService taskService;
  private final AnnotationService annotationService;
  private final TaskLogService taskLogService;

  public AetherController(
      AetherClient aetherClient,
      AgentService agentService,
      DatasetService datasetService,
      TaskService taskService,
      AnnotationService annotationService,
      TaskLogService taskLogService) {
    System.out.println("✅ AetherController loaded");
    this.aetherClient = aetherClient;
    this.agentService = agentService;
    this.datasetService = datasetService;
    this.taskService = taskService;
    this.annotationService = annotationService;
    this.taskLogService = taskLogService;
  }

  @PostMapping("/agent/list")
  public Result getAgentList(@RequestBody PageRequest entity) {
    return Result.OK_data(agentService.list(entity.getPageId(), entity.getPageSize()));
  }

  @GetMapping("/agent/list/simple")
  public Result getAgentList() {
    return Result.OK_data(agentService.simpleAgentsList());
  }

  // String task, Map<String, Object> params, Long modelId, Class<R> outputClass
  @PostMapping("/auto-label")
  public Result aetherAutoLabel(@RequestBody MultipleClassAnnotateRequest request) {
    log.info("AetherController.aetherAutoLabel");
    Map<String, Object> params = new HashMap<>();
    log.info("request: {}", request);
    params.put("data", request.getImgPath());
    params.put("data_type", "image");

    Map<String, Object> extra = new HashMap<>();
    extra.put("annotation_id", request.getAnnotationId());
    params.put("extra", extra);
    var res = aetherClient.invoke("label", params, 1L, PredictSingleImageResponse.class);

    if (res == null) {
      return Result.error("invoke error");
    }

    return Result.OK_data(res);
  }

  @GetMapping("/pipeline/content/{id}")
  public Result getPipelineContent(@PathVariable Long id) {
    Agent agent = agentService.getById(id);
    if (agent == null) {
      return Result.error("agent not found");
    }
    try {
      String r = AetherPipelineConverter.convert(agent.getPipelineContent());
      return Result.OK_data(r);
    } catch (Exception e) {
      log.error("convert error: ", e);
      return Result.error("convert error");
    }
  }

  @PostMapping("workflow/auto-label/dataset")
  public Result aetherAutoLabelDatasetWorkflow(@RequestBody Map<String, Object> request) {
    log.info("request:  " + request);
    var agentId = (Integer) request.get("agentId");
    if (agentId == null) {
      return Result.error("agent not found");
    }
    Agent agent = agentService.getById((long) agentId);
    Pipeline pipeline = PipelineParser.loadFromXml(agent.getPipelineContent());
    WorkflowContext context = new WorkflowContext();
    int annotationId = (int) request.get("annotationId");
    // String imgPath = (String) request.get("imgPath");
    int datasetId = (Integer) request.getOrDefault("datasetId", -1);
    var dataset = datasetService.get((long) datasetId);

    Task taskEntity = new Task();
    taskEntity.setAnnotationId((long) annotationId);
    taskEntity.setDatasetId((long) datasetId);
    taskEntity.setTaskType(pipeline.getName());
    taskService.newTask(taskEntity);

    context.put("annotation_id", annotationId);
    context.put("taskId", taskEntity.getTaskId());
    context.put("sync", pipeline.getSync());
    context.put("agentId", agentId);
    context.put("imgPath", dataset.getLocalS3StoragePath());

    Thread thread =
        new Thread(
            () -> {
              List<WorkflowStep> steps =
                  pipeline.getSteps().stream().map((v) -> WorkflowStep.fromConfig(v)).toList();
              WorkflowEngine workflowEngine = new WorkflowEngine(steps, context);
              workflowEngine.run(1);
              taskLogService.save(taskEntity.getTaskId(), "[post task] done");
            });
    thread.start();

    return Result.OK_msg("Task Created");
  }

  @PostMapping("/workflow/auto-label")
  public Object aetherAutoLabelWorkflow(@RequestBody Map<String, Object> request) {
    log.info("request:  " + request);
    var agentId = (Integer) request.get("agentId");
    if (agentId == null) {
      return Result.error("agent not found");
    }
    var isStream = (boolean) request.getOrDefault("stream", false);
    log.info("agent id " + agentId);
    if (isStream == false) {
      try {
        switch (agentId.toString()) {
          case "1":
            return aetherAutoLabelWorkflowImpl(
                (Integer) request.get("annotationId"), (String) request.get("imgPath"), agentId);

          case "2":
            return aetherAutoLabelWorkflowImpl(
                (Integer) request.get("annotationId"), (String) request.get("imgPath"), agentId);
          case "4":
            return aetherAutoLabelWorkflowImpl(
                (Integer) request.get("annotationId"),
                (String) request.get("imgPath"),
                agentId,
                (String) request.get("label"),
                (Double) request.get("left"),
                (Double) request.get("top"),
                (Double) request.get("right"),
                (Double) request.get("bottom"));
          case "3":
            return aetherAutoLabelWorkflowImpl(
                (Integer) request.get("annotationId"),
                (String) request.get("imgPath"),
                agentId,
                (String) request.get("template_image"));
          case "5":
            return aetherAutoLabelWorkflowImpl(
                (Integer) request.get("annotationId"), (String) request.get("imgPath"), agentId);
          default:
            return Result.error("agent not found");
        }
      } catch (Exception e) {
        log.error("aetherAutoLabelWorkflow error", e);
        e.printStackTrace();
        return Result.error("get agent infomation error");
      }
    }

    SseEmitter emitter = new SseEmitter(3600 * 1000L);

    Executors.newSingleThreadExecutor()
        .execute(
            () -> {
              SseResponse sseResponse = new SseResponse();
              sseResponse.setDone(false);
              sseResponse.setStatus("Running");
              sseResponse.setMessage("Start pipeline ...");
              SseUtil.sseSend(emitter, sseResponse);

              switch (agentId.toString()) {
                case "1":
                  aetherAutoLabelWorkflowImplStream(
                      (Integer) request.get("annotationId"),
                      (String) request.get("imgPath"),
                      agentId,
                      emitter,
                      sseResponse);
                  break;

                default:
                  sseResponse.setMessage("agent not support");
                  sseResponse.setDone(true);
                  SseUtil.sseSend(emitter, sseResponse);
                  emitter.complete();
              }
            });

    return emitter;
  }

  // 非流式实现
  private Result aetherAutoLabelWorkflowImpl(int annotationId, String imgPath, int agentId) {
    var agent = agentService.getById((long) agentId);
    if (agent == null) {
      return Result.error("agent not found");
    }

    Pipeline pipeline = PipelineParser.loadFromXml(agent.getPipelineContent());
    List<WorkflowStep> steps =
        pipeline.getSteps().stream().map((v) -> WorkflowStep.fromConfig(v)).toList();
    WorkflowContext context = new WorkflowContext();
    context.put("annotation_id", annotationId);
    context.put("imgPath", imgPath);

    Task taskEntity = new Task();
    taskEntity.setTaskType(pipeline.getName());

    var dataset = datasetService.findDatasetByDataPath(imgPath);
    if (dataset != null) {
      taskEntity.setDatasetId(dataset.getId());
    }
    taskEntity.setAnnotationId((long) annotationId);
    taskService.newTask(taskEntity);

    context.put("taskId", taskEntity.getTaskId());
    context.put("sync", pipeline.getSync());

    WorkflowEngine workflowEngine = new WorkflowEngine(steps, context);
    workflowEngine.run(1);

    var res = context.get(pipeline.getOutputKey());
    log.debug("detect result: " + res);
    if (res == null) {
      return Result.error("invoke error");
    }

    return Result.OK_data(res);
  }

  // TODO : 流式实现
  private void aetherAutoLabelWorkflowImplStream(
      int annotationId, String imgPath, int agentId, SseEmitter emitter, SseResponse response) {
    var agent = agentService.getById((long) agentId);
    if (agent == null) {
      response.setMessage("agent not found");
      response.setStatus("Error");
      response.setDone(true);
      SseUtil.sseSend(emitter, response);
      emitter.complete();
      return;
    }

    Pipeline pipeline = PipelineParser.loadFromXml(agent.getPipelineContent());
    List<WorkflowStep> steps =
        pipeline.getSteps().stream().map((v) -> WorkflowStep.fromConfig(v)).toList();
    WorkflowContext context = new WorkflowContext();
    context.put("annotation_id", annotationId);
    context.put("imgPath", imgPath);
    WorkflowEngine workflowEngine = new WorkflowEngine(steps, context);
    workflowEngine.run(
        1,
        (v) -> {
          response.setData(v);
          SseUtil.sseSend(emitter, response);
        });

    var res = context.get(pipeline.getOutputKey());
    log.debug("detect result: " + res);
    if (res == null) {
      response.setMessage("invoke error");
      response.setStatus("Error");
      response.setDone(true);
      SseUtil.sseSend(emitter, response);
      emitter.complete();
      return;
    } else {
      response.setMessage("done");
      response.setStatus("Done");
      response.setDone(true);
      response.setData(res);
      SseUtil.sseSend(emitter, response);
      emitter.complete();
    }
  }

  private Result aetherAutoLabelWorkflowImpl(
      int annotationId, String imgPath, int agentId, String templateImage) {
    var agent = agentService.getById((long) agentId);
    if (agent == null) {
      return Result.error("agent not found");
    }

    Pipeline pipeline = PipelineParser.loadFromXml(agent.getPipelineContent());
    List<WorkflowStep> steps =
        pipeline.getSteps().stream().map((v) -> WorkflowStep.fromConfig(v)).toList();
    WorkflowContext context = new WorkflowContext();
    context.put("annotation_id", annotationId);
    context.put("imgPath", imgPath);
    context.put("template_image", templateImage);

    Task taskEntity = new Task();
    taskEntity.setTaskType(pipeline.getName());

    var dataset = datasetService.findDatasetByDataPath(imgPath);
    if (dataset != null) {
      taskEntity.setDatasetId(dataset.getId());
    }
    taskEntity.setAnnotationId((long) annotationId);
    taskService.newTask(taskEntity);

    context.put("taskId", taskEntity.getTaskId());
    context.put("sync", pipeline.getSync());

    WorkflowEngine workflowEngine = new WorkflowEngine(steps, context);
    workflowEngine.run(1);

    var res = context.get(pipeline.getOutputKey());
    log.debug("detect result: " + res);
    if (res == null) {
      return Result.error("invoke error");
    }

    return Result.OK_data(res);
  }

  private Result aetherAutoLabelWorkflowImpl(
      int annotationId,
      String imgPath,
      int agentId,
      String label,
      double left,
      double top,
      double right,
      double bottom) {
    var agent = agentService.getById((long) agentId);
    if (agent == null) {
      return Result.error("agent not found");
    }

    Pipeline pipeline = PipelineParser.loadFromXml(agent.getPipelineContent());
    List<WorkflowStep> steps =
        pipeline.getSteps().stream().map((v) -> WorkflowStep.fromConfig(v)).toList();
    WorkflowContext context = new WorkflowContext();
    context.put("annotation_id", annotationId);
    context.put("imgPath", imgPath);
    context.put("label", label);
    context.put("left", left);
    context.put("top", top);
    context.put("right", right);
    context.put("bottom", bottom);

    Task taskEntity = new Task();
    taskEntity.setTaskType(pipeline.getName());

    var dataset = datasetService.findDatasetByDataPath(imgPath);
    if (dataset != null) {
      taskEntity.setDatasetId(dataset.getId());
    }
    taskEntity.setAnnotationId((long) annotationId);
    taskService.newTask(taskEntity);

    context.put("taskId", taskEntity.getTaskId());
    context.put("sync", pipeline.getSync());

    WorkflowEngine workflowEngine = new WorkflowEngine(steps, context);
    workflowEngine.run(1);

    var res = context.get(pipeline.getOutputKey());
    log.debug("detect result: " + res);
    if (res == null) {
      return Result.error("invoke error");
    }

    return Result.OK_data(res);
  }

  @PostMapping("/auto-find-similar")
  @Deprecated(since = "unused")
  public Result aetherAutoFindSimilar(@RequestBody FindSimilarObjectRequest request) {
    log.info("AetherController.aetherAutoLabel");
    Map<String, Object> params = new HashMap<>();
    log.info("request: {}", request);
    params.put("data", request.getPath());
    params.put("data_type", "image");

    Map<String, Object> extra = new HashMap<>();
    extra.put("annotation_id", request.getId());
    extra.put("label", request.getLabel());
    extra.put("left", request.getLeft());
    extra.put("top", request.getTop());
    extra.put("right", request.getRight());
    extra.put("bottom", request.getBottom());
    params.put("extra", extra);

    var res = aetherClient.invoke("find similar", params, 1L, PredictSingleImageResponse.class);

    if (res == null) {
      return Result.error("invoke error");
    }

    return Result.OK_data(res);
  }
}
