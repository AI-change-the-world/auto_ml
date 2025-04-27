package org.xiaoshuyui.automl.util;

import jakarta.annotation.PostConstruct;
import org.apache.opendal.AsyncOperator;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.InputStream;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

@Component
public class S3FileDelegate implements FileDelegate{

    @Value("${local-s3.access-key}")
    private String accessKey;

    @Value("${local-s3.secret-key}")
    private String secretKey;

    @Value("${local-s3.bucket-name}")
    private String bucketName;

    @Value("${local-s3.endpoint}")
    private String endpoint;

    static AsyncOperator op;

    @PostConstruct
    public void init() {
        System.out.println("accessKey:" + accessKey);
        System.out.println("secretKey:" + secretKey);
        System.out.println("bucketName:" + bucketName);
        System.out.println("endpoint:" + endpoint);

        final Map<String, String> conf = new HashMap<>();
        conf.put("root", "/");
        conf.put("access_key_id", accessKey);
        conf.put("secret_access_key", secretKey);
        conf.put("bucket", bucketName);
        conf.put("endpoint", endpoint);
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
