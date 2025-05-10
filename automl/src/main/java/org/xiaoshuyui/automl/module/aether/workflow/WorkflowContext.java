package org.xiaoshuyui.automl.module.aether.workflow;

import java.util.HashMap;
import java.util.Map;
import lombok.NoArgsConstructor;

@NoArgsConstructor
public class WorkflowContext {
  private final Map<String, Object> data = new HashMap<>();

  public void put(String key, Object val) {
    data.put(key, val);
  }

  public Object get(String key) {
    return data.get(key);
  }

  public void print() {
    for (Map.Entry<String, Object> entry : data.entrySet()) {
      System.out.println(entry.getKey() + " = " + entry.getValue());
    }
  }

  public <T> T get(String key, Class<T> clazz) {
    return clazz.cast(data.get(key));
  }
}
