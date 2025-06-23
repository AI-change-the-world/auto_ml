import 'package:flutter/material.dart';

abstract class BaseNodeConfigWidget extends StatefulWidget {
  const BaseNodeConfigWidget({
    super.key,
    required this.data,
    required this.onChanged,
    required this.uuid,
  });

  final Map<String, dynamic>? data;
  final void Function(Map<String, dynamic> newData) onChanged;
  final String uuid;
}
