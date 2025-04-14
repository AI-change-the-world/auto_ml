import 'package:json_annotation/json_annotation.dart';

part 'label_img_request.g.dart';

@JsonSerializable()
class LabelImgRequest {
  @JsonKey(name: 'image_path')
  final String imagePath;
  final List<String> classes;

  LabelImgRequest({required this.imagePath, required this.classes});

  factory LabelImgRequest.fromJson(Map<String, dynamic> json) =>
      _$LabelImgRequestFromJson(json);
  Map<String, dynamic> toJson() => _$LabelImgRequestToJson(this);
}
