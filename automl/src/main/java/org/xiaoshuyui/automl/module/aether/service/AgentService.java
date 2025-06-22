package org.xiaoshuyui.automl.module.aether.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.util.List;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.common.PageResult;
import org.xiaoshuyui.automl.module.aether.entity.Agent;
import org.xiaoshuyui.automl.module.aether.mapper.AgentMapper;

@Service
public class AgentService {
  private final AgentMapper agentMapper;

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

  public Agent getById(Long id) {
    return agentMapper.selectById(id);
  }

  public List simpleAgentsList() {
    return agentMapper.simpleAgentsList();
  }

  public void newAgent(Agent agent) {
    agentMapper.insert(agent);
  }
}
