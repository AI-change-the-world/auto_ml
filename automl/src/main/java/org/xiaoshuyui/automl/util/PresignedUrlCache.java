package org.xiaoshuyui.automl.util;

import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;

public class PresignedUrlCache {

  @Data
  // 内部类封装缓存条目
  private static class CachedUrl {
    String url;
    long expiresAt;

    CachedUrl(String url, long expiresAt) {
      this.url = url;
      this.expiresAt = expiresAt;
    }

    boolean isExpired() {
      return System.currentTimeMillis() > expiresAt;
    }
  }

  @Data
  @EqualsAndHashCode
  @AllArgsConstructor
  public static class CacheEntry {
    String key;
    String bucket;
  }

  // 线程安全缓存
  private final ConcurrentHashMap<CacheEntry, CachedUrl> cache = new ConcurrentHashMap<>();

  // 过期时间（例如：1 小时 = 3600_000 ms）
  private static final long EXPIRE_TIME_MS = 60 * 60 * 1000;

  /**
   * 获取 Presigned URL，自动缓存
   *
   * @param filePath S3 文件路径（唯一标识）
   * @param generator Function<String, String> 传入 filePath，返回 presigned URL
   */
  public String getPresignedUrl(
      String filePath, String bucket, Function<CacheEntry, String> generator) {
    CacheEntry entry = new CacheEntry(filePath, bucket);
    CachedUrl cached = cache.get(entry);

    if (cached != null && !cached.isExpired()) {
      return cached.url; // 命中缓存
    }

    // 缓存失效或不存在，重新生成
    String newUrl = generator.apply(entry);
    cache.put(entry, new CachedUrl(newUrl, System.currentTimeMillis() + EXPIRE_TIME_MS));

    return newUrl;
  }
}
