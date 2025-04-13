import 'package:auto_ml/modules/dataset/constants.dart';

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

class Dataset {
  int id = 0;

  String? name;

  String? description;

  String? dataPath;

  DatasetType type = DatasetType.image;

  DatasetTask task = DatasetTask.classification;

  String? labelPath;

  double rating = 0;

  int createAt = DateTime.now().millisecondsSinceEpoch;
}
