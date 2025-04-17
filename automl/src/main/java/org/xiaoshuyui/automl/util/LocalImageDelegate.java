package org.xiaoshuyui.automl.util;

import org.springframework.stereotype.Component;

import java.io.File;
import java.nio.file.Files;
import java.util.Base64;

@Component
public class LocalImageDelegate implements FileDelegate {
    @Override
    public String getFile(String path) throws Exception {
        String b64 = ImageUtil.compressImage(path, 0.5f);
        return b64;
    }

    public String getFileUnCompress(String path) throws Exception {
        File file = new File(path);
        String mimeType = Files.probeContentType(file.toPath()); // 自动识别 MIME 类型

        byte[] content = Files.readAllBytes(file.toPath());
        String base64 = Base64.getEncoder().encodeToString(content);

        return "data:" + mimeType + ";base64," + base64;
    }
}
