package org.xiaoshuyui.automl.module.annotation.service;

import java.util.List;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;
import org.xiaoshuyui.automl.module.annotation.mapper.AnnotationFileMapper;
import org.xiaoshuyui.automl.module.annotation.mapper.AnnotationMapper;

@Service
public class AnnotationService {
  final AnnotationFileMapper annotationFileMapper;

  final AnnotationMapper annotationMapper;

  public AnnotationService(
      AnnotationFileMapper annotationFileMapper, AnnotationMapper annotationMapper) {
    this.annotationFileMapper = annotationFileMapper;
    this.annotationMapper = annotationMapper;
  }

  public Annotation getById(Long id) {
    return annotationMapper.selectById(id);
  }

  public List<Annotation> getAnnotationsByDatasetId(Long datasetId) {
    return annotationMapper.getAnnotationsByDatasetId(datasetId);
  }
}
