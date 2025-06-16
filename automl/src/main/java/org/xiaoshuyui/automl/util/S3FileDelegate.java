package org.xiaoshuyui.automl.util;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.Resource;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import lombok.extern.slf4j.Slf4j;
import org.apache.opendal.AsyncOperator;
import org.apache.opendal.Entry;
import org.apache.opendal.Metadata.EntryMode;
import org.springframework.stereotype.Component;
import org.xiaoshuyui.automl.config.S3ConfigProperties;

@Component
@Slf4j
public class S3FileDelegate implements FileDelegate {

  @Resource private S3ConfigProperties properties;

  private final Map<String, AsyncOperator> operatorCache = new ConcurrentHashMap<>();

  private static final PresignedUrlCache presignedUrlCache = new PresignedUrlCache();

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

  @PostConstruct
  public void init() {
    initOperator(properties.getBucketName());
    initOperator(properties.getDatasetsBucketName());
    initOperator(properties.getModelsBucketName());
  }

  public List<String> getFilesIn(int number, String path, String bucketName) {
    List<Entry> all = getOperator(bucketName).list(path).join(); // 无法避免全拉
    List<String> result = new ArrayList<>();

    for (Entry entry : all) {
      if (entry.getMetadata().mode == EntryMode.FILE) {
        try {
          String presigned = cachedGetFile(entry.path, bucketName);
          result.add(presigned);

        } catch (Exception e) {
          e.printStackTrace();
        }

        if (result.size() >= number) {
          break;
        }
      }
    }

    return result;
  }

  private void initOperator(String bucket) {
    Map<String, String> conf =
        createConf(
            properties.getAccessKey(), properties.getSecretKey(), bucket, properties.getEndpoint());
    operatorCache.put(bucket, AsyncOperator.of("s3", conf));
  }

  // 本地S3
  private AsyncOperator getOperator(String bucketName) {
    // 如果传 null 或等于默认 bucket，则返回默认 operator
    if (bucketName == null || bucketName.equals(properties.getBucketName())) {
      return operatorCache.get(properties.getBucketName());
    }
    // 尝试从缓存获取，如果没有则初始化（兼容动态 bucket）
    return operatorCache.computeIfAbsent(
        bucketName,
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

  public AsyncOperator getOperator(
      String accessKey, String secretKey, String bucket, String endpoint) {
    Map<String, String> conf = createConf(accessKey, secretKey, bucket, endpoint);
    return AsyncOperator.of("s3", conf);
  }

  @Override
  public String getFile(String path) throws Exception {
    return getFile(path, null);
  }

  public String cachedGetFile(String path, String bucket) {

    return presignedUrlCache.getPresignedUrl(
        path,
        bucket,
        cacheEntry -> {
          try {
            return getFile(cacheEntry.getKey(), cacheEntry.getBucket());
          } catch (Exception e) {
            return null;
          }
        });
  }

  @Override
  public String getFile(String path, String bucket) throws Exception {
    return getOperator(bucket).presignRead(path, Duration.ofHours(1)).join().getUri();
  }

  @Override
  public void putFile(String path, InputStream inputStream) throws Exception {
    byte[] bytes = inputStream.readAllBytes();
    getOperator(properties.getBucketName()).write(path, bytes);
  }

  public void putFile(String path, String content, String bucket) {
    getOperator(bucket).write(path, content.getBytes());
  }

  public void putFile(String path, InputStream content, String bucket) throws IOException {
    getOperator(bucket).write(path, content.readAllBytes());
  }

  public String getFileContent(String path, String bucket) {
    try {
      return new String(getOperator(bucket).read(path).join());
    } catch (Exception e) {
      log.error("get file content error: {}", e.getMessage());
      return "";
    }
  }

  @Override
  public InputStream getFileStream(String path, String bucket) throws Exception {
    var future = getOperator(bucket).read(path);
    return new ByteArrayInputStream(future.join());
  }

  @Override
  public List<String> putFileList(List<String> files, String bucket, String basePath)
      throws Exception {
    AsyncOperator op = getOperator(bucket);
    List<String> result = new ArrayList<>();
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
    getOperator(null).list("/").thenAccept(System.out::println).join();
  }

  public List<String> listFiles(String path, String bucket) throws Exception {

    return getOperator(bucket).list(path).join().stream()
        .filter(item -> item.getMetadata().mode == EntryMode.FILE)
        .map(item -> item.path)
        .toList();
  }

  public void createDir(String path, String bucket) {
    try {
      if (!path.endsWith("/")) {
        path = path + "/";
      }
      getOperator(bucket).createDir(path).join();
    } catch (Exception e) {
      throw new RuntimeException(e);
    }
  }
}
