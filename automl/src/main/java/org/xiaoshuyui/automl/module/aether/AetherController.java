package org.xiaoshuyui.automl.module.aether;

import java.util.HashMap;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse;
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
}
