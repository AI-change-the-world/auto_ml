package org.xiaoshuyui.automl.util;

import org.springframework.stereotype.Component;

@Component
public class LocalImageDelegate implements FileDelegate {
    @Override
    public String getFile(String path) throws Exception {
        String b64 = ImageUtil.compressImage(path, 0.5f);
        return b64;
    }
}
