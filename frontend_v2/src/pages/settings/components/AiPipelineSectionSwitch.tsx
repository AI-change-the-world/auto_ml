import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Segmented } from 'antd';

type AiPipelineSectionKey = 'templates' | 'providers';

interface AiPipelineSectionSwitchProps {
  activeKey: AiPipelineSectionKey;
}

const sectionRouteMap: Record<AiPipelineSectionKey, string> = {
  templates: '/ai-pipeline',
  providers: '/ai-pipeline/providers',
};

const AiPipelineSectionSwitch: React.FC<AiPipelineSectionSwitchProps> = ({ activeKey }) => {
  const navigate = useNavigate();

  return (
    <Segmented<AiPipelineSectionKey>
      value={activeKey}
      options={[
        { label: '模板', value: 'templates' },
        { label: 'Provider 资源', value: 'providers' },
      ]}
      onChange={(value) => navigate(sectionRouteMap[value])}
    />
  );
};

export default AiPipelineSectionSwitch;
