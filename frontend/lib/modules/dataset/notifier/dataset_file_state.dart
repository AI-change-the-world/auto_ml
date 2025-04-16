class DatasetFileState {
  final String? sampleFile;
  final int count;
  final int status;
  String? currentContent;

  DatasetFileState({
    this.sampleFile,
    this.count = 0,
    this.status = 0,
    this.currentContent,
  });

  DatasetFileState copyWith({
    String? sampleFile,
    int? count,
    int? index,
    int? status,
    String? currentContent,
  }) {
    return DatasetFileState(
      sampleFile: sampleFile ?? this.sampleFile,
      count: count ?? this.count,
      status: status ?? this.status,
      currentContent: currentContent ?? this.currentContent,
    );
  }
}
