package org.xiaoshuyui.automl;

import jakarta.annotation.Resource;
import java.io.File;
import java.io.FileInputStream;
import org.springframework.boot.test.context.SpringBootTest;
import org.xiaoshuyui.automl.util.S3FileDelegate;

@SpringBootTest(classes = AutomlApplication.class)
public class OpendalS3Test {

  @Resource private S3FileDelegate s3FileDelegate;

  @org.junit.jupiter.api.Test
  public void test() throws Exception {
    s3FileDelegate.listFiles();
    System.out.println(s3FileDelegate.getFile("image.png"));

    File file = new File("/Users/guchengxi/Desktop/projects/auto_ml/frontend/assets/test.png");
    FileInputStream fileInputStream = new FileInputStream(file);
    s3FileDelegate.putFile("another.png", fileInputStream);
  }
}
