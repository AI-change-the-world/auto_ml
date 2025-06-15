class DatasetFileState {
  final List<String> samples;
  final int usedCount;

  DatasetFileState({this.samples = const [], this.usedCount = 0});

  DatasetFileState copyWith({List<String>? samples, int? usedCount}) {
    return DatasetFileState(
      samples: samples ?? this.samples,
      usedCount: usedCount ?? this.usedCount,
    );
  }

  factory DatasetFileState.fromJson(Map<String, dynamic> json) {
    return DatasetFileState(
      samples:
          (json['samples'] as List<dynamic>)
              .map((dynamic item) => item as String)
              .toList(),
      usedCount: json['usedCount'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {'samples': samples, 'usedCount': usedCount};
  }
}
