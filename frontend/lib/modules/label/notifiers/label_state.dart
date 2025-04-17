class LabelState {
  String current;
  String dataPath;
  String labelPath;
  // String selectedAnnotationUuid;
  // LabelMode mode;

  /// missing dataset type, such as yolo or sth else
  late List<MapEntry<String, String>> dataLabelPairs = [];

  // List<Annotation> currentLabels;

  LabelState({
    this.current = "",
    required this.dataPath,
    required this.labelPath,
    // this.currentLabels = const [],
    // this.selectedAnnotationUuid = "",
    // this.mode = LabelMode.edit,
  });

  LabelState copyWith({
    String? current,
    String? dataPath,
    String? labelPath,
    // List<Annotation>? currentLabels,
    // String? selectedAnnotationUuid,
    // LabelMode? mode,
  }) {
    return LabelState(
      current: current ?? this.current,
      dataPath: dataPath ?? this.dataPath,
      labelPath: labelPath ?? this.labelPath,
      // currentLabels: currentLabels ?? this.currentLabels,
      // selectedAnnotationUuid:
      //     selectedAnnotationUuid ?? this.selectedAnnotationUuid,
      // mode: mode ?? this.mode,
    );
  }
}
