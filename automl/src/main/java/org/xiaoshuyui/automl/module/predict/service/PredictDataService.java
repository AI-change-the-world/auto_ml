package org.xiaoshuyui.automl.module.predict.service;

import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.predict.entity.PredictData;
import org.xiaoshuyui.automl.module.predict.mapper.PredictDataMapper;

import java.util.List;

@Service
public class PredictDataService {

    final PredictDataMapper predictDataMapper;

    public PredictDataService(PredictDataMapper predictDataMapper) {
        this.predictDataMapper = predictDataMapper;
    }

    public PredictData getById(Long id) {
        return predictDataMapper.selectById(id);
    }

    public List<PredictData> getDatas() {
        return predictDataMapper.selectList(null);
    }
}
