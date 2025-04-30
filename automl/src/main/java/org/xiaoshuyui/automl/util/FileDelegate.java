package org.xiaoshuyui.automl.util;

import java.io.InputStream;

public interface FileDelegate {

  default String getFile(String path) throws Exception {
    return null;
  }

  default InputStream getFileStream(String path) throws Exception {
    return null;
  }
  ;

  default void putFile(String path, InputStream inputStream) throws Exception {}
}
