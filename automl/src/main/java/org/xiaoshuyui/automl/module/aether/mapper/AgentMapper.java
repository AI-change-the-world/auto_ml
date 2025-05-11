package org.xiaoshuyui.automl.module.aether.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import java.util.List;
import org.apache.ibatis.annotations.Select;
import org.xiaoshuyui.automl.module.aether.entity.Agent;
import org.xiaoshuyui.automl.module.aether.entity.AgentSimple;

public interface AgentMapper extends BaseMapper<Agent> {

  @Select(
      "SELECT agent_id AS id, agent_name  AS name , is_recommended as isRecommended FROM agent WHERE is_deleted = 0")
  public List<AgentSimple> simpleAgentsList();
}
