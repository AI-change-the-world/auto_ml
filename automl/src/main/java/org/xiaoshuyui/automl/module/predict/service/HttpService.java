package org.xiaoshuyui.automl.module.predict.service;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.List;
import java.util.concurrent.TimeUnit;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.predict.entity.DescribeImageListRequest;
import org.xiaoshuyui.automl.module.predict.entity.DescribeImageRequest;
import org.xiaoshuyui.automl.module.predict.entity.PythonVideoProcessRequest;
import reactor.core.publisher.Flux;

@Slf4j
@Service
public class HttpService {
  @Value("${ai-platform.video-process}")
  private String videoProcess;

  @Value("${ai-platform.url}")
  private String aiPlatformUrl;

  @Value("${ai-platform.describe-image}")
  private String describeImage;

  @Value("${ai-platform.describe-image-list}")
  private String describeImageList;

  private static final OkHttpClient client = new OkHttpClient.Builder()
      .connectTimeout(300, TimeUnit.SECONDS) // 连接超时时间
      .readTimeout(1800, TimeUnit.SECONDS) // 读取超时时间
      .writeTimeout(300, TimeUnit.SECONDS) // 写入超时时间
      .build();

  private static Gson gson = new GsonBuilder()
      .serializeNulls() // 👈 关键：保留 null 字段
      .create();

  public Flux<String> getVideoProcess(String url, String sessionId) {
    PythonVideoProcessRequest pythonVideoProcessRequest = new PythonVideoProcessRequest();
    pythonVideoProcessRequest.setFile(url);
    pythonVideoProcessRequest.setSession_id(sessionId);
    String json = gson.toJson(pythonVideoProcessRequest);

    RequestBody body = RequestBody.create(json, MediaType.parse("application/json"));
    Request request = new Request.Builder().url(aiPlatformUrl + videoProcess).post(body).build();

    try {
      Response response = client.newCall(request).execute();
      if (response.isSuccessful() && response.body() != null) {
        // 这里用 Flux.using 来确保资源管理正确
        return Flux.using(
            () -> response, // Resource supplier
            resp -> Flux.create(
                sink -> {
                  try (BufferedReader reader = new BufferedReader(new InputStreamReader(resp.body().byteStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                      if (!line.trim().isEmpty()) {
                        sink.next(line);
                      }
                    }
                    sink.complete();
                  } catch (IOException e) {
                    sink.error(new RuntimeException(e));
                  }
                }),
            resp -> {
              // Cleanup logic, always close response
              if (resp != null) {
                resp.close();
              }
            });
      } else {
        log.error("Response error: {}", response);
        if (response != null) {
          response.close();
        }
      }
    } catch (Exception e) {
      log.error("Request error", e);
    }
    return Flux.error(new IllegalStateException("Cannot connect to AI platform."));
  }

  // TODO model should not be set by default
  public Flux<String> getDescribeImage(String filepath) {
    DescribeImageRequest describeImageRequest = new DescribeImageRequest();
    describeImageRequest.setFrame_path(filepath);
    describeImageRequest.setModel_id(1L);
    describeImageRequest.setPrompt(null);

    String json = gson.toJson(describeImageRequest);
    log.info("Describe image request: {}", json);
    RequestBody body = RequestBody.create(json, MediaType.parse("application/json"));
    Request request = new Request.Builder().url(aiPlatformUrl + describeImage).post(body).build();

    try {
      Response response = client.newCall(request).execute();
      if (response.isSuccessful() && response.body() != null) {
        // 这里用 Flux.using 来确保资源管理正确
        return Flux.using(
            () -> response, // Resource supplier
            resp -> Flux.create(
                sink -> {
                  try (BufferedReader reader = new BufferedReader(new InputStreamReader(resp.body().byteStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                      if (!line.trim().isEmpty()) {
                        sink.next(line);
                      }
                    }
                    sink.complete();
                  } catch (IOException e) {
                    sink.error(new RuntimeException(e));
                  }
                }),
            resp -> {
              // Cleanup logic, always close response
              if (resp != null) {
                resp.close();
              }
            });
      } else {
        log.error("Response error: {}", response);
        if (response != null) {
          response.close();
        }
      }
    } catch (Exception e) {
      log.error("Request error", e);
    }
    return Flux.error(new IllegalStateException("Cannot connect to AI platform."));
  }

  // TODO model should not be set by default
  public Flux<String> getDescribeImageList(List<String> filepath) {
    DescribeImageListRequest describeImageRequest = new DescribeImageListRequest();
    describeImageRequest.setFrames(filepath);
    describeImageRequest.setModel_id(1L);
    describeImageRequest.setPrompt(null);

    String json = gson.toJson(describeImageRequest);
    log.info("Describe image request: {}", json);
    RequestBody body = RequestBody.create(json, MediaType.parse("application/json"));
    Request request = new Request.Builder().url(aiPlatformUrl + describeImageList).post(body).build();

    try {
      Response response = client.newCall(request).execute();
      if (response.isSuccessful() && response.body() != null) {
        // 这里用 Flux.using 来确保资源管理正确
        return Flux.using(
            () -> response, // Resource supplier
            resp -> Flux.create(
                sink -> {
                  try (BufferedReader reader = new BufferedReader(new InputStreamReader(resp.body().byteStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                      if (!line.trim().isEmpty()) {
                        sink.next(line);
                      }
                    }
                    sink.complete();
                  } catch (IOException e) {
                    sink.error(new RuntimeException(e));
                  }
                }),
            resp -> {
              // Cleanup logic, always close response
              if (resp != null) {
                resp.close();
              }
            });
      } else {
        log.error("Response error: {}", response);
        if (response != null) {
          response.close();
        }
      }
    } catch (Exception e) {
      log.error("Request error", e);
    }
    return Flux.error(new IllegalStateException("Cannot connect to AI platform."));
  }
}
