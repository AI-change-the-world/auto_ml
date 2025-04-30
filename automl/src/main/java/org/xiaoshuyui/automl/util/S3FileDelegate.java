package org.xiaoshuyui.automl.util;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.Resource;
import java.io.InputStream;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;
import org.apache.opendal.AsyncOperator;
import org.springframework.stereotype.Component;
import org.xiaoshuyui.automl.config.S3ConfigProperties;

@Component
public class S3FileDelegate implements FileDelegate {

  @Resource S3ConfigProperties properties;

  static AsyncOperator op;

  @PostConstruct
  public void init() {
    System.out.println("accessKey:" + properties.getAccessKey());
    System.out.println("secretKey:" + properties.getSecretKey());
    System.out.println("bucketName:" + properties.getBucketName());
    System.out.println("endpoint:" + properties.getEndpoint());

    final Map<String, String> conf = new HashMap<>();
    conf.put("root", "/");
    conf.put("access_key_id", properties.getAccessKey());
    conf.put("secret_access_key", properties.getSecretKey());
    conf.put("bucket", properties.getBucketName());
    conf.put("endpoint", properties.getEndpoint());
    conf.put("region", "us-east-1");
    conf.put("enable_virtual_host_style", "false");
    conf.put("log_level", "debug");

    op = AsyncOperator.of("s3", conf);
  }

  @Override
  public String getFile(String path) throws Exception {
    var res = op.presignRead(path, Duration.ofSeconds(3600));
    return res.join().getUri();
  }

  @Override
  public void putFile(String path, InputStream inputStream) throws Exception {
    op.write(path, inputStream.readAllBytes());
    //        FileDelegate.super.putFile(path, inputStream);
  }

  public void listFiles() throws Exception {
    op.list("/").thenAccept(System.out::println).join();
  }

  @Override
  public InputStream getFileStream(String path) throws Exception {
    return null;
  }
}
