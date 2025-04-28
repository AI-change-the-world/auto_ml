import 'package:auto_ml/modules/dataset/models/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';

class AnnotationState {
  final List<Annotation> annotations;

  AnnotationState({this.annotations = const []});

  AnnotationState copyWith({List<Annotation>? annotations, Dataset? current}) {
    return AnnotationState(annotations: annotations ?? this.annotations);
  }
}
