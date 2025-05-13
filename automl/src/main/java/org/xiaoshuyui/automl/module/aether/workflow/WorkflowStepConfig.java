package org.xiaoshuyui.automl.module.aether.workflow;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlElement;
import lombok.Data;

@Data
@XmlAccessorType(value = XmlAccessType.FIELD)
public class WorkflowStepConfig {
  @XmlAttribute private int id;
  @XmlAttribute private String name;

  @XmlAttribute(name = "outputKey")
  private String outputKey;

  @XmlAttribute(name = "outputType")
  private String outputType;

  @XmlAttribute(name = "loop")
  private Boolean loop;

  @XmlAttribute(name = "loopVar")
  private String loopVar;

  @XmlAttribute(name = "inputKey")
  private String inputKey;

  @XmlAttribute(name = "inputType")
  private String inputType;

  @XmlElement(name = "action")
  private ActionConfig action;

  @XmlElement(name = "aether")
  private AetherWorkflowConfig aether;

  @XmlElement(name = "next")
  private Integer next;

  public boolean getLoop() {
    if (loop == null) return false;
    return loop;
  }
}
