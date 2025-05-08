package org.xiaoshuyui.automl.module.annotation;

import java.util.Arrays;
import org.springframework.web.bind.annotation.*;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.annotation.entity.AnnotationFileResponse;
import org.xiaoshuyui.automl.module.annotation.entity.NewAnnotationRequest;
import org.xiaoshuyui.automl.module.annotation.entity.UpdateAnnotationRequest;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.dataset.entity.request.GetFilePreviewRequest;
import org.xiaoshuyui.automl.module.dataset.entity.response.GetFileContentResponse;

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

  @GetMapping("/{id}")
  public Result getById(@PathVariable("id") Long id) {
    return Result.OK_data(annotationService.getById(id));
  }

  @GetMapping("/{id}/file/list")
  public Result getFileList(@PathVariable("id") Long id) {
    var annotation = annotationService.getById(id);
    if (annotation == null) {
      return Result.error("annotation not found");
    }
    AnnotationFileResponse response = new AnnotationFileResponse();
    response.setAnnotationId(id);
    response.setAnnotationPath(annotation.getAnnotationSavePath());
    response.setClasses(Arrays.stream(annotation.getClassItems().split(";")).toList());
    response.setStorageType(annotation.getStorageType());

    response.setFiles(annotationService.getFileList(annotation));
    return Result.OK_data(response);
  }

  @PostMapping("/content")
  public Result getAnnotationContent(@RequestBody GetFilePreviewRequest request) {
    try {
      GetFileContentResponse response = new GetFileContentResponse();
      response.setContent(annotationService.getAnnotationContent(request.getPath()));
      return Result.OK_data(response);
    } catch (Exception e) {
      return Result.error(e.getMessage());
    }
  }

  @PostMapping("/new")
  public Result newAnnotation(@RequestBody NewAnnotationRequest entity) {
    annotationService.newAnnotation(entity);

    return Result.OK();
  }

  @PostMapping("/file/update")
  public Result updateAnnotationFile(@RequestBody UpdateAnnotationRequest entity) {

    int r = annotationService.updateAnnotationFile(entity.getAnnotationPath(),
        entity.getContent());
    if (r == 0) {
      return Result.OK();
    } else {
      return Result.error("更新失败");
    }
  }
}
