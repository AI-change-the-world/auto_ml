package org.xiaoshuyui.automl.module.annotation.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import java.util.List;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;

public interface AnnotationMapper extends BaseMapper<Annotation> {
  List<Annotation> getAnnotationsByDatasetId(Long datasetId);
}
