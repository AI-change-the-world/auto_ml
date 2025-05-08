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
import org.xiaoshuyui.automl.common.PythonApiResponse;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse;
import org.xiaoshuyui.automl.module.tool.entity.FindSimilarObjectRequest;
import org.xiaoshuyui.automl.module.tool.entity.LabelData;
import org.xiaoshuyui.automl.module.tool.entity.ModelUseRequest;
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

  @Value("${ai-platform.find-similar}")
  String findSimilarApi;

  private final ToolModelMapper toolModelMapper;
  private final AnnotationService annotationService;

  public ToolModelService(ToolModelMapper toolModelMapper, AnnotationService annotationService) {
    this.toolModelMapper = toolModelMapper;
    this.annotationService = annotationService;
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
}
