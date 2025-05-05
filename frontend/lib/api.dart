class Api {
  Api._();

  static String baseUrl = 'http://localhost:8080';

  static void setBaseUrl(String url) {
    baseUrl = url;
  }

  /// [dataset]
  static final String getAllDatasets = '/dataset/list';

  static final String createDataset = "/dataset/new";

  static final String updateDataset = "/dataset/modify";

  static final String deleteDataset = "/dataset/delete/{id}";

  static final String getAnnotationByDatasetId = "/annotation/list/{id}";

  static final String preview = "/dataset/file/preview";

  static final String details = "/dataset/details/{id}";

  static final String datasetFileList = "/dataset/{id}/file/list";

  // static final String datasetContent = "/dataset/content";

  /// [annotation]
  static final String annotationGetById = "/annotation/{id}";

  static final String annotationFileList = "/annotation/{id}/file/list";

  static final String annotationContent = "/annotation/content";

  static final String annotationNew = "/annotation/new";

  /// [tools] label image
  static final String getToolModels = "/tool-model/list";

  static final String autoLabel = "/tool-model/model/auto-label";

  /// [predict] predict
  static final String predictList = "/predict/file/list";

  static final String getPreview = "/predict/file/preview/{id}";

  static final String processVideoData = "/predict/videoProcess";

  static final String s3preview = "/predict/s3/preview";

  static final String describeImageList = "/predict/describe/list";

  static final String describeImage = "/predict/describe";

  /// [task] task
  static final String taskList = "/task/list";

  static final String taskLog = "/task/{id}/logs";
}
