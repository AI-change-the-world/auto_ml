class BaseResponse<T> {
  final int? status;
  final String? message;
  final T? data;

  BaseResponse({this.status, this.message, this.data});

  factory BaseResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Object?) fromJsonT,
  ) => BaseResponse(
    status: json['status'] as int?,
    message: json['message'] as String?,
    data: json['data'] == null ? null : fromJsonT(json['data']),
  );

  Map<String, dynamic> toJson(Object? Function(T) toJsonT) => {
    'status': status,
    'message': message,
    'data': data == null ? null : toJsonT(data as T),
  };
}
