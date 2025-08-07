import 'dart:ui';

class Annotation {
  Offset position;
  double width;
  double height;
  int id;
  final String uuid;
  bool editable;
  bool selected;
  bool isOnAdding;
  bool visible;

  Annotation(
    this.position,
    this.width,
    this.height,
    this.id, {
    this.editable = true,
    this.selected = false,
    this.isOnAdding = false,
    this.visible = true,
    required this.uuid,
  });

  String getLabel(List<String> classes) {
    if (id < 0 || id >= classes.length) {
      return "unknown";
    }

    return classes[id];
  }

  @override
  bool operator ==(Object other) {
    return other is Annotation && uuid == other.uuid;
  }

  @override
  int get hashCode => uuid.hashCode;

  Annotation copyWith({
    Offset? position,
    double? width,
    double? height,
    int? id,
    bool? editable,
    bool? selected,
    bool? isOnAdding,
    bool? visible,
  }) {
    Annotation a = Annotation(
      position ?? this.position,
      width ?? this.width,
      height ?? this.height,
      id ?? this.id,
      editable: editable ?? this.editable,
      selected: selected ?? this.selected,
      isOnAdding: isOnAdding ?? this.isOnAdding,
      visible: visible ?? this.visible,
      uuid: uuid,
    );
    return a;
  }
}
