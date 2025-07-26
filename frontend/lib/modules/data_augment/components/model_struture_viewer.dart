import 'dart:convert';

import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/data_augment/notifiers/gan_notifiers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ModelStrutureViewer extends StatefulWidget {
  const ModelStrutureViewer({super.key, required this.modelId});
  final String modelId;

  @override
  State<ModelStrutureViewer> createState() => _ModelStrutureViewerState();
}

class _ModelStrutureViewerState extends State<ModelStrutureViewer> {
  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: MediaQuery.of(context).size.width * 0.9,
      height: MediaQuery.of(context).size.height * 0.9,
      child: Container(
        padding: const EdgeInsets.all(8),
        child: Consumer(
          builder: (context, ref, child) {
            final state = ref.watch(showModelStrutureProvider(widget.modelId));

            return state.when(
              data: (data) {
                if (data == "") {
                  return Center(child: Text("Un-supported Model"));
                }
                if (data.startsWith("data")) {
                  data = data.split(",").last;
                }
                final bytes = base64Decode(data);
                return InteractiveViewer(
                  maxScale: 4,
                  child: Image.memory(bytes),
                );
              },
              error: (error, stackTrace) {
                return Text("Error: $error");
              },
              loading: () {
                return const Center(child: CircularProgressIndicator());
              },
            );
          },
        ),
      ),
    );
  }
}
