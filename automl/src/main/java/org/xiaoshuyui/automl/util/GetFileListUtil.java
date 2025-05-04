package org.xiaoshuyui.automl.util;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.opendal.AsyncOperator;

/*
 * 
 * 获取本地文件列表
*/
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
    List<String> allFiles = new ArrayList<>();
    if (storageType == 0) {
      try (AsyncOperator op = AsyncOperator.of("fs", conf)) {
        var res = op.list("").join();
        // return res.stream().map(item -> item.path).toList();
        for (var item : res) {
          if (item.metadata.isDir()) {
            continue;
          }
          if (item.metadata.isFile()) {
            allFiles.add(baseDir + "/" + item.path);
          }
        }
      }
    }

    return allFiles;
  }
}
