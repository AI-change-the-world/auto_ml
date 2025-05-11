import 'package:json_annotation/json_annotation.dart';

part 'agent_simple_response.g.dart';

@JsonSerializable()
class AgentSimpleResponse {
  final List<AgentSimple> data;
  AgentSimpleResponse({required this.data});

  factory AgentSimpleResponse.fromJson(Map<String, dynamic> json) =>
      _$AgentSimpleResponseFromJson(json);

  Map<String, dynamic> toJson() {
    return _$AgentSimpleResponseToJson(this);
  }
}

@JsonSerializable()
class AgentSimple {
  final int id;
  final String name;
  final int isRecommended;

  AgentSimple({
    required this.id,
    required this.name,
    required this.isRecommended,
  });

  factory AgentSimple.fromJson(Map<String, dynamic> json) =>
      _$AgentSimpleFromJson(json);

  Map<String, dynamic> toJson() {
    return _$AgentSimpleToJson(this);
  }
}
