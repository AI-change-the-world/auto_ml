import 'package:auto_ml/modules/predict/models/predict_list_response.dart';

class PredictDataState {
  final List<PredictData> data;

  PredictDataState({this.data = const []});

  PredictDataState copyWith({List<PredictData>? data}) {
    return PredictDataState(data: data ?? this.data);
  }
}
