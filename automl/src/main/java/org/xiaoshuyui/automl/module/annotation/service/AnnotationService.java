package org.xiaoshuyui.automl.module.annotation.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.annotation.Resource;
import java.io.InputStream;
import java.util.List;
import java.util.UUID;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.xiaoshuyui.automl.config.S3ConfigProperties;
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

  @Resource private S3ConfigProperties properties;

  public Annotation getById(Long id) {
    return annotationMapper.selectById(id);
  }

  public List<Annotation> getAnnotationsByDatasetId(Long datasetId) {
    return annotationMapper.getAnnotationsByDatasetId(datasetId);
  }

  public List<String> getFileList(Annotation annotation) {
    try {
      return s3FileDelegate.listFiles(
          annotation.getAnnotationSavePath(), properties.getDatasetsBucketName());
    } catch (Exception e) {
      log.error("get file list error: {}", e.getMessage());
      return null;
    }
  }

  public int updateAnnotationFile(String annotationPath, String content) {
    try {
      s3FileDelegate.putFile(annotationPath, content, properties.getDatasetsBucketName());
      return 0;
    } catch (Exception e) {
      log.error("update annotation file error: {}", e.getMessage());
      return 1;
    }
  }

  public String getAnnotationContent(String path) {
    try {
      return s3FileDelegate.getFileContent(path, properties.getDatasetsBucketName());
    } catch (Exception e) {
      log.error("get file content error: {}", e.getMessage());
      return null;
    }
  }

  public void putFileToDataset(String path, InputStream inputStream) throws Exception {
    s3FileDelegate.putFile(path, inputStream, properties.getDatasetsBucketName());
  }

  public Long newAnnotation(NewAnnotationRequest request) {
    Annotation annotation = new Annotation();
    annotation.setDatasetId(request.getDatasetId());
    annotation.setStorageType(request.getStorageType());
    annotation.setAnnotationPath(request.getSavePath());
    annotation.setAnnotationType(request.getType());
    annotation.setClassItems(request.getClasses());
    QueryWrapper<Annotation> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("annotation_save_path", annotation.getAnnotationPath());
    Long count = annotationMapper.selectCount(queryWrapper);

    if (request.getStorageType() == 0) {
      // create annotation save path
      String p;
      if (request.getSavePath() != null && !request.getSavePath().isEmpty() && count == 0) {
        p = "/annotation/" + request.getSavePath();
      } else {
        p = "/annotation/" + UUID.randomUUID() + "/";
      }

      s3FileDelegate.createDir(p, properties.getDatasetsBucketName());
      annotation.setAnnotationSavePath(p);
    }

    annotationMapper.insert(annotation);

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
      s3FileDelegate.createDir(basePath, properties.getDatasetsBucketName());
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
          s3FileDelegate.putFileList(l, properties.getDatasetsBucketName(), basePath);
        }

        annotationMapper.updateById(annotation);
      } catch (Exception e) {
        log.error("scan folder error: {}", e.getMessage());
      }
    }
  }

  @Transactional
  public void updateAnnotationClasses(Long id, String classes) {
    Annotation annotation = annotationMapper.selectById(id);
    annotation.setClassItems(classes);
    annotationMapper.updateById(annotation);
  }

  public void updateAnnotationPrompt(String prompt, Long id) {
    Annotation annotation = annotationMapper.selectById(id);
    annotation.setPrompt(prompt);
    annotationMapper.updateById(annotation);
  }
}
