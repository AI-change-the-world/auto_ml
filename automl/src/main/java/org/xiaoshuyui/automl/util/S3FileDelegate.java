package org.xiaoshuyui.automl.util;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.Resource;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import lombok.extern.slf4j.Slf4j;
import org.apache.opendal.AsyncOperator;
import org.springframework.stereotype.Component;
import org.xiaoshuyui.automl.config.S3ConfigProperties;

@Component
@Slf4j
public class S3FileDelegate implements FileDelegate {

  @Resource private S3ConfigProperties properties;

  private AsyncOperator defaultOperator;
  private Map<String, String> defaultConf;

  // 缓存不同 bucket 的 operator，避免重复初始化
  private final Map<String, AsyncOperator> operatorCache = new ConcurrentHashMap<>();

  @PostConstruct
  public void init() {
    defaultConf =
        createConf(
            properties.getAccessKey(),
            properties.getSecretKey(),
            properties.getBucketName(),
            properties.getEndpoint());
    defaultOperator = AsyncOperator.of("s3", defaultConf);
  }

  private Map<String, String> createConf(
      String accessKey, String secretKey, String bucket, String endpoint) {
    Map<String, String> conf = new HashMap<>();
    conf.put("root", "/");
    conf.put("access_key_id", accessKey);
    conf.put("secret_access_key", secretKey);
    conf.put("bucket", bucket);
    conf.put("endpoint", endpoint);
    conf.put("region", "us-east-1");
    conf.put("enable_virtual_host_style", "false");
    conf.put("log_level", "debug");
    return conf;
  }

  private AsyncOperator getOperator(String bucket) {
    if (bucket == null || bucket.equals(properties.getBucketName())) {
      return defaultOperator;
    }
    return operatorCache.computeIfAbsent(
        bucket,
        b -> {
          Map<String, String> conf =
              createConf(
                  properties.getAccessKey(),
                  properties.getSecretKey(),
                  b,
                  properties.getEndpoint());
          return AsyncOperator.of("s3", conf);
        });
  }

  @Override
  public String getFile(String path) throws Exception {
    return getFile(path, null);
  }

  @Override
  public String getFile(String path, String bucket) throws Exception {
    return getOperator(bucket).presignRead(path, Duration.ofHours(1)).join().getUri();
  }

  @Override
  public void putFile(String path, InputStream inputStream) throws Exception {
    // 优化内存使用：分块上传更合适（如需）
    byte[] bytes = inputStream.readAllBytes();
    defaultOperator.write(path, bytes);
  }

  public String getFileContent(String path) {
    try {
      return new String(defaultOperator.read(path).join());
    } catch (Exception e) {
      log.error("get file content error: {}", e.getMessage());
      return "";
    }
  }

  @Override
  public InputStream getFileStream(String path) throws Exception {
    // 返回文件内容流（需要支持）
    var future = defaultOperator.read(path);
    return new ByteArrayInputStream(future.join());
  }

  @Override
  public List putFileList(List<String> files, String bucket, String basePath) throws Exception {
    AsyncOperator op = getOperator(bucket);
    List<String> result = new java.util.ArrayList<>();
    for (String file : files) {
      Path source = Path.of(file);
      String targetPath = basePath + "/" + source.getFileName();
      log.info("uploading {} to {}", file, targetPath);
      byte[] content = Files.readAllBytes(source);
      op.write(targetPath, content);
      result.add(targetPath);
    }
    return result;
  }

  public void listFiles() throws Exception {
    defaultOperator.list("/").thenAccept(System.out::println).join();
  }

  public List<String> listFiles(String path) throws Exception {
    return defaultOperator.list(path).join().stream().map(item -> item.path).toList();
  }

  public void createDir(String path, String bucket) {
    try {
      if (!path.endsWith("/")) {
        path = path + "/";
      }
      AsyncOperator op = getOperator(bucket);
      op.createDir(path).join();
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }
}
