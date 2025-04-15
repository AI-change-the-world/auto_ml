import 'package:auto_ml/modules/dataset/entity/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';

class AnnotationState {
  final List<Annotation> annotations;
  final Dataset? current;

  AnnotationState({this.annotations = const [], this.current});

  AnnotationState copyWith({List<Annotation>? annotations, Dataset? current}) {
    return AnnotationState(
      annotations: annotations ?? this.annotations,
      current: current ?? this.current,
    );
  }
}
