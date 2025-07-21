import 'package:auto_ml/modules/annotation/models/annotation.dart';
import 'package:auto_ml/modules/annotation/notifiers/enum.dart';

class AnnotationState {
  final List<Annotation> annotations;
  final String selectedAnnotationUuid;
  final LabelMode mode;
  final bool modified;

  AnnotationState({
    this.annotations = const [],
    this.selectedAnnotationUuid = "",
    this.mode = LabelMode.edit,
    this.modified = false,
  });

  AnnotationState copyWith({
    List<Annotation>? annotations,
    String? selectedAnnotationUuid,
    LabelMode? mode,
    bool? modified,
  }) {
    return AnnotationState(
      annotations: annotations ?? this.annotations,
      selectedAnnotationUuid:
          selectedAnnotationUuid ?? this.selectedAnnotationUuid,
      mode: mode ?? this.mode,
      modified: modified ?? this.modified,
    );
  }
}
