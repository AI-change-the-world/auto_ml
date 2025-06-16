package org.xiaoshuyui.automl.module.home.entity;

import java.util.ArrayList;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class HomeIndex {
  Long datasetCount;
  Long annotationCount;
  Long taskCount;
  Long taskErrorCount;
  List<TaskPerDay> taskPerDays;

  @Data
  public static class TaskPerDay {
    String date;
    Long taskCount;
    Long taskDuration;

    public TaskPerDay(String date, Long taskCount, Long taskDuration) {
      this.date = date;
      this.taskCount = taskCount;
      this.taskDuration = taskDuration;
    }

    public TaskPerDay() {
      this.date = "";
      this.taskCount = 0L;
      this.taskDuration = 0L;
    }
  }

  public HomeIndex() {
    datasetCount = 0L;
    annotationCount = 0L;
    taskCount = 0L;
    taskErrorCount = 0L;
    taskPerDays = new ArrayList<>();
  }
}
