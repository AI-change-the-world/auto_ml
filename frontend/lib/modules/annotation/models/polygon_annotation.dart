import 'package:flutter/material.dart';
import 'package:uuid/uuid.dart';

class PolygonAnnotation {
  List<Offset> points; // 多边形的顶点
  int id;
  late String uuid;
  bool editable;
  bool selected;

  PolygonAnnotation(
    this.points,
    this.id, {
    this.editable = true,
    this.selected = false,
  }) {
    uuid = Uuid().v4();
  }

  @override
  bool operator ==(Object other) {
    return other is PolygonAnnotation && uuid == other.uuid;
  }

  @override
  int get hashCode => uuid.hashCode;

  PolygonAnnotation copyWith({
    List<Offset>? points,
    int? id,
    bool? editable,
    bool? selected,
  }) {
    PolygonAnnotation p = PolygonAnnotation(
      points ?? List.from(this.points),
      id ?? this.id,
      editable: editable ?? this.editable,
      selected: selected ?? this.selected,
    );
    p.uuid = uuid;
    return p;
  }

  bool isPointInPolygon(Offset point) {
    int intersections = 0;
    int n = points.length;

    for (int i = 0; i < n; i++) {
      // 获取多边形的当前边（连接点i和i+1，最后一个点与第一个点连接）
      Offset p1 = points[i];
      Offset p2 = points[(i + 1) % n];

      // 判断射线是否与多边形的边相交
      if (point.dy > p1.dy && point.dy <= p2.dy ||
          point.dy > p2.dy && point.dy <= p1.dy) {
        double xIntersect =
            p1.dx + (point.dy - p1.dy) * (p2.dx - p1.dx) / (p2.dy - p1.dy);
        if (xIntersect > point.dx) {
          intersections++;
        }
      }
    }

    // 如果交点数为奇数，则点在多边形内部
    return intersections % 2 == 1;
  }
}
