package org.xiaoshuyui.automl.module.dataset.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.xiaoshuyui.automl.module.dataset.entity.Dataset;
import org.xiaoshuyui.automl.module.dataset.entity.DatasetStorage;
import org.xiaoshuyui.automl.module.dataset.entity.request.ModifyDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.NewDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.mapper.DatasetMapper;
import org.xiaoshuyui.automl.module.dataset.mapper.DatasetStorageMapper;

@Service
public class DatasetService {

    private final DatasetMapper datasetMapper;

    private final DatasetStorageMapper datasetStorageMapper;

    public DatasetService(DatasetMapper datasetMapper, DatasetStorageMapper datasetStorageMapper) {
        this.datasetMapper = datasetMapper;
        this.datasetStorageMapper = datasetStorageMapper;
    }

    @Transactional
    public void newDataset(NewDatasetRequest request){
        Dataset dataset = new Dataset();
        dataset.setName(request.getName());
        dataset.setDescription(request.getDescription());
        DatasetStorage datasetStorage = new DatasetStorage();
        datasetStorage.setStorageType(request.getStorageType());
        datasetStorage.setUrl(request.getUrl());
        datasetStorage.setUsername(request.getUsername());
        datasetStorage.setPassword(request.getPassword());

        datasetMapper.insert(dataset);
        datasetStorage.setId(dataset.getId());
        datasetStorageMapper.insert(datasetStorage);
    }

    @Transactional
    public void modifyDataset(ModifyDatasetRequest request){
        Dataset dataset = new Dataset();
        dataset.setId(request.getId());
        dataset.setName(request.getName());
        dataset.setDescription(request.getDescription());
        datasetMapper.updateById(dataset);
        DatasetStorage datasetStorage = new DatasetStorage();
        datasetStorage.setId(request.getId());
        datasetStorage.setStorageType(request.getStorageType());
        datasetStorage.setUrl(request.getUrl());
        datasetStorage.setUsername(request.getUsername());
        datasetStorage.setPassword(request.getPassword());
        datasetStorageMapper.updateById(datasetStorage);
    }
}
