package org.xiaoshuyui.automl.module.tool.entity;

import com.google.gson.annotations.SerializedName;
import java.util.UUID;
import lombok.Data;

@Data
public class DatasetAggregateAnalysis {

  private String id = UUID.randomUUID().toString();

  @SerializedName("image_stats")
  private ImageStatsSummary imageStats;

  @SerializedName("object_stats")
  private ObjectStatsSummary objectStats;

  @SerializedName("yolo_recommendation")
  private YoloModelRecommendation yoloRecommendation;

  @Data
  public static class ImageStatsSummary {
    @SerializedName("total_images")
    private int totalImages;

    @SerializedName("annotated_images")
    private int annotatedImages;

    @SerializedName("image_only")
    private int imageOnly;

    @SerializedName("label_only")
    private int labelOnly;
  }

  @Data
  public static class ObjectStatsSummary {
    @SerializedName("total_objects")
    private int totalObjects;

    @SerializedName("small_objects")
    private int smallObjects;

    @SerializedName("medium_objects")
    private int mediumObjects;

    @SerializedName("large_objects")
    private int largeObjects;

    @SerializedName("average_objects_per_image")
    private float averageObjectsPerImage;
  }

  @Data
  public static class YoloModelRecommendation {
    @SerializedName("suggested_model")
    private String suggestedModel;

    @SerializedName("rationale")
    private String rationale;

    @SerializedName("tiling_recommended")
    private boolean tilingRecommended;

    @SerializedName("tiling_strategy")
    private String tilingStrategy; // optional
  }
}
