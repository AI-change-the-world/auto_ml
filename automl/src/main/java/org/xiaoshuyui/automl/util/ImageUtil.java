package org.xiaoshuyui.automl.util;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.util.Base64;
import net.coobird.thumbnailator.Thumbnails;

public class ImageUtil {

  public static String compressImage(String path, float quality) throws Exception {
    ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

    Thumbnails.of(new File(path))
        .scale(0.5) // 不缩放尺寸，只压缩质量
        .outputQuality(quality) // 0.0 ~ 1.0，数值越小压缩越大
        .outputFormat("jpg") // 可以强制转为 jpg
        .toOutputStream(outputStream);

    byte[] compressedBytes = outputStream.toByteArray();
    return Base64.getEncoder().encodeToString(compressedBytes);
  }
}
