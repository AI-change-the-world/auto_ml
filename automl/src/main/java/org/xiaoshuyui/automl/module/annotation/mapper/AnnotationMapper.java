package org.xiaoshuyui.automl.module.annotation.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;

import java.util.List;

public interface AnnotationMapper extends BaseMapper<Annotation> {
    List<Annotation> getAnnotationsByDatasetId(Long datasetId);
}
