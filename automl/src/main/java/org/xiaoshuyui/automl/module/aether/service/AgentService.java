package org.xiaoshuyui.automl.module.aether.service;

import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.common.PageResult;
import org.xiaoshuyui.automl.module.aether.entity.Agent;
import org.xiaoshuyui.automl.module.aether.mapper.AgentMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;

@Service
public class AgentService {
    final private AgentMapper agentMapper;

    public AgentService(AgentMapper agentMapper) {
        this.agentMapper = agentMapper;
    }

    public PageResult list(int pageNum, int pageSize) {
        IPage<Agent> page = new Page<>(pageNum, pageSize);
        QueryWrapper<Agent> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("is_deleted", 0);

        IPage<Agent> resultPage = agentMapper.selectPage(page, queryWrapper);

        return new PageResult<>(resultPage.getRecords(), resultPage.getTotal());
    }
}
