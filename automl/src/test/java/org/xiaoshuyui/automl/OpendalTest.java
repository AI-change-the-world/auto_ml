package org.xiaoshuyui.automl;

import org.apache.opendal.*;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.Map;


public class OpendalTest {

    @Test
    public void test() {
        // 构造本地文件系统的Operator
        final Map<String, String> conf = new HashMap<>();
        conf.put("root", "/");

        try (AsyncOperator op = AsyncOperator.of("fs", conf)) {
            var res = op.list("/Users/guchengxi/Desktop/projects/auto_ml/frontend/dataset/images/").join();
            for (var item : res) {
                System.out.println(item.path);
            }
        }
    }
}
