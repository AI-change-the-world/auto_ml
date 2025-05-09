package org.xiaoshuyui.automl.module.aether.workflow;

import jakarta.xml.bind.annotation.XmlAttribute;

public class ActionConfig {
  @XmlAttribute(name = "class")
  private String className;

  public String getClassName() {
    return className;
  }
}
