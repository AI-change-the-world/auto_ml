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

class RefactorAnnotationState {
  List<Annotation> annotations;
  LabelMode mode;
  bool modified;

  RefactorAnnotationState({
    this.annotations = const [],
    this.mode = LabelMode.edit,
    this.modified = false,
  });

  RefactorAnnotationState copyWith({
    List<Annotation>? annotations,
    LabelMode? mode,
    bool? modified,
  }) {
    return RefactorAnnotationState(
      annotations: annotations ?? this.annotations,
      mode: mode ?? this.mode,
      modified: modified ?? this.modified,
    );
  }

  void updateWith({
    List<Annotation>? annotations,
    LabelMode? mode,
    bool? modified,
  }) {
    this.annotations = annotations ?? this.annotations;
    this.mode = mode ?? this.mode;
    this.modified = modified ?? this.modified;
  }
}
