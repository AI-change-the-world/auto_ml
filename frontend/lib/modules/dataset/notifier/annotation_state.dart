import 'package:auto_ml/modules/dataset/models/annotation_list_response.dart';

class AnnotationState {
  final List<Annotation> annotations;
  final int selected;
  final bool loading;
  final String chartData;

  AnnotationState({
    this.annotations = const [],
    this.selected = -1,
    this.loading = false,
    this.chartData = '',
  });

  AnnotationState copyWith({
    List<Annotation>? annotations,
    int? selected,
    bool? loading,
    String? chartData,
  }) {
    return AnnotationState(
      annotations: annotations ?? this.annotations,
      selected: selected ?? this.selected,
      loading: loading ?? this.loading,
      chartData: chartData ?? this.chartData,
    );
  }
}
