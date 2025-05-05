class BasePageResult<T> {
  final int total;
  final List<T> records;

  BasePageResult({required this.total, required this.records});

  factory BasePageResult.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic>) fromJsonT,
  ) {
    return BasePageResult(
      total: json['total'] as int,
      records:
          (json['records'] as List<dynamic>?)
              ?.map((e) => fromJsonT(e as Map<String, dynamic>))
              .toList() ??
          [],
    );
  }
}
