package org.xiaoshuyui.automl.module.predict.service;

import java.util.UUID;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.predict.entity.PredictTask;
import org.xiaoshuyui.automl.module.predict.mapper.PredictTaskMapper;

@Service
public class PredictTaskService {
  final PredictTaskMapper predictTaskMapper;

  public PredictTaskService(PredictTaskMapper predictTaskMapper) {
    this.predictTaskMapper = predictTaskMapper;
  }

  public PredictTask getById(Long id) {
    return predictTaskMapper.selectById(id);
  }

  public String create(Long dataId) {
    PredictTask predictTask = new PredictTask();
    predictTask.setTaskDataId(dataId);
    predictTask.setSessionId(UUID.randomUUID().toString());
    predictTask.setTaskResult("");
    predictTaskMapper.insert(predictTask);
    return predictTask.getSessionId();
  }
}
