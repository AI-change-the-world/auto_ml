package org.xiaoshuyui.automl.module.dataset.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.annotation.Resource;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.dataset.entity.Dataset;
import org.xiaoshuyui.automl.module.dataset.entity.request.ModifyDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.NewDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.response.DatasetDetailsResponse;
import org.xiaoshuyui.automl.module.dataset.mapper.DatasetMapper;
import org.xiaoshuyui.automl.util.GetFileListUtil;
import org.xiaoshuyui.automl.util.LocalImageDelegate;

@Slf4j
@Service
public class DatasetService {

  private final DatasetMapper datasetMapper;

  public DatasetService(DatasetMapper datasetMapper) {
    this.datasetMapper = datasetMapper;
  }

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

  @Resource LocalImageDelegate localImageDelegate;

  public String getFileContent(String datasetBaseUrl, String path, int storageType)
      throws Exception {
    if (storageType == 0) {
      String p = datasetBaseUrl;
      if (!p.endsWith("/")) {
        p = p + "/";
      }
      p = p + path;
      return localImageDelegate.getFile(p);
    }
    // todo unimplemented
    return null;
  }

  public String getFileContentUnCompress(String datasetBaseUrl, String path, int storageType)
      throws Exception {
    if (storageType == 0) {
      String p = datasetBaseUrl;
      if (!p.endsWith("/")) {
        p = p + "/";
      }
      p = p + path;
      return localImageDelegate.getFileUnCompress(p);
    }
    // todo unimplemented
    return null;
  }

  ///  only one level folder
  ///
  /// todo: exception handling
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

  private void scanFolderParallel(Dataset dataset) {
    Thread thread =
        new Thread(
            () -> {
              scanFolderSync(dataset);
            });
    thread.start();
  }
}
