package org.xiaoshuyui.automl.module.aether;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.xml.parsers.DocumentBuilderFactory;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;

@Slf4j
public class AetherPipelineConverter {
  @Data
  static class Step {
    String id;
    String name;
    String next;

    Step(String id, String name, String next) {
      this.id = id;
      this.name = name;
      this.next = next;
    }
  }

  public static String convert(String pipeline) throws Exception {
    // 将字符串转为 InputStream
    ByteArrayInputStream input =
        new ByteArrayInputStream(pipeline.getBytes(StandardCharsets.UTF_8));

    // 解析 XML
    Document doc = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(input);
    doc.getDocumentElement().normalize();
    NodeList steps = doc.getElementsByTagName("step");
    List<Step> stepList = new ArrayList<>();
    Map<String, Integer> positionMap = new HashMap<>();

    int startX = 100;
    int stepWidth = 200;
    int stepHeight = 100;
    int gap = 250;

    for (int i = 0; i < steps.getLength(); i++) {
      Element step = (Element) steps.item(i);
      String id = step.getAttribute("id");
      String name = step.getAttribute("name");
      String next = null;
      NodeList nextNodes = step.getElementsByTagName("next");
      if (nextNodes.getLength() > 0) {
        next = nextNodes.item(0).getTextContent();
      }

      stepList.add(new Step(id, name, next));
      positionMap.put(id, i);
    }

    JsonArray nodes = new JsonArray();
    JsonArray edges = new JsonArray();

    for (int i = 0; i < stepList.size(); i++) {
      Step s = stepList.get(i);
      int dx = startX + i * gap;
      int dy = 200;

      JsonObject node = new JsonObject();
      node.addProperty("uuid", "step-" + s.id);
      node.addProperty("label", s.name);
      node.addProperty("depth", -1);
      JsonObject offset = new JsonObject();
      offset.addProperty("dx", dx);
      offset.addProperty("dy", dy);
      node.add("offset", offset);
      node.addProperty("width", stepWidth);
      node.addProperty("height", stepHeight);
      node.addProperty("nodeName", s.name);
      node.addProperty("description", "");
      node.addProperty("builderName", "StepNode");
      node.add("data", new JsonObject());
      nodes.add(node);

      if (s.next != null && positionMap.containsKey(s.next)) {
        int nextIdx = positionMap.get(s.next);
        int targetDx = startX + nextIdx * gap;

        JsonObject edge = new JsonObject();
        edge.addProperty("uuid", "edge-" + s.id + "-" + s.next);
        edge.addProperty("source", "step-" + s.id);
        edge.addProperty("target", "step-" + s.next);

        JsonObject start = new JsonObject();
        start.addProperty("dx", dx + stepWidth);
        start.addProperty("dy", dy + stepHeight / 2);
        edge.add("start", start);

        JsonObject end = new JsonObject();
        end.addProperty("dx", targetDx);
        end.addProperty("dy", dy + stepHeight / 2);
        edge.add("end", end);

        edges.add(edge);
      }
    }

    JsonObject root = new JsonObject();
    root.add("nodes", nodes);
    root.add("edges", edges);

    Gson gson = new GsonBuilder().setPrettyPrinting().create();
    return gson.toJson(root);
  }
}
