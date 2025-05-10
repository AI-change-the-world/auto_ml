class AetherBaseResponse<T> {
  final bool success;
  final T? output;

  final Meta meta;
  final String? error;

  AetherBaseResponse({
    required this.success,
    this.output,
    required this.meta,
    this.error,
  });

  factory AetherBaseResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Object?) fromJsonT,
  ) => AetherBaseResponse(
    success: json['success'] as bool,
    output: json['output'] == null ? null : fromJsonT(json['output']),
    meta: Meta.fromJson(json['meta'] as Map<String, dynamic>),
    error: json['error'] as String?,
  );

  Map<String, dynamic> toJson(Object? Function(T) toJsonT) => {
    'success': success,
    'output': output == null ? null : toJsonT(output as T),
    'meta': meta.toJson(),
    'error': error,
    'timestamp': meta.timeCostMs,
    'taskId': meta.taskId,
  };
}

class Meta {
  final int timeCostMs;
  final int taskId;

  Meta({required this.timeCostMs, required this.taskId});

  factory Meta.fromJson(Map<String, dynamic> json) => Meta(
    timeCostMs: json['timeCostMs'] as int,
    taskId: json['taskId'] as int,
  );

  Map<String, dynamic> toJson() => {'timeCostMs': timeCostMs, 'taskId': taskId};
}
