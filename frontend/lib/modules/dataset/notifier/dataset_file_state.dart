class DatasetFileState {
  final List<String> files;
  final int count;
  final int index;
  final int status;
  String? currentContent;

  DatasetFileState({
    this.files = const [],
    this.count = 0,
    this.index = 0,
    this.status = 0,
    this.currentContent,
  });

  DatasetFileState copyWith({
    List<String>? files,
    int? count,
    int? index,
    int? status,
    String? currentContent,
  }) {
    return DatasetFileState(
      files: files ?? this.files,
      count: count ?? this.count,
      index: index ?? this.index,
      status: status ?? this.status,
      currentContent: currentContent ?? this.currentContent,
    );
  }
}
