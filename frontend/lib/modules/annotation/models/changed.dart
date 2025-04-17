enum SizeChangedType { left, right, top, bottom }

class SizeChanged {
  final double value;
  final SizeChangedType type;

  const SizeChanged({required this.value, required this.type});
}
