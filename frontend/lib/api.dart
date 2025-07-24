class Api {
  Api._();

  // dev
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

  static final String appendDatasetFiles = "/dataset/{id}/append/files";

  static final String datasetExport = "/dataset/export/{id}";

  // static final String datasetContent = "/dataset/content";

  /// [annotation]
  static final String annotationGetById = "/annotation/{id}";

  static final String annotationFileList = "/annotation/{id}/file/list";

  static final String annotationContent = "/annotation/content";

  static final String annotationNew = "/annotation/new";

  static final String annotationUpdate = "/annotation/file/update";

  static final String annotationClassesUpdate = "/annotation/update/classes";

  static final String appendAnnotationFiles = "/annotation/{id}/append/files";

  static final String annotationUpdatePrompt = "/annotation/update/prompt";

  static final String annotationExport = "/annotation/export/{id}";

  static final String annotationDetails = "/annotation/class/details/{id}";

  static final String annotationGenerate = "/annotation/generate/details/{id}";

  /// [tools] label image
  static final String getToolModels = "/tool-model/list";

  static final String newToolModel = "/tool-model/new";

  static final String autoLabel = "/tool-model/model/auto-label";

  static final String autoLabelMultiple =
      "/tool-model/model/auto-label/multiple";

  static final String getSimilar = "/tool-model/find/similar";

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

  static final String newTrainTask = "/task/create/train";

  /// [base models] base models
  static final String baseModelsList = "/task/base-models/list";

  static final String baseModelsTypeList = "/task/base-models/list/{type}";

  /// [deploy] deploy
  static final String deployList = "/deploy/available-models/list";

  static final String runningModels = "/deploy/running-models";

  static final String startModel = "/deploy/start/{id}";

  static final String stopModel = "/deploy/stop/{id}";

  static final String predictSingleImage = "/deploy/predict/image";

  /// [aether] aether
  static final String aetherAgentList = "/aether/agent/list";

  static final String aetherAgentSimpleList = "/aether/agent/list/simple";

  static final String agent = "/aether/workflow/auto-label";

  static final String annotationDataset = "/aether/workflow/auto-label/dataset";

  static final String agentWorkflowContent = "/aether/pipeline/content/{id}";

  /// [home] index
  static final String homeIndex = "/home/index";

  /// [aug-and-qua] augment and quality
  static final String gan =
      "http://localhost:18000/augment/gan/generate/stream";

  static final String cv = "http://localhost:18000/augment/cv/generate/stream";

  static final String getAugData = "/augmentAndQuality/get/image";

  static final String optimize =
      "http://localhost:18000/augment/sd/prompt/optimize";

  static final String sd = "http://localhost:18000/augment/sd/generate";

  static final String measure = "http://localhost:18000/augment/measure/stream";

  static final String sdIsOn = "http://localhost:18000/augment/on";

  static final String sdInitial =
      "http://localhost:18000/augment/sd/initialize";

  static final String sdOptimize =
      "http://localhost:18000/augment/sd/deep-optimize";

  static final String graph =
      "http://localhost:18000/augment/graph/embedded/{model_id}";

  // video processing

  static final String upload = "http://localhost:18001/video/upload";

  static final String searchFrame = "http://localhost:18001/video/search-frame";
}
