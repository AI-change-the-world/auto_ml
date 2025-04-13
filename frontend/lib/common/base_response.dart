class BaseResponse<T> {
  final int? code;
  final String? message;
  final bool? success;
  final T? data;
  final int? timestamp;

  BaseResponse({
    this.code,
    this.success,
    this.message,
    this.data,
    this.timestamp,
  });

  factory BaseResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Object?) fromJsonT,
  ) => BaseResponse(
    code: json['code'] as int?,
    success: json['success'] as bool?,
    message: json['message'] as String?,
    data: json['data'] == null ? null : fromJsonT(json['data']),
    timestamp: json['timestamp'] as int?,
  );

  Map<String, dynamic> toJson(Object? Function(T) toJsonT) => {
    'code': code,
    'success': success,
    'message': message,
    'timestamp': timestamp,
    'data': data == null ? null : toJsonT(data as T),
  };
}
