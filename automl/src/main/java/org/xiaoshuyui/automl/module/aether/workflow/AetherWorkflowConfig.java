package org.xiaoshuyui.automl.module.aether.workflow;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlElementWrapper;
import jakarta.xml.bind.annotation.XmlValue;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import lombok.Data;

@Data
@XmlAccessorType(value = XmlAccessType.FIELD)
public class AetherWorkflowConfig {
  private String task;
  private Long modelId;
  private String inputType;
  private String inputKey;

  @XmlElementWrapper(name = "extra")
  @XmlElement(name = "entry")
  private List<Entry> extraEntries;

  @Override
  public String toString() {
    return "task: "
        + task
        + "\n"
        + "modelId: "
        + modelId
        + "\n"
        + "inputType: "
        + inputType
        + "\n"
        + "inputKey: "
        + inputKey
        + "\n"
        + "extraEntries: "
        + extraEntries
        + "\n";
  }

  public Map<String, Object> getExtra(WorkflowContext context) {
    Map<String, Object> result = new HashMap<>();
    if (extraEntries != null) {
      for (Entry e : extraEntries) {
        String resolvedValue = resolvePlaceholders(e.value, context);
        if (e.type.equals("num")) {
          try {
            if (resolvedValue.contains(".")) {
              result.put(e.key, Double.parseDouble(resolvedValue));
            } else {
              result.put(e.key, Long.parseLong(resolvedValue));
            }
          } catch (NumberFormatException ex) {
            result.put(e.key, resolvedValue);
          }
        } else {
          result.put(e.key, resolvedValue);
        }
      }
    }
    return result;
  }

  private String resolvePlaceholders(String value, WorkflowContext context) {
    if (value == null) return null;

    Pattern pattern = Pattern.compile("\\$\\{(.+?)}");
    Matcher matcher = pattern.matcher(value);
    StringBuffer sb = new StringBuffer();
    while (matcher.find()) {
      String varName = matcher.group(1);
      Object replacement = context.get(varName);
      matcher.appendReplacement(
          sb, Matcher.quoteReplacement(replacement != null ? replacement.toString() : ""));
    }
    matcher.appendTail(sb);
    return sb.toString();
  }

  // simple inner class for <entry key=...>value</entry>
  @XmlAccessorType(value = XmlAccessType.FIELD)
  @Data
  public static class Entry {
    @XmlAttribute public String key;
    @XmlValue public String value;
    @XmlAttribute public String type = "str"; // 默认类型为字符串

    @Override
    public String toString() {
      return "Entry{" + "key='" + key + '\'' + ", value='" + value + '\'' + '}';
    }
  }
}
