package org.xiaoshuyui.automl.module.annotation.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.annotation.entity.AnnotationFile;
import org.xiaoshuyui.automl.module.annotation.mapper.AnnotationFileMapper;

@Deprecated
@Service
public class AnnotationFileServiceImpl extends ServiceImpl<AnnotationFileMapper, AnnotationFile> implements AnnotationFileService {

    final AnnotationFileMapper annotationFileMapper;

    public AnnotationFileServiceImpl(AnnotationFileMapper annotationFileMapper) {
        this.annotationFileMapper = annotationFileMapper;
    }

    public void saveSingle(AnnotationFile annotationFile) {
        annotationFileMapper.insert(annotationFile);
    }
}
