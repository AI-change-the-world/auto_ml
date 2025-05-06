package org.xiaoshuyui.automl.module.deploy.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.common.PageRequest;
import org.xiaoshuyui.automl.common.PageResult;
import org.xiaoshuyui.automl.module.deploy.entity.AvailableModel;
import org.xiaoshuyui.automl.module.deploy.mapper.AvailableModelMapper;

@Service
public class AvailableModelService {

  private final AvailableModelMapper availableModelMapper;

  public AvailableModelService(AvailableModelMapper availableModelMapper) {
    this.availableModelMapper = availableModelMapper;
  }

  public PageResult getAvailableModels(PageRequest pageRequest) {
    IPage<AvailableModel> page = new Page<>(pageRequest.getPageId(), pageRequest.getPageSize());
    QueryWrapper<AvailableModel> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("is_deleted", 0);

    IPage<AvailableModel> resultPage = availableModelMapper.selectPage(page, queryWrapper);
    return new PageResult<>(resultPage.getRecords(), resultPage.getTotal());
  }
}
