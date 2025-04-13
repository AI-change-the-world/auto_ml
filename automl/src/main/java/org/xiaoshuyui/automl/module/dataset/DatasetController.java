package org.xiaoshuyui.automl.module.dataset;

import org.springframework.web.bind.annotation.*;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.dataset.entity.request.ModifyDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.NewDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.NewDatasetResponse;
import org.xiaoshuyui.automl.module.dataset.service.DatasetService;

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

    @GetMapping("/storage/{id}")
    public Result getStorage(@PathVariable Long id) {
        return Result.OK_data(datasetService.getDatasetStorage(id));
    }
}
