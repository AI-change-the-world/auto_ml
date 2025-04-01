import 'package:auto_ml/modules/isar/dataset.dart';

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
