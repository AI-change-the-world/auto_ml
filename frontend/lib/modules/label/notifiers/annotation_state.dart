import 'package:auto_ml/modules/label/models/annotation.dart';

enum LabelMode { edit, add }

class AnnotationState {
  final List<Annotation> annotations;
  final String selectedAnnotationUuid;
  final LabelMode mode;

  AnnotationState({
    this.annotations = const [],
    this.selectedAnnotationUuid = "",
    this.mode = LabelMode.edit,
  });

  AnnotationState copyWith({
    List<Annotation>? annotations,
    String? selectedAnnotationUuid,
    LabelMode? mode,
  }) {
    return AnnotationState(
      annotations: annotations ?? this.annotations,
      selectedAnnotationUuid:
          selectedAnnotationUuid ?? this.selectedAnnotationUuid,
      mode: mode ?? this.mode,
    );
  }
}
