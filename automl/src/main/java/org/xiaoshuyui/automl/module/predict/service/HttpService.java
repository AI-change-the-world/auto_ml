package org.xiaoshuyui.automl.module.predict.service;

import com.google.gson.Gson;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.predict.entity.VideoProcessRequest;
import reactor.core.publisher.Flux;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

@Slf4j
@Service
public class HttpService {
    @Value("${ai-platform.video-process}")
    private String videoProcess;

    @Value("${ai-platform.url}")
    private String aiPlatformUrl;

    private static final OkHttpClient client = new OkHttpClient();

    private static final Gson gson = new Gson();

    public Flux<String> getVideoProcess(String url,String sessionId) {
        VideoProcessRequest videoProcessRequest = new VideoProcessRequest();
        videoProcessRequest.setFile(url);
        videoProcessRequest.setSession_id(sessionId);
        String json = gson.toJson(videoProcessRequest);

        RequestBody body = RequestBody.create(json, MediaType.parse("application/json"));
        Request request = new Request.Builder()
                .url(aiPlatformUrl+videoProcess)  // Python SSE接口的 URL
                .post(body)
                .build();

        try {
            Response response = client.newCall(request).execute();
            if (response.isSuccessful() && response.body() != null) {
                return Flux.create(sink -> {
                    BufferedReader reader = new BufferedReader(new InputStreamReader(response.body().byteStream()));

                    String line;
                    while (true) {
                        try {
                            if ((line = reader.readLine()) == null) break;
                        } catch (IOException e) {
                            sink.error(new RuntimeException(e));
                            return;
                        }
                        if (!line.trim().isEmpty()) {
                            sink.next(line);  // 将每行数据推送到 Flux
                        }
                    }
                    sink.complete();
                });
            }
        }catch (Exception e){
            log.error("error",e);
        }

        return null;
    }
}
