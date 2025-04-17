class Api {
  Api._();

  /// dataset
  static final String getAllDatasets = '/dataset/list';

  static final String createDataset = "/dataset/new";

  static final String updateDataset = "/dataset/modify";

  static final String deleteDataset = "/dataset/delete/{id}";

  static final String getAnnotationByDatasetId = "/annotation/list/{id}";

  static final String preview = "/dataset/file/preview";

  static final String details = "/dataset/details/{id}";

  /// annotation
}
