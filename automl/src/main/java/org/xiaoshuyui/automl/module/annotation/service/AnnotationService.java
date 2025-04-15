package org.xiaoshuyui.automl.module.annotation.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;
import org.xiaoshuyui.automl.module.annotation.mapper.AnnotationFileMapper;
import org.xiaoshuyui.automl.module.annotation.mapper.AnnotationMapper;

import java.util.List;

@Service
public class AnnotationService {
    final AnnotationFileMapper annotationFileMapper;

    final AnnotationMapper annotationMapper;

    public AnnotationService(AnnotationFileMapper annotationFileMapper, AnnotationMapper annotationMapper) {
        this.annotationFileMapper = annotationFileMapper;
        this.annotationMapper = annotationMapper;
    }

    Annotation getById(Long id) {
        Annotation annotation = annotationMapper.selectById(id);
        if (annotation == null) {
            return null;
        }
        QueryWrapper queryWrapper = new QueryWrapper();
        queryWrapper.eq("annotation_id", id);
        Long count = annotationFileMapper.selectCount(queryWrapper);
        annotation.setAnnotatedFileCount(count);
        return annotation;
    }

    public List<Annotation> getAnnotationsByDatasetId(Long datasetId) {
        return annotationMapper.getAnnotationsByDatasetId(datasetId);
    }
}
