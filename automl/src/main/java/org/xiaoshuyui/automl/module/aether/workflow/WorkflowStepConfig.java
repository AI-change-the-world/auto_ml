package org.xiaoshuyui.automl.module.aether.workflow;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlElement;
import lombok.Data;

@Data
@XmlAccessorType(value = XmlAccessType.FIELD)
public class WorkflowStepConfig {
  @XmlAttribute private String id;
  @XmlAttribute private String name;

  @XmlElement(name = "action")
  private ActionConfig action;

  @XmlElement(name = "aether")
  private AetherWorkflowConfig aether;

  @XmlElement(name = "next")
  private String next;
}
