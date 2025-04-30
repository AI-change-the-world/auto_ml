package org.xiaoshuyui.automl.module.annotation;

import jakarta.annotation.Resource;
import java.util.Arrays;
import org.springframework.web.bind.annotation.*;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.annotation.entity.AnnotationFileResponse;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.dataset.entity.request.GetFilePreviewRequest;
import org.xiaoshuyui.automl.module.dataset.entity.response.GetFileContentResponse;
import org.xiaoshuyui.automl.util.GetFileListUtil;
import org.xiaoshuyui.automl.util.LocalAnnotationDelegate;

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
    response.setAnnotationPath(annotation.getAnnotationPath());
    response.setClasses(Arrays.stream(annotation.getClassItems().split(";")).toList());
    response.setStorageType(annotation.getStorageType());

    response.setFiles(
        GetFileListUtil.getFileList(annotation.getAnnotationPath(), annotation.getStorageType()));
    return Result.OK_data(response);
  }

  @Resource private LocalAnnotationDelegate fileDelegate;

  @PostMapping("/content")
  public Result getAnnotationContent(@RequestBody GetFilePreviewRequest request) {
    try {
      ///  TODO s3
      GetFileContentResponse response = new GetFileContentResponse();
      response.setContent(fileDelegate.getFile(request.getBaseUrl() + "/" + request.getPath()));
      return Result.OK_data(response);
    } catch (Exception e) {
      return Result.error(e.getMessage());
    }
  }
}
