package org.xiaoshuyui.automl.module.aether.workflow;

import jakarta.xml.bind.JAXBContext;
import jakarta.xml.bind.Unmarshaller;
import java.io.InputStream;
import java.io.StringReader;

public class PipelineParser {
  public static Pipeline loadFromResource(String resourcePath) {
    try (InputStream is =
        Thread.currentThread().getContextClassLoader().getResourceAsStream(resourcePath)) {
      JAXBContext ctx = JAXBContext.newInstance(Pipeline.class);
      Unmarshaller um = ctx.createUnmarshaller();
      return (Pipeline) um.unmarshal(is);
    } catch (Exception e) {
      throw new RuntimeException("Failed to load pipeline XML", e);
    }
  }

  public static Pipeline loadFromXml(String xml) {
    try {
      JAXBContext ctx = JAXBContext.newInstance(Pipeline.class);
      Unmarshaller um = ctx.createUnmarshaller();
      StringReader reader = new StringReader(xml);
      return (Pipeline) um.unmarshal(reader);
    } catch (Exception e) {
      throw new RuntimeException("Failed to load pipeline XML", e);
    }
  }
}
