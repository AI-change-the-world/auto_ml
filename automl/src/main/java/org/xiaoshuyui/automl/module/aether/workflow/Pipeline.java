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

  @XmlAttribute(name = "name")
  private String name;

  @XmlElement(name = "sync")
  private Boolean sync;

  public List<WorkflowStepConfig> getSteps() {
    return steps;
  }

  public String getOutputKey() {
    return outputKey;
  }

  public String getName() {
    if (name == null) return "label image";
    return name;
  }

  public Boolean getSync() {
    if (sync == null) return true;
    return sync;
  }
}
