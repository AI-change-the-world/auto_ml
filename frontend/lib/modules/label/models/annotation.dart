import 'dart:ui';

import 'package:uuid/uuid.dart';

class Annotation {
  Offset position;
  double width;
  double height;
  int id;
  late String uuid;

  Annotation(this.position, this.width, this.height, this.id) {
    uuid = Uuid().v4();
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
  }) {
    Annotation a = Annotation(
      position ?? this.position,
      width ?? this.width,
      height ?? this.height,
      id ?? this.id,
    );
    a.uuid = uuid;
    return a;
  }
}
