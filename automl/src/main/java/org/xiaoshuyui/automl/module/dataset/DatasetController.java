package org.xiaoshuyui.automl.module.dataset;

import java.util.List;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.dataset.entity.request.GetFilePreviewRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.ModifyDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.NewDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.response.DatasetFileListResponse;
import org.xiaoshuyui.automl.module.dataset.entity.response.GetFileContentResponse;
import org.xiaoshuyui.automl.module.dataset.entity.response.NewDatasetResponse;
import org.xiaoshuyui.automl.module.dataset.service.DatasetService;

@Slf4j
@RestController
@RequestMapping("/dataset")
public class DatasetController {

  DatasetService datasetService;

  public DatasetController(DatasetService datasetService) {
    this.datasetService = datasetService;
  }

  @PostMapping("/new")
  public Result newDataset(@RequestBody NewDatasetRequest request) {
    var id = datasetService.newDataset(request);
    NewDatasetResponse newDatasetResponse = new NewDatasetResponse();
    newDatasetResponse.setId(id);
    return Result.OK_data(newDatasetResponse);
  }

  @PostMapping("/modify")
  public Result modifyDataset(@RequestBody ModifyDatasetRequest request) {
    datasetService.modifyDataset(request);
    return Result.OK();
  }

  @GetMapping("/list")
  public Result getDataset() {
    return Result.OK_data(datasetService.getDataset());
  }

  @GetMapping("/delete/{id}")
  public Result deleteDataset(@PathVariable Long id) {
    datasetService.deleteById(id);
    return Result.OK();
  }

  @GetMapping("/details/{id}")
  public Result getDetails(@PathVariable Long id) {
    return Result.OK_data(datasetService.get(id));
  }

  @PostMapping("/file/preview")
  public Result previewFile(@RequestBody GetFilePreviewRequest request) {
    try {
      String s = datasetService.getFileContent(
          request.getPath(), request.getStorageType());
      GetFileContentResponse response = new GetFileContentResponse();
      response.setContent(s);
      return Result.OK_data(response);
    } catch (Exception e) {
      log.error(e.getMessage());
    }

    return Result.error("get content failed");
  }

  @GetMapping("/{id}/file/list")
  public Result getFileList(@PathVariable Long id) {
    var dataset = datasetService.get(id);
    if (dataset == null) {
      return Result.error("dataset not found");
    }
    DatasetFileListResponse response = new DatasetFileListResponse();
    response.setDatasetId(id);
    response.setCount(dataset.getFileCount());
    response.setDatasetType(dataset.getType());
    response.setStorageType(dataset.getStorageType());
    response.setDatasetBaseUrl(dataset.getUrl());
    List<String> files = datasetService.getFileList(dataset);

    // List<String> files = GetFileListUtil.getFileList(dataset.getUrl(),
    // dataset.getStorageType());
    response.setFiles(files);
    return Result.OK_data(response);
  }

}
