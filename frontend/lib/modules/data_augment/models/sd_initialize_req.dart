// class SDInitializeRequest(BaseModel):
//     enable_img2img: Optional[bool] = False
//     enable_inpaint: Optional[bool] = False
//     model_path: Optional[str] = "/root/models/sd3m"

import 'package:json_annotation/json_annotation.dart';

part 'sd_initialize_req.g.dart';

@JsonSerializable()
class SDInitializeRequest {
  SDInitializeRequest({this.enableImg2img, this.enableInpaint, this.modelPath});

  @JsonKey(name: "enable_img2img")
  bool? enableImg2img;
  @JsonKey(name: "enable_inpaint")
  bool? enableInpaint;
  @JsonKey(name: "model_path")
  String? modelPath;

  Map<String, dynamic> toJson() => _$SDInitializeRequestToJson(this);

  factory SDInitializeRequest.fromJson(Map<String, dynamic> json) =>
      _$SDInitializeRequestFromJson(json);
}
