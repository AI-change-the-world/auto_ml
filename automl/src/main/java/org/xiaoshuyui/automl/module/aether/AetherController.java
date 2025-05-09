package org.xiaoshuyui.automl.module.aether;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.xiaoshuyui.automl.common.Result;
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

    public AetherController(AetherClient aetherClient) {
        System.out.println("✅ AetherController loaded");
        this.aetherClient = aetherClient;
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
    public Result aetherAutoLabelWorkflow(@RequestBody MultipleClassAnnotateRequest request) {
        Pipeline pipeline = PipelineParser.loadFromResource("pipeline/pipeline.xml");
        List<WorkflowStep> steps = pipeline.getSteps().stream().map((v) -> WorkflowStep.fromConfig(v)).toList();
        WorkflowContext context = new WorkflowContext();
        context.put("annotation_id", request.getAnnotationId());
        context.put("imgPath", request.getImgPath());
        WorkflowEngine workflowEngine = new WorkflowEngine(steps, context);
        workflowEngine.run("1");

        var res = context.get(pipeline.getOutputKey());
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
