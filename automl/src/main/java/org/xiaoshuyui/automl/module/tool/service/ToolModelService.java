package org.xiaoshuyui.automl.module.tool.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.tool.entity.ToolModel;
import org.xiaoshuyui.automl.module.tool.mapper.ToolModelMapper;

import java.util.List;

@Service
public class ToolModelService {

    private final ToolModelMapper toolModelMapper;

    public ToolModelService(ToolModelMapper toolModelMapper) {
        this.toolModelMapper = toolModelMapper;
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
}
