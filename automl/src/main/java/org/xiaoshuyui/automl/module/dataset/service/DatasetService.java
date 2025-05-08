package org.xiaoshuyui.automl.module.dataset.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.annotation.Resource;
import java.io.InputStream;
import java.util.List;
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

  @Resource private S3ConfigProperties properties;

  public long newDataset(NewDatasetRequest request) {
    Dataset dataset = new Dataset();
    dataset.setName(request.getName());
    dataset.setDescription(request.getDescription());
    dataset.setRanking(request.getRanking());
    dataset.setStorageType(request.getStorageType());
    dataset.setUrl(request.getUrl());
    dataset.setUsername(request.getUsername());
    dataset.setPassword(request.getPassword());

    datasetMapper.insert(dataset);
    dataset.setId(dataset.getId());

    this.scanFolderParallel(dataset);
    return dataset.getId();
  }

  public void putFileToDataset(String path, InputStream inputStream) throws Exception {
    s3FileDelegate.putFile(path, inputStream, properties.getDatasetsBucketName());
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
          List<String> targets =
              s3FileDelegate.putFileList(l, properties.getDatasetsBucketName(), basePath);
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
    Thread thread =
        new Thread(
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
      int fileCount =
          s3FileDelegate
              .listFiles(dataset.getLocalS3StoragePath(), properties.getDatasetsBucketName())
              .size();
      dataset.setFileCount((long) fileCount);
      datasetMapper.updateById(dataset);
    } catch (Exception e) {
      e.printStackTrace();
      log.error("update count error: {}", e.getMessage());
    }
  }
}
