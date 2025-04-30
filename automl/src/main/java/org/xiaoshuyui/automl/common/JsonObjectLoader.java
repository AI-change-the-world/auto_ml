package org.xiaoshuyui.automl.common;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;
import java.lang.reflect.Field;

public class JsonObjectLoader {

  private static final ObjectMapper mapper = new ObjectMapper();

  // 从字符串加载并可选校验
  public static <T> T loadFromString(String json, Class<T> clazz, boolean validate) {
    try {
      T obj = mapper.readValue(json, clazz);
      if (validate) validateFields(obj);
      return obj;
    } catch (JsonProcessingException e) {
      System.err.println("❌ JSON 解析失败: " + e.getMessage());
    } catch (IllegalAccessException e) {
      System.err.println("❌ 字段访问失败: " + e.getMessage());
    } catch (IllegalArgumentException e) {
      System.err.println("❌ 校验失败: " + e.getMessage());
    }
    return null;
  }

  // 从文件加载并可选校验
  public static <T> T loadFromFile(String filePath, Class<T> clazz, boolean validate) {
    try {
      T obj = mapper.readValue(new File(filePath), clazz);
      if (validate) validateFields(obj);
      return obj;
    } catch (IOException e) {
      System.err.println("❌ 文件读取或 JSON 解析失败: " + e.getMessage());
    } catch (IllegalAccessException e) {
      System.err.println("❌ 字段访问失败: " + e.getMessage());
    } catch (IllegalArgumentException e) {
      System.err.println("❌ 校验失败: " + e.getMessage());
    }
    return null;
  }

  // 基于反射通用校验非空字段
  private static <T> void validateFields(T obj) throws IllegalAccessException {
    Class<?> clazz = obj.getClass();
    for (Field field : clazz.getDeclaredFields()) {
      field.setAccessible(true);
      Object value = field.get(obj);

      if (value == null) {
        throw new IllegalArgumentException("字段 `" + field.getName() + "` 为 null");
      }

      if (value instanceof String str && str.isBlank()) {
        throw new IllegalArgumentException("字段 `" + field.getName() + "` 为空字符串");
      }

      if (value instanceof Iterable<?> iterable && !iterable.iterator().hasNext()) {
        throw new IllegalArgumentException("字段 `" + field.getName() + "` 是空集合");
      }

      // 递归校验嵌套对象
      if (!isPrimitiveOrWrapper(field.getType()) && !(value instanceof String)) {
        validateFields(value);
      }
    }
  }

  private static boolean isPrimitiveOrWrapper(Class<?> type) {
    return type.isPrimitive()
        || type == Boolean.class
        || type == Integer.class
        || type == Long.class
        || type == Double.class
        || type == Float.class
        || type == Short.class
        || type == Byte.class
        || type == Character.class;
  }
}
