package org.xiaoshuyui.automl.module.annotation;

import java.io.ByteArrayOutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import lombok.extern.slf4j.Slf4j;
import org.apache.http.HttpStatus;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.annotation.entity.AnnotationFileResponse;
import org.xiaoshuyui.automl.module.annotation.entity.NewAnnotationRequest;
import org.xiaoshuyui.automl.module.annotation.entity.UpdateAnnotationClassesRequest;
import org.xiaoshuyui.automl.module.annotation.entity.UpdateAnnotationPromptRequest;
import org.xiaoshuyui.automl.module.annotation.entity.UpdateAnnotationRequest;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.dataset.entity.request.GetFilePreviewRequest;
import org.xiaoshuyui.automl.module.dataset.entity.response.GetFileContentResponse;

@Slf4j
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
    String classes = annotation.getClassItems();
    if (classes == null || classes.isEmpty()) {
      response.setClasses(new ArrayList<>());
    } else {
      response.setClasses(Arrays.stream(classes.split(";")).toList());
    }

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

  @PostMapping("/{id}/append/files")
  public Result uploadMultipleFiles(
      @RequestParam("files") MultipartFile[] files, @PathVariable Long id) {
    var a = annotationService.getById(id);
    if (a == null) {
      return Result.error("annotation not found");
    }

    int errorCount = 0;
    for (MultipartFile file : files) {

      if (!file.isEmpty()) {
        String fileName = file.getOriginalFilename();

        String savePath = a.getAnnotationSavePath() + "/" + fileName;

        try {
          annotationService.putFileToDataset(savePath, file.getInputStream());
        } catch (Exception e) {
          log.error(e.getMessage());
          errorCount += 1;
        }
      }
    }
    return Result.OK_msg(errorCount + " files failed");
  }

  @GetMapping("/export/{id}")
  public ResponseEntity<byte[]> exportAnnotation(@PathVariable Long id) throws Exception {
    ByteArrayOutputStream zip = annotationService.exportS3Zip(id); // 上面的函数

    HttpHeaders headers = new HttpHeaders();
    headers.setContentType(MediaType.APPLICATION_OCTET_STREAM);
    String contentDisposition = "attachment; filename=\"annotation_" + id + ".zip\"";
    headers.set(HttpHeaders.CONTENT_DISPOSITION, contentDisposition);

    return new ResponseEntity<>(zip.toByteArray(), headers, HttpStatus.SC_OK);
  }

  @PostMapping("/new")
  public Result newAnnotation(@RequestBody NewAnnotationRequest entity) {
    annotationService.newAnnotation(entity);

    return Result.OK();
  }

  @GetMapping("/generate/details/{id}")
  public Result generateDetails(@PathVariable Long id) {
    annotationService.generateDetails(id);
    return Result.OK();
  }

  @GetMapping("/class/details/{id}")
  public Result getAnnotationClassDetails(@PathVariable Long id) {
    var annotation = annotationService.getById(id);
    if (annotation == null) {
      return Result.error("annotation not found");
    }

    return Result.OK_data(annotation.getDetails());
  }

  @PostMapping("/file/update")
  public Result updateAnnotationFile(@RequestBody UpdateAnnotationRequest entity) {

    int r = annotationService.updateAnnotationFile(entity.getAnnotationPath(), entity.getContent());
    if (r == 0) {
      return Result.OK();
    } else {
      return Result.error("更新失败");
    }
  }

  @PostMapping("/update/classes")
  public Result updateAnnotationClasses(@RequestBody UpdateAnnotationClassesRequest entity) {
    annotationService.updateAnnotationClasses(entity.getId(), entity.getClasses());
    return Result.OK();
  }

  @PostMapping("/update/prompt")
  public Result updatePrompt(@RequestBody UpdateAnnotationPromptRequest entity) {
    annotationService.updateAnnotationPrompt(entity.getPrompt(), entity.getAnnotationId());
    return Result.OK();
  }
}
