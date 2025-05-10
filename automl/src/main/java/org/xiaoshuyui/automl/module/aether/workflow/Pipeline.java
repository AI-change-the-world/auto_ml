package org.xiaoshuyui.automl.module.aether.workflow;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlAttribute;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlRootElement;
import java.util.List;

@XmlRootElement(name = "pipeline")
@XmlAccessorType(value = XmlAccessType.FIELD)
public class Pipeline {
  @XmlElement(name = "step")
  private List<WorkflowStepConfig> steps;

  @XmlAttribute(name = "outputKey")
  private String outputKey;

  public List<WorkflowStepConfig> getSteps() {
    return steps;
  }

  public String getOutputKey() {
    return outputKey;
  }
}
