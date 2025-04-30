package org.xiaoshuyui.automl.module;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

@Slf4j
@Component
public class HeartbeatChecker {
  @Value("${ai-platform.url}")
  String aiPlatformUrl;

  private final RestTemplate restTemplate = new RestTemplate();

  @Scheduled(fixedRate = 300_000)
  public void checkHeartbeat() {
    try {
      ResponseEntity<String> response = restTemplate.getForEntity(aiPlatformUrl, String.class);
      if (response.getStatusCode().is2xxSuccessful()) {
        log.info("AI platform 服务正常 ✅ 状态码: {}", response.getStatusCode());
      } else {
        log.warn("AI platform 服务异常 ⚠️ 状态码: {}", response.getStatusCode());
      }
    } catch (Exception e) {
      log.error("AI platform 服务访问失败 ❌ 异常信息: {}", e.getMessage());
    }
  }
}
