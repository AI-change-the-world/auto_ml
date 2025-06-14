import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/models/get_all_dataset_response.dart'
    as r;

DatasetType getType(int type) {
  switch (type) {
    case 0:
      return DatasetType.image;
    case 1:
      return DatasetType.text;
    case 2:
      return DatasetType.audio;
    case 3:
      return DatasetType.video;
    default:
      return DatasetType.image;
  }
}

class Dataset {
  int id;
  String name;
  String description;
  String createdAt;
  String updatedAt;
  DatasetType type;
  double ranking;

  String datasetPath;
  @Deprecated("will be removed in future")
  String labelPath;
  int storageType;
  String username;
  String password;
  int scanStatus;
  String? sampleFilePath;
  int fileCount;

  Dataset({
    this.id = -1,
    this.name = "",
    this.description = "",
    this.createdAt = "",
    this.updatedAt = "",
    this.type = DatasetType.image,
    this.ranking = 0,
    this.datasetPath = "",
    this.labelPath = "",
    this.storageType = 0,
    this.username = "",
    this.password = "",
    this.scanStatus = 0,
    this.sampleFilePath,
    this.fileCount = 0,
  });

  static Dataset fromDataset(r.Dataset d) {
    return Dataset(
      id: d.id,
      name: d.name,
      description: d.description,
      createdAt: d.createdAt.toLocal().toString(),
      updatedAt: d.updatedAt.toLocal().toString(),
      type: getType(d.type),
      ranking: d.ranking,
      datasetPath: d.url ?? "Unknown",
      labelPath: "",
      storageType: d.storageType,
      username: d.username ?? "",
      password: d.password ?? "",
      scanStatus: d.scanStatus,
      sampleFilePath: d.sampleFilePath,
      fileCount: d.fileCount,
    );
  }

  @override
  String toString() {
    return "Dataset(id: $id, name: $name, description: $description, createdAt: $createdAt, updatedAt: $updatedAt, type: $type, ranking: $ranking, datasetPath: $datasetPath, labelPath: $labelPath)";
  }
}

class DatasetState {
  final List<Dataset> datasets;
  final Dataset? current;

  DatasetState({this.datasets = const [], this.current});

  DatasetState copyWith({List<Dataset>? datasets, Dataset? current}) {
    return DatasetState(datasets: datasets ?? this.datasets, current: current);
  }
}
