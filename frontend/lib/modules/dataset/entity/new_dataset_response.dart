class NewDatasetResponse {
  int id;

  NewDatasetResponse({required this.id});

  factory NewDatasetResponse.fromJson(Map<String, dynamic> json) {
    return NewDatasetResponse(id: json['id']);
  }

  Map<String, dynamic> toJson() {
    return {'id': id};
  }
}
