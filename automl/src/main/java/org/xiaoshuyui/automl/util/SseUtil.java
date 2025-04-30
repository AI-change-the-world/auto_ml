package org.xiaoshuyui.automl.util;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
public class SseUtil {
  private static final Gson gson =
      new GsonBuilder()
          .serializeNulls() // 👈 关键：保留 null 字段
          .create();

  public static void sseSend(SseEmitter emitter, Object o) {
    try {
      emitter.send(gson.toJson(o));
    } catch (Exception e) {
      log.error(e.getMessage());
      emitter.completeWithError(e);
    }
  }
}
