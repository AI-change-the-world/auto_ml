package org.xiaoshuyui.automl.module.aether;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.xiaoshuyui.automl.common.PageRequest;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.aether.service.AgentService;
import org.xiaoshuyui.automl.module.aether.workflow.Pipeline;
import org.xiaoshuyui.automl.module.aether.workflow.PipelineParser;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowContext;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowEngine;
import org.xiaoshuyui.automl.module.aether.workflow.WorkflowStep;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse;
import org.xiaoshuyui.automl.module.tool.entity.FindSimilarObjectRequest;
import org.xiaoshuyui.automl.module.tool.entity.MultipleClassAnnotateRequest;

@RestController
@RequestMapping("/aether")
@Slf4j
public class AetherController {
    private final AetherClient aetherClient;
    private final AgentService agentService;

    public AetherController(AetherClient aetherClient, AgentService agentService) {
        System.out.println("✅ AetherController loaded");
        this.aetherClient = aetherClient;
        this.agentService = agentService;
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

    @PostMapping("/workflow/auto-label")
    public Result aetherAutoLabelWorkflow(@RequestBody Map<String, Object> request) {
        var agentId = (Integer) request.get("agentId");
        if (agentId == null) {
            return Result.error("agent not found");
        }
        log.info("agent id " + agentId);
        try {
            switch (agentId.toString()) {
                case "1":
                    return aetherAutoLabelWorkflowImpl((Integer) request.get("annotationId"),
                            (String) request.get("imgPath"),
                            agentId);

                case "2":
                    return aetherAutoLabelWorkflowImpl((Integer) request.get("annotationId"),
                            (String) request.get("imgPath"),
                            agentId);
                case "4":
                    return aetherAutoLabelWorkflowImpl((Integer) request.get("annotationId"),
                            (String) request.get("imgPath"),
                            agentId,
                            (String) request.get("label"),
                            (Double) request.get("left"),
                            (Double) request.get("top"),
                            (Double) request.get("right"),
                            (Double) request.get("bottom"));
                case "3":
                    return aetherAutoLabelWorkflowImpl((Integer) request.get("annotationId"),
                            (String) request.get("imgPath"),
                            agentId,
                            (String) request.get("template_image"));
                default:
                    return Result.error("agent not found");
            }
        } catch (Exception e) {
            log.error("aetherAutoLabelWorkflow error", e);
            e.printStackTrace();
            return Result.error("get agent infomation error");
        }

    }

    private Result aetherAutoLabelWorkflowImpl(int annotationId, String imgPath, int agentId) {
        var agent = agentService.getById((long) agentId);
        if (agent == null) {
            return Result.error("agent not found");
        }

        Pipeline pipeline = PipelineParser.loadFromXml(agent.getPipelineContent());
        List<WorkflowStep> steps = pipeline.getSteps().stream().map((v) -> WorkflowStep.fromConfig(v)).toList();
        WorkflowContext context = new WorkflowContext();
        context.put("annotation_id", annotationId);
        context.put("imgPath", imgPath);
        WorkflowEngine workflowEngine = new WorkflowEngine(steps, context);
        workflowEngine.run("1");

        var res = context.get(pipeline.getOutputKey());
        log.debug("detect result: " + res);
        if (res == null) {
            return Result.error("invoke error");
        }

        return Result.OK_data(res);
    }

    private Result aetherAutoLabelWorkflowImpl(int annotationId, String imgPath, int agentId, String templateImage) {
        var agent = agentService.getById((long) agentId);
        if (agent == null) {
            return Result.error("agent not found");
        }

        Pipeline pipeline = PipelineParser.loadFromXml(agent.getPipelineContent());
        List<WorkflowStep> steps = pipeline.getSteps().stream().map((v) -> WorkflowStep.fromConfig(v)).toList();
        WorkflowContext context = new WorkflowContext();
        context.put("annotation_id", annotationId);
        context.put("imgPath", imgPath);
        context.put("template_image", templateImage);
        WorkflowEngine workflowEngine = new WorkflowEngine(steps, context);
        workflowEngine.run("1");

        var res = context.get(pipeline.getOutputKey());
        log.debug("detect result: " + res);
        if (res == null) {
            return Result.error("invoke error");
        }

        return Result.OK_data(res);
    }

    private Result aetherAutoLabelWorkflowImpl(int annotationId, String imgPath, int agentId, String label, double left,
            double top, double right, double bottom) {
        var agent = agentService.getById((long) agentId);
        if (agent == null) {
            return Result.error("agent not found");
        }

        Pipeline pipeline = PipelineParser.loadFromXml(agent.getPipelineContent());
        List<WorkflowStep> steps = pipeline.getSteps().stream().map((v) -> WorkflowStep.fromConfig(v)).toList();
        WorkflowContext context = new WorkflowContext();
        context.put("annotation_id", annotationId);
        context.put("imgPath", imgPath);
        context.put("label", label);
        context.put("left", left);
        context.put("top", top);
        context.put("right", right);
        context.put("bottom", bottom);
        WorkflowEngine workflowEngine = new WorkflowEngine(steps, context);
        workflowEngine.run("1");

        var res = context.get(pipeline.getOutputKey());
        log.debug("detect result: " + res);
        if (res == null) {
            return Result.error("invoke error");
        }

        return Result.OK_data(res);
    }

    @PostMapping("/auto-find-similar")
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
