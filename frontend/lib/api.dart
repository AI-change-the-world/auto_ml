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

  static final String datasetFileList = "/dataset/{id}/file/list";

  static final String datasetContent = "/dataset/content";

  /// annotation
  static final String annotationGetById = "/annotation/{id}";

  static final String annotationFileList = "/annotation/{id}/file/list";

  static final String annotationContent = "/annotation/content";

  /// [tools] label image
  static final String getToolModels = "/tool-model/list";

  static final String autoLabel = "/tool-model/model/chat";
}
