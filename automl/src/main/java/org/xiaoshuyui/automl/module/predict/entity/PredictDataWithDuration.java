package org.xiaoshuyui.automl.module.predict.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class PredictDataWithDuration {
    LocalDateTime createdAt;
    String presignUrl;

    public boolean isExpired() {
        return createdAt.plusSeconds(60 * 59).isBefore(LocalDateTime.now());
    }

    public void refresh(String presignUrl){
        this.presignUrl = presignUrl;
        this.createdAt = LocalDateTime.now();
    }
}
