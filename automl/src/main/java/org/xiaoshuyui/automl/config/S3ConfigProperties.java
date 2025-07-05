package org.xiaoshuyui.automl.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.stereotype.Component;

@Data
@Component
@RefreshScope
@ConfigurationProperties(prefix = "local-s3-config")
public class S3ConfigProperties {
  private String accessKey;
  private String secretKey;
  private String bucketName;
  private String endpoint;
  private String datasetsBucketName;
  private String modelsBucketName;
  private String augmentBucketName;

  @Override
  public String toString() {
    return "accessKey: "
        + accessKey
        + "\n"
        + "secretKey: "
        + secretKey
        + "\n"
        + "bucketName: "
        + bucketName
        + "\n"
        + "endpoint: "
        + endpoint
        + "\n"
        + "datasetBucketName: "
        + datasetsBucketName
        + "\n"
        + "modelsBucketName: "
        + modelsBucketName
        + "\n"
        + "augmentBucketName: "
        + augmentBucketName
        + "\n";
  }
}
