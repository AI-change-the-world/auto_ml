package org.xiaoshuyui.automl.module.dataset.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.annotation.Resource;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.List;
import java.util.UUID;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.config.S3ConfigProperties;
import org.xiaoshuyui.automl.module.dataset.entity.Dataset;
import org.xiaoshuyui.automl.module.dataset.entity.request.ModifyDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.NewDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.response.DatasetDetailsResponse;
import org.xiaoshuyui.automl.module.dataset.mapper.DatasetMapper;
import org.xiaoshuyui.automl.util.GetFileListUtil;
import org.xiaoshuyui.automl.util.S3FileDelegate;

@Slf4j
@Service
public class DatasetService {

  private final DatasetMapper datasetMapper;
  private final S3FileDelegate s3FileDelegate;

  public DatasetService(DatasetMapper datasetMapper, S3FileDelegate s3FileDelegate) {
    this.datasetMapper = datasetMapper;
    this.s3FileDelegate = s3FileDelegate;
  }

  @Resource
  private S3ConfigProperties properties;

  public long newDataset(NewDatasetRequest request) {
    Dataset dataset = new Dataset();
    dataset.setName(request.getName());
    dataset.setDescription(request.getDescription());
    dataset.setRanking(request.getRanking());
    dataset.setStorageType(request.getStorageType());
    dataset.setUrl(request.getUrl());
    dataset.setUsername(request.getUsername());
    dataset.setPassword(request.getPassword());
    if (request.getStorageType() == 0) {
      // 创建s3目录
      String p = "/dataset/" + UUID.randomUUID() + "/";
      s3FileDelegate.createDir(p, properties.getDatasetsBucketName());
      dataset.setLocalS3StoragePath(p);
      dataset.setScanStatus(3);
    }

    datasetMapper.insert(dataset);

    // this.scanFolderParallel(dataset);
    return dataset.getId();
  }

  public void updateDataset(Dataset dataset) {
    datasetMapper.updateById(dataset);
  }

  public void putFileToDataset(String path, InputStream inputStream) throws Exception {
    s3FileDelegate.putFile(path, inputStream, properties.getDatasetsBucketName());
  }

  public ByteArrayOutputStream exportS3Zip(Long datasetId) throws Exception {
    Dataset dataset = datasetMapper.selectById(datasetId);
    if (dataset == null) {
      throw new IllegalArgumentException("Dataset not found with id: " + datasetId);
    }

    List<String> fileList = s3FileDelegate.listFiles(dataset.getLocalS3StoragePath(),
        properties.getDatasetsBucketName());
    if (fileList.isEmpty()) {
      throw new IllegalArgumentException("No files found in the dataset.");
    }
    ByteArrayOutputStream zipOut = new ByteArrayOutputStream();
    try (ZipOutputStream zos = new ZipOutputStream(zipOut)) {
      for (String filePath : fileList) {
        InputStream is = s3FileDelegate.getFileStream(filePath, properties.getDatasetsBucketName()); // 获取文件流
        String prefix = filePath.substring(0, filePath.lastIndexOf("/"));
        ZipEntry entry = new ZipEntry(filePath.replaceFirst(prefix, ""));
        zos.putNextEntry(entry);
        is.transferTo(zos); // 写入压缩包
        zos.closeEntry();
      }
    }

    return zipOut;
  }

  public void modifyDataset(ModifyDatasetRequest request) {
    Dataset dataset = new Dataset();
    dataset.setId(request.getId());
    dataset.setName(request.getName());
    dataset.setDescription(request.getDescription());
    dataset.setRanking(request.getRanking());
    dataset.setId(request.getId());
    dataset.setStorageType(request.getStorageType());
    dataset.setUrl(request.getUrl());
    dataset.setUsername(request.getUsername());
    dataset.setPassword(request.getPassword());
    datasetMapper.updateById(dataset);
  }

  public List<String> getFileList(Dataset dataset) {
    try {
      return s3FileDelegate.listFiles(
          dataset.getLocalS3StoragePath(), properties.getDatasetsBucketName());
    } catch (Exception e) {
      log.error("get file list error: {}", e.getMessage());
      return null;
    }
  }

  public List<Dataset> getDataset() {
    QueryWrapper queryWrapper = new QueryWrapper();
    queryWrapper.eq("is_deleted", 0);
    return datasetMapper.selectList(queryWrapper);
  }

