class Api {
  Api._();

  static final String getAllDatasets = '/dataset/list';

  static final String getStorage = "/dataset/storage/{id}";

  static final String createDataset = "/dataset/new";

  static final String updateDataset = "/dataset/modify";

  static final String deleteDataset = "/dataset/delete/{id}";
}
