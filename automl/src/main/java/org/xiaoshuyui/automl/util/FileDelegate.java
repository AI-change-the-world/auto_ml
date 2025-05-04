package org.xiaoshuyui.automl.util;

import java.io.InputStream;
import java.util.List;

import org.jetbrains.annotations.Nullable;

public interface FileDelegate {

  default String getFile(String path, @Nullable String bucket) throws Exception {
    return null;
  }

  default String getFile(String path) throws Exception {
    return null;
  }

  default InputStream getFileStream(String path) throws Exception {
    return null;
  };

  default void putFile(String path, InputStream inputStream) throws Exception {
  }

  /*
   * 批量上传文件
   * files: 文件列表
   * bucket: 存储桶
   * basePath: 文件夹路径
   * return: 文件列表
   */
  default List<String> putFileList(List<String> files, String bucket, String basePath) throws Exception {
    return null;
  }
}
