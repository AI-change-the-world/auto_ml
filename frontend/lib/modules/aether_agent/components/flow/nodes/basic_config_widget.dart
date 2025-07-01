import 'package:flow_compose/flow_compose.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

// ignore: must_be_immutable
abstract class BaseNodeConfigWidget extends ConsumerStatefulWidget {
  const BaseNodeConfigWidget({
    super.key,
    required this.data,
    required this.onDataChanged,
  });

  // final Map<String, dynamic>? data;
  final void Function(Map<String, dynamic> newData) onDataChanged;
  // final String uuid;
  final NodeModel data;
}
