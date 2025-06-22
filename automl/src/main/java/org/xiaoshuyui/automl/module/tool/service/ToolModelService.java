package org.xiaoshuyui.automl.module.tool.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;
import java.util.List;
import java.util.concurrent.TimeUnit;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.xiaoshuyui.automl.common.PythonApiResponse;
import org.xiaoshuyui.automl.module.aether.entity.Agent;
import org.xiaoshuyui.automl.module.aether.service.AgentService;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse;
import org.xiaoshuyui.automl.module.tool.entity.FindSimilarObjectRequest;
import org.xiaoshuyui.automl.module.tool.entity.LabelData;
import org.xiaoshuyui.automl.module.tool.entity.ModelUseRequest;
import org.xiaoshuyui.automl.module.tool.entity.NewModelRequest;
import org.xiaoshuyui.automl.module.tool.entity.PredictRequest;
import org.xiaoshuyui.automl.module.tool.entity.ToolModel;
import org.xiaoshuyui.automl.module.tool.mapper.ToolModelMapper;

@Service
@Slf4j
public class ToolModelService {

  @Value("${ai-platform.url}")
  String baseUrl;

  @Value("${ai-platform.get-label}")
  String getLabelApi;

  @Value("${ai-platform.get-multi-class-label}")
  String getMultiClassApi;

  @Value("${ai-platform.find-similar}")
  String findSimilarApi;

  private final ToolModelMapper toolModelMapper;
  private final AnnotationService annotationService;
  private final AgentService agentService;

  public ToolModelService(ToolModelMapper toolModelMapper, AnnotationService annotationService,
      AgentService agentService) {
    this.toolModelMapper = toolModelMapper;
    this.annotationService = annotationService;
    this.agentService = agentService;
  }

  public List<ToolModel> getAll() {
    QueryWrapper<ToolModel> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("is_deleted", 0);
    return toolModelMapper.selectList(queryWrapper);
  }

  public ToolModel getById(Long id) {
    QueryWrapper<ToolModel> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("is_deleted", 0);
    queryWrapper.eq("tool_model_id", id);
    return toolModelMapper.selectOne(queryWrapper);
  }

  private static final OkHttpClient client = new OkHttpClient.Builder()
      .connectTimeout(300, TimeUnit.SECONDS) // 连接超时时间
      .readTimeout(1800, TimeUnit.SECONDS) // 读取超时时间
      .writeTimeout(300, TimeUnit.SECONDS) // 写入超时时间
      .build();

  private static Gson gson = new GsonBuilder()
      .serializeNulls() // 👈 关键：保留 null 字段
      .create();

  public LabelData getLabel(ModelUseRequest request) {

    try {
      PredictRequest predictRequest = new PredictRequest();
      Annotation annotation = annotationService.getById(request.getAnnotationId());
      predictRequest.setImage_data(request.getContent());
      predictRequest.setModel_id(request.getModelId());
      predictRequest.setClasses(List.of(annotation.getClassItems().split(";")));
      predictRequest.setPrompt(request.getPrompt());

      // 创建 RequestBody
      RequestBody body = RequestBody.create(gson.toJson(predictRequest), MediaType.parse("application/json"));
      Request req = new Request.Builder().url(baseUrl + getLabelApi).post(body).build();

      Response response = client.newCall(req).execute();
      Type type = new TypeToken<PythonApiResponse<LabelData>>() {
      }.getType();
      PythonApiResponse<LabelData> labelData = gson.fromJson(response.body().string(), type);
      return labelData.data;

    } catch (Exception e) {
      System.out.println(e);
      log.error("auto label error: {}", e.getMessage());
      return null;
    }
  }

  // find similar
  public PredictSingleImageResponse findSimilar(FindSimilarObjectRequest request) {
    try {
      RequestBody body = RequestBody.create(gson.toJson(request), MediaType.parse("application/json"));
      Request req = new Request.Builder().url(baseUrl + findSimilarApi).post(body).build();
      Response response = client.newCall(req).execute();
      Type type = new TypeToken<PythonApiResponse<PredictSingleImageResponse>>() {
      }.getType();

      PythonApiResponse<PredictSingleImageResponse> pythonApiResponse = gson.fromJson(response.body().string(), type);

      return pythonApiResponse.data;
    } catch (Exception e) {
      e.printStackTrace();
      log.error("find similar error: {}", e.getMessage());
      return null;
    }
  }

  // 多类物体识别
  /*
   * class MultiClassImageAnnotateRequest(BaseModel):
   * image_data: str
   * annotation_id: int
   * tool_model_id: int
   */
  public PredictSingleImageResponse getMultipleClasses(
      Long annotationId, String imgPath, Long toolModelId) {
    try {
      String json = String.format(
          "{\"annotation_id\":\"%d\",\"image_data\":\"%s\",\"tool_model_id\":%d}",
          annotationId, imgPath, toolModelId);

      log.info("Request: {}", json);

      RequestBody body = RequestBody.create(json, MediaType.parse("application/json"));
      Request req = new Request.Builder().url(baseUrl + getMultiClassApi).post(body).build();
      Response response = client.newCall(req).execute();
      Type type = new TypeToken<PythonApiResponse<PredictSingleImageResponse>>() {
      }.getType();

      PythonApiResponse<PredictSingleImageResponse> pythonApiResponse = gson.fromJson(response.body().string(), type);

      return pythonApiResponse.data;
    } catch (Exception e) {
      e.printStackTrace();
      log.error("find similar error: {}", e.getMessage());
      return null;
    }
  }

  private static String pipelineTemplate = """
      <?xml version="1.0" encoding="UTF-8"?>
      <pipeline outputKey="1_result" name="label-image" sync="true">
          <step id="1" name="label-image">
              <action class="org.xiaoshuyui.automl.module.aether.workflow.action.LabelImageAction"/>
              <aether>
                  <task>label</task>
                  <modelId>{{model_id}}</modelId>
                  <inputType>image</inputType>
                  <inputKey>imgPath</inputKey>
                  <extra>
                      <entry key="annotation_id" type="num">${annotation_id}</entry>
                  </extra>
              </aether>
          </step>
      </pipeline>
                  """;

  @Transactional
  public void addNewModel(NewModelRequest request) throws Exception {
    QueryWrapper<ToolModel> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("tool_model_name", request.getName());
    var e = toolModelMapper.selectOne(queryWrapper);
    if (e != null) {
      throw new RuntimeException("model name already exists");
    }

    ToolModel toolModel = new ToolModel();
    toolModel.setName(request.getName());
    toolModel.setDescription(request.getDescription());
    toolModel.setModelName(request.getModelName());
    toolModel.setBaseUrl(request.getBaseUrl());
    toolModel.setApiKey(request.getApiKey());
    toolModel.setType(request.getType());
    toolModelMapper.insert(toolModel);

    String pipeline = pipelineTemplate.replace("{{model_id}}", toolModel.getId().toString()).trim();

    Agent agent = new Agent();
    agent.setName(request.getName() + " 智能体");
    agent.setDescription("创建model之后自动生成的Agent， 基座模型是" + request.getModelName());
    agent.setPipelineContent(pipeline);
    agent.setIsEmbedded(0);
    agent.setIsRecommended(0);
    agentService.newAgent(agent);
  }
}
