package org.xiaoshuyui.automl;

import org.junit.jupiter.api.Test;
import org.xiaoshuyui.automl.module.aether.workflow.Pipeline;
import org.xiaoshuyui.automl.module.aether.workflow.PipelineParser;

public class PipelineTest {

  @Test
  public void pipelineTest() {
    Pipeline pipeline = PipelineParser.loadFromResource("pipeline.xml");
    pipeline
        .getSteps()
        .forEach(
            step -> {
              System.out.println("Step " + step.getId() + ": " + step.getName());
              if (step.getAether() != null) {
                System.out.println("  → Aether task: " + step.getAether().getTask());
                System.out.println("  → modelId: " + step.getAether().getModelId());
                // System.out.println(" → extra map: " + step.getAether().getExtra());
              }
            });
  }
}
