package org.xiaoshuyui.automl.module.dataset;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.dataset.entity.request.ModifyDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.NewDatasetRequest;
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
        datasetService.newDataset(request);
        return Result.OK();
    }

    @PostMapping("/modify")
    public Result modifyDataset(@RequestBody ModifyDatasetRequest request) {
        datasetService.modifyDataset(request);
        return Result.OK();
    }
}
