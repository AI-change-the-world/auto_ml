import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/entity/get_all_dataset_response.dart'
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
  String labelPath;

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
      datasetPath: "",
      labelPath: "",
    );
  }
}

class DatasetState {
  final List<Dataset> datasets;

  DatasetState({this.datasets = const []});

  DatasetState copyWith({
    List<DatasetType>? selectedTypes,
    List<Dataset>? datasets,
  }) {
    return DatasetState(datasets: datasets ?? this.datasets);
  }
}
