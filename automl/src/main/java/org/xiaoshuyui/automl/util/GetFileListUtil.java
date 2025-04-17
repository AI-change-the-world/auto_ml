package org.xiaoshuyui.automl.util;

import org.apache.opendal.AsyncOperator;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class GetFileListUtil {

    public static List<String> getFileList(String baseDir, int storageType) {
        if (baseDir == null) {
            return null;
        }
        final Map<String, String> conf = new HashMap<>();
        String path = baseDir;
        if (!path.endsWith("/")) {
            path = path + "/";
        }
        conf.put("root", path);
        if (storageType == 0) {
            try (AsyncOperator op = AsyncOperator.of("fs", conf)) {
                var res = op.list("").join();
                return res.stream().map(item -> item.path).toList();
            }
        }

        return null;
    }
}
