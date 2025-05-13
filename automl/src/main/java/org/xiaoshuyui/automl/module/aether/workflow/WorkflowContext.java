package org.xiaoshuyui.automl.module.aether.workflow;

import java.util.LinkedHashMap;
import java.util.Map;
import lombok.NoArgsConstructor;

@NoArgsConstructor
public class WorkflowContext {
  private final Map<String, Object> data = new LinkedHashMap<>();

  public void put(String key, Object val) {
    data.put(key, val);
  }

  public Object get(String key) {
    return data.get(key);
  }

  public Object getOrDefault(String key, Object defaultVal) {
    return data.getOrDefault(key, defaultVal);
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
