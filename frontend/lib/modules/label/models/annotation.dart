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

  Annotation copyWith({
    Offset? position,
    double? width,
    double? height,
    int? id,
  }) {
    return Annotation(
      position ?? this.position,
      width ?? this.width,
      height ?? this.height,
      id ?? this.id,
    );
  }
}
