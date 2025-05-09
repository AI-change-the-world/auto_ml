package org.xiaoshuyui.automl.module.aether.entity;

import com.google.gson.annotations.SerializedName;
import lombok.Data;

@Data
public class AetherResponse<T> {
  boolean success;
  T output;
  Meta meta;

  @Data
  public static class Meta {
    @SerializedName("time_cost_ms")
    int timeCostMs;

    @SerializedName("task_id")
    Long taskId;
  }

  String error;
}
