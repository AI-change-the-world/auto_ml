package org.xiaoshuyui.automl.common;

import lombok.Data;

@Data
public class SseResponse<T> {
  T data;
  String message;
  String status;
  boolean isDone;
}
