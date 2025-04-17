package org.xiaoshuyui.automl.util;

import org.springframework.stereotype.Component;

import java.io.File;
import java.nio.file.Files;
import java.nio.file.Paths;

@Component
public class LocalAnnotationDelegate implements FileDelegate{
    @Override
    public String getFile(String path) throws Exception {
        File file = new File(path);
        if (file.exists()) {
            return new String(Files.readAllBytes(Paths.get(path)));
        }
        return "";
    }
}
