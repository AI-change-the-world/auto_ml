import 'package:json_annotation/json_annotation.dart';

part 'label_img_response.g.dart';

@JsonSerializable()
class LabelImgData {
  @JsonKey(name: 'image_path')
  final String? imagePath;
  final List<Labels>? labels;

  LabelImgData({this.imagePath, this.labels});

  factory LabelImgData.fromJson(Map<String, dynamic> json) =>
      _$LabelImgDataFromJson(json);
  Map<String, dynamic> toJson() => _$LabelImgDataToJson(this);
}

@JsonSerializable()
class Labels {
  final String? label;
  @JsonKey(name: 'x_center')
  final double? xCenter;
  @JsonKey(name: 'y_center')
  final double? yCenter;
  final double? width;
  final double? height;

  Labels({this.label, this.xCenter, this.yCenter, this.width, this.height});

  factory Labels.fromJson(Map<String, dynamic> json) => _$LabelsFromJson(json);
  Map<String, dynamic> toJson() => _$LabelsToJson(this);

  @override
  String toString() {
    return 'Labels{label: $label, xCenter: $xCenter, yCenter: $yCenter, width: $width, height: $height}';
  }
}
