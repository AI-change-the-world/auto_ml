package org.xiaoshuyui.automl.module.annotation.service;

import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;
import org.xiaoshuyui.automl.module.annotation.entity.NewAnnotationRequest;
import org.xiaoshuyui.automl.module.annotation.mapper.AnnotationMapper;
import org.xiaoshuyui.automl.util.GetFileListUtil;
import org.xiaoshuyui.automl.util.S3FileDelegate;

@Service
@Slf4j
public class AnnotationService {
  private final S3FileDelegate s3FileDelegate;

  final AnnotationMapper annotationMapper;

  public AnnotationService(S3FileDelegate s3FileDelegate, AnnotationMapper annotationMapper) {
    this.s3FileDelegate = s3FileDelegate;
    this.annotationMapper = annotationMapper;
  }

  public Annotation getById(Long id) {
    return annotationMapper.selectById(id);
  }

  public List<Annotation> getAnnotationsByDatasetId(Long datasetId) {
    return annotationMapper.getAnnotationsByDatasetId(datasetId);
  }

  public List<String> getFileList(Annotation annotation) {
    try {
      return s3FileDelegate.listFiles(annotation.getAnnotationSavePath());
    } catch (Exception e) {
      log.error("get file list error: {}", e.getMessage());
      return null;
    }
  }

  public String getAnnotationContent(String path) {
    try {
      return s3FileDelegate.getFileContent(path);
    } catch (Exception e) {
      log.error("get file content error: {}", e.getMessage());
      return null;
    }
  }

  public Long newAnnotation(NewAnnotationRequest request) {
    Annotation annotation = new Annotation();
    annotation.setDatasetId(request.getDatasetId());
    annotation.setStorageType(request.getStorageType());
    annotation.setAnnotationPath(request.getSavePath());
    annotation.setAnnotationType(request.getType());
    annotation.setClassItems(request.getClasses());

    annotationMapper.insert(annotation);

    scanFolderParallel(annotation);
    return annotation.getId();
  }

  private void scanFolderParallel(Annotation annotation) {
    Thread thread =
        new Thread(
            () -> {
              scanAndUploadToLocalS3FolderSync(annotation);
            });
    thread.start();
  }

  private void scanAndUploadToLocalS3FolderSync(Annotation annotation) {
    String uuid = java.util.UUID.randomUUID().toString();
    String basePath = "/annotation/" + uuid + "/";
    if (annotation.getAnnotationPath() == null) {
      log.info("annotation path is null, create empty folder");
      s3FileDelegate.createDir(basePath, null);
      annotation.setAnnotationSavePath(basePath);
      annotationMapper.updateById(annotation);
      return;
    }
    if (annotation.getStorageType() == 0) {
      try {
        List<String> l =
            GetFileListUtil.getFileList(
                annotation.getAnnotationPath(), annotation.getStorageType());

        if (!l.isEmpty()) {

          annotation.setAnnotationSavePath(basePath);
          log.info("files: {}", l);
          s3FileDelegate.putFileList(l, null, basePath);
        }

        annotationMapper.updateById(annotation);
      } catch (Exception e) {
        log.error("scan folder error: {}", e.getMessage());
      }
    }
  }
}
