package org.xiaoshuyui.automl.module.dataset;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.dataset.entity.request.GetFilePreviewRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.ModifyDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.NewDatasetRequest;
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
            String s = datasetService.getFileContent(request.getBaseUrl(), request.getPath(), request.getStorageType());
            GetFileContentResponse response = new GetFileContentResponse();
            response.setContent(s);
            return Result.OK_data(response);
        } catch (Exception e) {
            log.error(e.getMessage());
        }

        return Result.error("get content failed");
    }
}
