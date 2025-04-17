import 'package:auto_ml/modules/annotation/models/annotation.dart';

enum LabelMode { edit, add }

class AnnotationState {
  final List<Annotation> annotations;
  final String selectedAnnotationUuid;
  final LabelMode mode;

  final String current;

  AnnotationState({
    this.annotations = const [],
    this.selectedAnnotationUuid = "",
    this.mode = LabelMode.edit,
    this.current = "",
  });

  AnnotationState copyWith({
    List<Annotation>? annotations,
    String? selectedAnnotationUuid,
    LabelMode? mode,
    String? current,
  }) {
    return AnnotationState(
      annotations: annotations ?? this.annotations,
      selectedAnnotationUuid:
          selectedAnnotationUuid ?? this.selectedAnnotationUuid,
      mode: mode ?? this.mode,
      current: current ?? this.current,
    );
  }
}
