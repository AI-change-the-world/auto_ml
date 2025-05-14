package org.xiaoshuyui.automl.module.aether;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.reflect.TypeToken;
import jakarta.annotation.Resource;
import java.lang.reflect.Type;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.xiaoshuyui.automl.module.aether.entity.AetherRequest;
import org.xiaoshuyui.automl.module.aether.entity.AetherResponse;
import org.xiaoshuyui.automl.module.task.service.TaskService;

@Slf4j
@Component
public class AetherClient {
  @Value("${ai-platform.url}")
  String url;

  @Value("${ai-platform.aether}")
  String aether;

  @Resource private TaskService taskService;

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

  /*
   * params : {"data":str,"data_type":str,"extra":map}
   */
  @Deprecated(since = "use  `invoke(AetherRequest request, Class<R> outputClass)` ")
  public <T, R> AetherResponse<R> invoke(
      String task, Map<String, Object> params, Long modelId, Class<R> outputClass) {
    AetherRequest<Map<String, Object>> request = new AetherRequest<>();
    request.setTask(task);
    request.setModelId(modelId);
    log.debug("param: " + params);
    request.setInput(
        new AetherRequest.Input(params.get("data").toString(), params.get("data_type").toString()));

    AetherRequest.Meta meta = new AetherRequest.Meta();
    meta.setSync(true);

    // 设置 extra 可选参数
    if (params.containsKey("extra")) {
      request.setExtra((Map<String, Object>) params.get("extra"));
    }
    request.setMeta(meta);

    // Serialize request
    String requestJson = gson.toJson(request);

    // Send HTTP POST
    RequestBody body = RequestBody.create(requestJson, MediaType.get("application/json"));
    Request httpRequest = new Request.Builder().url(url + aether).post(body).build();

    try {
      Response httpResponse = client.newCall(httpRequest).execute();
      if (!httpResponse.isSuccessful()) {
        throw new RuntimeException("Request failed: " + httpResponse.code());
      }

      String responseJson = httpResponse.body().string();

      // 使用 TypeToken 反序列化
      Type responseType = TypeToken.getParameterized(AetherResponse.class, outputClass).getType();
      return gson.fromJson(responseJson, responseType);
    } catch (Exception e) {
      log.error("invoke error: {}", e.getMessage());
      return null;
    }
  }

  public <T, R> AetherResponse<R> invoke(AetherRequest request, Class<R> outputClass) {

    // Serialize request
    String requestJson = gson.toJson(request);

    log.debug("param: " + requestJson);

    // Send HTTP POST
    RequestBody body = RequestBody.create(requestJson, MediaType.get("application/json"));
    Request httpRequest = new Request.Builder().url(url + aether).post(body).build();

    try {
      Response httpResponse = client.newCall(httpRequest).execute();
      if (!httpResponse.isSuccessful()) {
        throw new RuntimeException("Request failed: " + httpResponse.code());
      }

      String responseJson = httpResponse.body().string();

      // 使用 TypeToken 反序列化
      Type responseType = TypeToken.getParameterized(AetherResponse.class, outputClass).getType();
      return gson.fromJson(responseJson, responseType);
    } catch (Exception e) {
      log.error("invoke error: {}", e.getMessage());
      return null;
    }
  }
}
