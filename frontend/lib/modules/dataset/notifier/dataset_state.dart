import 'package:auto_ml/modules/isar/dataset.dart';

class DatasetState {
  final List<DatasetType> selectedTypes;
  final List<Dataset> datasets;

  DatasetState({this.selectedTypes = const [], this.datasets = const []});

  DatasetState copyWith({
    List<DatasetType>? selectedTypes,
    List<Dataset>? datasets,
  }) {
    return DatasetState(
      selectedTypes: selectedTypes ?? this.selectedTypes,
      datasets: datasets ?? this.datasets,
    );
  }
}
