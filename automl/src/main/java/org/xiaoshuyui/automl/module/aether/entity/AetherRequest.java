package org.xiaoshuyui.automl.module.aether.entity;

import com.google.gson.annotations.SerializedName;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
public class AetherRequest<T> {
  String task;

  @SerializedName("model_id")
  Long modelId;

  Input input;
  Meta meta;
  T extra;

  @Data
  @AllArgsConstructor
  @NoArgsConstructor
  public static class Input {
    String data;

    @SerializedName("data_type")
    String dataType;
  }

  @Data
  public static class Meta {
    @SerializedName("task_id")
    Long taskId;

    boolean sync;
  }
}
