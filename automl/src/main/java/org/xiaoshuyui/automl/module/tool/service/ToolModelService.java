package org.xiaoshuyui.automl.module.tool.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.concurrent.TimeUnit;
import okhttp3.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.dataset.service.DatasetService;
import org.xiaoshuyui.automl.module.tool.entity.ToolModel;
import org.xiaoshuyui.automl.module.tool.mapper.ToolModelMapper;

@Service
public class ToolModelService {

  @Value("${ai-platform.url}")
  String baseUrl;

  @Value("${ai-platform.get-label}")
  String getLabelApi;

  private final ToolModelMapper toolModelMapper;
  private final DatasetService datasetService;
  private final AnnotationService annotationService;

  public ToolModelService(
      ToolModelMapper toolModelMapper,
      DatasetService datasetService,
      AnnotationService annotationService) {
    this.toolModelMapper = toolModelMapper;
    this.datasetService = datasetService;
    this.annotationService = annotationService;
  }

  public List<ToolModel> getAll() {
    QueryWrapper<ToolModel> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("is_deleted", 0);
    return toolModelMapper.selectList(queryWrapper);
  }

  public ToolModel getById(Long id) {
    QueryWrapper<ToolModel> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("is_deleted", 0);
    queryWrapper.eq("tool_model_id", id);
    return toolModelMapper.selectOne(queryWrapper);
  }

  private static final OkHttpClient okClient =
      new OkHttpClient.Builder()
          .connectTimeout(10, TimeUnit.SECONDS)
          .readTimeout(180, TimeUnit.SECONDS)
          .writeTimeout(10, TimeUnit.SECONDS)
          .build();
  private static final ObjectMapper mapper = new ObjectMapper();
}
