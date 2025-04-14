package org.xiaoshuyui.automl.module.dataset.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationFileServiceImpl;
import org.xiaoshuyui.automl.module.dataset.entity.Dataset;
import org.xiaoshuyui.automl.module.dataset.entity.DatasetStorage;
import org.xiaoshuyui.automl.module.dataset.entity.request.ModifyDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.entity.request.NewDatasetRequest;
import org.xiaoshuyui.automl.module.dataset.mapper.DatasetMapper;
import org.xiaoshuyui.automl.module.dataset.mapper.DatasetStorageMapper;

import java.util.List;

@Service
public class DatasetService {

    private final DatasetMapper datasetMapper;

    private final DatasetStorageMapper datasetStorageMapper;

    private final AnnotationFileServiceImpl annotationFileService;

    public DatasetService(DatasetMapper datasetMapper, DatasetStorageMapper datasetStorageMapper, AnnotationFileServiceImpl annotationFileService) {
        this.datasetMapper = datasetMapper;
        this.datasetStorageMapper = datasetStorageMapper;
        this.annotationFileService = annotationFileService;
    }

    @Transactional
    public long newDataset(NewDatasetRequest request) {
        Dataset dataset = new Dataset();
        dataset.setName(request.getName());
        dataset.setDescription(request.getDescription());
        dataset.setRanking(request.getRanking());
        DatasetStorage datasetStorage = new DatasetStorage();
        datasetStorage.setStorageType(request.getStorageType());
        datasetStorage.setUrl(request.getUrl());
        datasetStorage.setUsername(request.getUsername());
        datasetStorage.setPassword(request.getPassword());

        datasetMapper.insert(dataset);
        datasetStorage.setId(dataset.getId());
        datasetStorageMapper.insert(datasetStorage);

        annotationFileService.scanFolderParallel(datasetStorage);
        return dataset.getId();
    }

    @Transactional
    public void modifyDataset(ModifyDatasetRequest request) {
        Dataset dataset = new Dataset();
        dataset.setId(request.getId());
        dataset.setName(request.getName());
        dataset.setDescription(request.getDescription());
        dataset.setRanking(request.getRanking());
        datasetMapper.updateById(dataset);
        DatasetStorage datasetStorage = new DatasetStorage();
        datasetStorage.setId(request.getId());
        datasetStorage.setStorageType(request.getStorageType());
        datasetStorage.setUrl(request.getUrl());
        datasetStorage.setUsername(request.getUsername());
        datasetStorage.setPassword(request.getPassword());
        datasetStorageMapper.updateById(datasetStorage);
    }

    public List<Dataset> getDataset() {
        QueryWrapper queryWrapper = new QueryWrapper();
        queryWrapper.eq("is_deleted", 0);
        return datasetMapper.selectList(queryWrapper);
    }

    public DatasetStorage getDatasetStorage(Long id) {
        QueryWrapper queryWrapper = new QueryWrapper();
        queryWrapper.eq("dataset_id", id);
        return datasetStorageMapper.selectOne(queryWrapper);
    }

    @Transactional
    public void deleteById(Long id){
        Dataset dataset = datasetMapper.selectOne(new QueryWrapper<Dataset>().eq("dataset_id", id));
        dataset.setIsDeleted(1);
        datasetMapper.updateById(dataset);
    }
}
