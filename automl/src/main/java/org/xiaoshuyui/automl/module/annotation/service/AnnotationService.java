package org.xiaoshuyui.automl.module.annotation.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import jakarta.annotation.Resource;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.xiaoshuyui.automl.config.S3ConfigProperties;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;
import org.xiaoshuyui.automl.module.annotation.entity.AnnotationDetails;
import org.xiaoshuyui.automl.module.annotation.entity.AnnotationDetails.CountMap;
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

  public ByteArrayOutputStream exportS3Zip(Long annotationId) throws Exception {
    Annotation annotation = annotationMapper.selectById(annotationId);
    if (annotation == null) {
      throw new IllegalArgumentException("Annotation not found with id: " + annotationId);
    }

    List<String> fileList =
        s3FileDelegate.listFiles(
            annotation.getAnnotationSavePath(), properties.getDatasetsBucketName());
    if (fileList.isEmpty()) {
      throw new IllegalArgumentException("No files found in the annotation.");
    }
    ByteArrayOutputStream zipOut = new ByteArrayOutputStream();
    try (ZipOutputStream zos = new ZipOutputStream(zipOut)) {
      for (String filePath : fileList) {
        InputStream is =
            s3FileDelegate.getFileStream(filePath, properties.getDatasetsBucketName()); // 获取文件流
        String prefix = filePath.substring(0, filePath.lastIndexOf("/"));
        ZipEntry entry = new ZipEntry(filePath.replaceFirst(prefix, ""));
        zos.putNextEntry(entry);
        is.transferTo(zos); // 写入压缩包
        zos.closeEntry();
      }
    }

    return zipOut;
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

  private static Gson gson =
      new GsonBuilder()
          .serializeNulls() // 👈 关键：保留 null 字段
          .create();

  public void generateDetails(Long id) {
    Annotation annotation = annotationMapper.selectById(id);
    if (annotation == null) {
      log.error("Annotation not found with id: {}", id);
      return;
    }

    var thread =
        new Thread(
            () -> {
              AnnotationDetails details = new AnnotationDetails();
              Map<String, Integer> results = new HashMap();
              try {
                List<String> files =
                    s3FileDelegate.listFiles(
                        annotation.getAnnotationSavePath(), properties.getDatasetsBucketName());
                details.setFileCount((long) files.size());

                if (annotation.getAnnotationType() == 0) {
                  for (var str : files) {
                    String content =
                        s3FileDelegate.getFileContent(str, properties.getDatasetsBucketName());
                    List<String> subStrings = List.of(content.split("\n"));
                    if (subStrings.size() != 2) {
                      continue;
                    }
                    if (results.get(subStrings.get(1)) != null) {
                      results.put(subStrings.get(1), results.get(subStrings.get(1)) + 1);
                    } else {
                      results.put(subStrings.get(1), 1);
                    }
                  }
                } else if (annotation.getAnnotationType() == 1) {
                  List<String> classes = List.of(annotation.getClassItems().split(";"));
                  for (var str : files) {

                    String content =
                        s3FileDelegate.getFileContent(str, properties.getDatasetsBucketName());
                    if (content.length() == 0) continue;
                    List<String> subStrings = List.of(content.split("\n"));
                    for (var a : subStrings) {
                      String sub = List.of(a.split(" ")).get(0);
                      Integer i = Integer.parseInt(sub);
                      String classname = classes.get(i);

                      if (results.get(classname) != null) {
                        results.put(classname, results.get(classname) + 1);
                      } else {
                        results.put(classname, 1);
                      }
                    }
                  }
                }

              } catch (Exception e) {
                e.printStackTrace();
                log.error("Error listing files for annotation {}: {}", id, e.getMessage());
              }
              List<CountMap> labelCountMap = new ArrayList<>();
              for (var entry : results.entrySet()) {
                CountMap countMap = new CountMap();
                countMap.setName(entry.getKey());
                countMap.setCount((long) entry.getValue());
                labelCountMap.add(countMap);
              }
              details.setLabelCountMap(labelCountMap);
              annotation.setDetails(gson.toJson(details));
            });

    thread.start();
  }

  public Long getAnnotationCountByDatasetId(Long datasetId) {
    QueryWrapper queryWrapper = new QueryWrapper();
    queryWrapper.eq("dataset_id", datasetId);
    return annotationMapper.selectCount(queryWrapper);
  }
}
