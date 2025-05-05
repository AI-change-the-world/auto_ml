package org.xiaoshuyui.automl.module.task.service;

import java.util.List;

import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.task.entity.BaseModels;
import org.xiaoshuyui.automl.module.task.mapper.BaseModelsMapper;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;

@Service
public class BaseModelsService {
    final private BaseModelsMapper baseModelsMapper;

    public BaseModelsService(BaseModelsMapper baseModelsMapper) {
        this.baseModelsMapper = baseModelsMapper;
    }

    public BaseModels getById(Long id) {
        return baseModelsMapper.selectById(id);
    }

    public List<BaseModels> getBaseModels() {
        QueryWrapper<BaseModels> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("is_deleted", 0);
        return baseModelsMapper.selectList(queryWrapper);
    }

    public List<BaseModels> getModelsByType(int type) {
        QueryWrapper<BaseModels> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("base_model_type", type);
        queryWrapper.eq("is_deleted", 0);
        return baseModelsMapper.selectList(queryWrapper);
    }
}
