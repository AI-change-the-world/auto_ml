package org.xiaoshuyui.automl;

import java.util.HashMap;
import java.util.Map;
import org.apache.opendal.*;
import org.junit.jupiter.api.Test;

public class OpendalTest {

  @Test
  public void test() {
    // 构造本地文件系统的Operator
    final Map<String, String> conf = new HashMap<>();
    conf.put("root", "/Users/guchengxi/Desktop/projects/auto_ml/frontend/dataset/images/");

    try (AsyncOperator op = AsyncOperator.of("fs", conf)) {
      var res = op.list("").join();
      for (var item : res) {
        System.out.println(item.path);
      }
    }
  }
}
