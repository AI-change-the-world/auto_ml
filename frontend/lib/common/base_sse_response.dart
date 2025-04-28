class SseResponse<T> {
  T? data;
  String? message;
  String? status;
  bool isDone;

  SseResponse({this.isDone = false, this.message, this.data, this.status});

  factory SseResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Object?) fromJsonT,
  ) => SseResponse(
    isDone: json['isDone'] as bool? ?? false,
    message: json['message'] as String?,
    data: json['data'] == null ? null : fromJsonT(json['data']),
    status: json['status'] as String?,
  );

  Map<String, dynamic> toJson(Object? Function(T) toJsonT) => {
    'isDone': isDone,
    'message': message,
    'status': status,
    'data': data == null ? null : toJsonT(data as T),
  };
}
