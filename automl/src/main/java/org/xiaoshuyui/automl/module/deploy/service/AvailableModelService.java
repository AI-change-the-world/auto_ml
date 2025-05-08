package org.xiaoshuyui.automl.module.deploy.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import java.lang.reflect.Type;
import java.util.concurrent.TimeUnit;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.common.PageRequest;
import org.xiaoshuyui.automl.common.PageResult;
import org.xiaoshuyui.automl.common.PythonApiResponse;
import org.xiaoshuyui.automl.module.deploy.entity.AvailableModel;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageRequest;
import org.xiaoshuyui.automl.module.deploy.entity.PredictSingleImageResponse;
import org.xiaoshuyui.automl.module.deploy.entity.RunningModelsResponse;
import org.xiaoshuyui.automl.module.deploy.mapper.AvailableModelMapper;

@Service
@Slf4j
public class AvailableModelService {

  private final AvailableModelMapper availableModelMapper;

  public AvailableModelService(AvailableModelMapper availableModelMapper) {
    this.availableModelMapper = availableModelMapper;
  }

  @Value("${ai-platform.url}")
  String aiPlatformUrl;

  @Value("${ai-platform.get-running-models}")
  String getRunningModels;

  @Value("${ai-platform.start-model}")
  String startModel;

  @Value("${ai-platform.stop-model}")
  String stopModel;

  @Value("${ai-platform.predict-single-image}")
  String predictSingleImage;

  private static final OkHttpClient client =
      new OkHttpClient.Builder()
          .connectTimeout(300, TimeUnit.SECONDS) // 连接超时时间
          .readTimeout(1800, TimeUnit.SECONDS) // 读取超时时间
          .writeTimeout(300, TimeUnit.SECONDS) // 写入超时时间
          .build();

  private static Gson gson =
      new GsonBuilder()
          .serializeNulls() // 👈 关键：保留 null 字段
          .create();

  public PageResult getAvailableModels(PageRequest pageRequest) {
    IPage<AvailableModel> page = new Page<>(pageRequest.getPageId(), pageRequest.getPageSize());
    QueryWrapper<AvailableModel> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("is_deleted", 0);

    IPage<AvailableModel> resultPage = availableModelMapper.selectPage(page, queryWrapper);
    return new PageResult<>(resultPage.getRecords(), resultPage.getTotal());
  }

  public RunningModelsResponse getRunningModels() {

    try {
      Request request = new Request.Builder().url(aiPlatformUrl + getRunningModels).get().build();

      Response response = client.newCall(request).execute();
      Type type = new TypeToken<PythonApiResponse<RunningModelsResponse>>() {}.getType();

      PythonApiResponse<RunningModelsResponse> runningModelsResponse =
          gson.fromJson(response.body().string(), type);

      return runningModelsResponse.data;
    } catch (Exception e) {
      System.out.println(e);
      log.error("auto label error: {}", e.getMessage());
      return null;
    }
  }

  public int startModel(Long id) {
    try {
      Request request =
          new Request.Builder().url(aiPlatformUrl + startModel + id.toString()).get().build();
      Response response = client.newCall(request).execute();
      if (response.isSuccessful()) {
        log.info("start model success");
        return 0;
      } else {
        log.error("start model error: {}", response);
        return 1;
      }
    } catch (Exception e) {
      System.out.println(e);
      log.error("auto label error: {}", e.getMessage());
      return 1;
    }
  }

  public int stopModel(Long id) {
    try {
      Request request =
          new Request.Builder().url(aiPlatformUrl + stopModel + id.toString()).get().build();
      Response response = client.newCall(request).execute();
      if (response.isSuccessful()) {
        log.info("start model success");
        return 0;
      } else {
        log.error("start model error: {}", response);
        return 1;
      }
    } catch (Exception e) {
      log.error("stop model error: {}", e.getMessage());
      return 1;
    }
  }

  public PredictSingleImageResponse predictSingleImage(PredictSingleImageRequest entity) {
    try {
      String json =
          String.format(
              "{\"data\":\"%s\",\"model_id\":%d}",
              escapeJson(entity.getData()), // 避免特殊字符问题
              entity.getModelId());

      RequestBody body = RequestBody.create(json, MediaType.parse("application/json"));

      Request request =
          new Request.Builder()
              .url(aiPlatformUrl + predictSingleImage) // 替换为实际地址
              .post(body)
              .build();
      Response response = client.newCall(request).execute();
      if (response.isSuccessful() && response.body() != null) {
        Type type = new TypeToken<PythonApiResponse<PredictSingleImageResponse>>() {}.getType();

        PythonApiResponse<PredictSingleImageResponse> pythonApiResponse =
            gson.fromJson(response.body().string(), type);

        return pythonApiResponse.data;

      } else {
        log.error("Response error: {}", response);
        return null;
      }

    } catch (Exception e) {
      log.error("predict single image error: {}", e.getMessage());
      return null;
    }
  }

  private static String escapeJson(String input) {
    return input.replace("\\", "\\\\").replace("\"", "\\\"");
  }
}