  public void deleteById(Long id) {
    Dataset dataset = datasetMapper.selectOne(new QueryWrapper<Dataset>().eq("dataset_id", id));
    dataset.setIsDeleted(1);
    datasetMapper.updateById(dataset);
  }

  public Dataset get(Long id) {
    return datasetMapper.selectOne(new QueryWrapper<Dataset>().eq("dataset_id", id));
  }

  public DatasetDetailsResponse getDetails(Long id) {
    Dataset dataset = get(id);
    DatasetDetailsResponse response = new DatasetDetailsResponse();
    if (dataset.getScanStatus() == 1) {
      response.setSamplePath(dataset.getSampleFilePath());
    }
    response.setStatus(dataset.getScanStatus());
    response.setCount(dataset.getFileCount());
    return response;
  }

  public String getFileContent(String path, int storageType) throws Exception {
    return s3FileDelegate.getFile(path, properties.getDatasetsBucketName());
  }

  /// only one level folder
  ///
  /// todo: exception handling
  @Deprecated(since = "use `scanAndUploadToLocalS3FolderSync` instead")
  private void scanFolderSync(Dataset storage) {
    if (storage.getUrl() == null) {
      return;
    }
    if (storage.getStorageType() == 0) {
      try {
        List<String> l = GetFileListUtil.getFileList(storage.getUrl(), storage.getStorageType());
        if (!l.isEmpty()) {
          storage.setFileCount((long) l.size());
          storage.setSampleFilePath(l.get(0));
        }
        storage.setScanStatus(1);
        datasetMapper.updateById(storage);
      } catch (Exception e) {
        storage.setScanStatus(2);
        datasetMapper.updateById(storage);
        log.error("scan folder error: {}", e.getMessage());
      }
    }
  }

  private void scanAndUploadToLocalS3FolderSync(Dataset storage) {
    if (storage.getUrl() == null) {
      return;
    }
    if (storage.getStorageType() == 0) {
      try {
        List<String> l = GetFileListUtil.getFileList(storage.getUrl(), storage.getStorageType());

        if (!l.isEmpty()) {
          String uuid = java.util.UUID.randomUUID().toString();
          String basePath = "/dataset/" + uuid + "/";
          storage.setFileCount((long) l.size());
          storage.setLocalS3StoragePath(basePath);
          log.info("files: {}", l);
          List<String> targets = s3FileDelegate.putFileList(l, properties.getDatasetsBucketName(), basePath);
          storage.setSampleFilePath(targets.get(0));
        }
        storage.setScanStatus(1);
        datasetMapper.updateById(storage);
      } catch (Exception e) {
        storage.setScanStatus(2);
        datasetMapper.updateById(storage);
        log.error("scan folder error: {}", e.getMessage());
      }
    }
  }

  private void scanFolderParallel(Dataset dataset) {
    Thread thread = new Thread(
        () -> {
          scanAndUploadToLocalS3FolderSync(dataset);
        });
    thread.start();
  }

  public void updateCount(Long id) {
    Dataset dataset = datasetMapper.selectById(id);
    if (dataset == null) {
      return;
    }
    try {
      int fileCount = s3FileDelegate
          .listFiles(dataset.getLocalS3StoragePath(), properties.getDatasetsBucketName())
          .size();
      dataset.setFileCount((long) fileCount);
      datasetMapper.updateById(dataset);
    } catch (Exception e) {
      e.printStackTrace();
      log.error("update count error: {}", e.getMessage());
    }
  }

  public Dataset findDatasetByDataPath(String path) {
    if (path == null || path.isEmpty()) {
      return null;
    }

    var datasetName = removeFilenameIfHasExtension(path);

    log.info("datasetName: {}", datasetName);

    if (datasetName == null || datasetName.isEmpty()) {
      return null;
    }
    return datasetMapper.selectOne(
        new QueryWrapper<Dataset>().like("local_s3_storage_path", datasetName));
  }

  public static String removeFilenameIfHasExtension(String path) {
    if (path == null || path.isEmpty())
      return path;

    // 去掉结尾的 `/`，避免误判目录
    String cleanPath = path.endsWith("/") ? path.substring(0, path.length() - 1) : path;

    int lastSlash = cleanPath.lastIndexOf('/');
    if (lastSlash == -1)
      return path;

    String lastSegment = cleanPath.substring(lastSlash + 1);

    // 如果最后一段包含“.”，且不是以“.”开头，认为是文件名
    if (lastSegment.contains(".") && !lastSegment.startsWith(".")) {
      return cleanPath.substring(0, lastSlash);
    }

    return path;
  }
}
