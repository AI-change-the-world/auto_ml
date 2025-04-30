package org.xiaoshuyui.automl.module.predict.service;

import java.time.LocalDateTime;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.predict.entity.PredictData;
import org.xiaoshuyui.automl.module.predict.mapper.PredictDataMapper;
import org.xiaoshuyui.automl.util.S3FileDelegate;

@Service
public class PredictDataService {

  private static final Logger log = LoggerFactory.getLogger(PredictDataService.class);
  final PredictDataMapper predictDataMapper;
  final S3FileDelegate s3FileDelegate;

  public PredictDataService(PredictDataMapper predictDataMapper, S3FileDelegate s3FileDelegate) {
    this.predictDataMapper = predictDataMapper;
    this.s3FileDelegate = s3FileDelegate;
  }

  public PredictData getById(Long id) {
    return predictDataMapper.selectById(id);
  }

  public List<PredictData> getDatas() {
    return predictDataMapper.selectList(null);
  }

  public String getFile(Long id) throws Exception {
    PredictData predictData = predictDataMapper.selectById(id);
    if (predictData == null) {
      return null;
    }
    return s3FileDelegate.getFile(predictData.getFileName());
  }

  public String getFile(String filename) throws Exception {
    log.info(LocalDateTime.now() + ": " + filename);
    return s3FileDelegate.getFile(filename);
  }
}
