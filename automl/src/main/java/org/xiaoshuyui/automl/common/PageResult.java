package org.xiaoshuyui.automl.common;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class PageResult<T> {
  private List<T> records;
  private long total;
}
