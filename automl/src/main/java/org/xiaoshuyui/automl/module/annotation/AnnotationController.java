package org.xiaoshuyui.automl.module.annotation;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;

@RestController
@RequestMapping("/annotation")
public class AnnotationController {

    final AnnotationService annotationService;

    public AnnotationController(AnnotationService annotationService) {
        this.annotationService = annotationService;
    }

    @GetMapping("/list/{datasetId}")
    public Result getByDatasetId(@PathVariable("datasetId") Long datasetId) {
        return Result.OK_data(annotationService.getAnnotationsByDatasetId(datasetId));
    }
}
