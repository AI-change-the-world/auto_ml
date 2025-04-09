import 'dart:async';

import 'package:auto_ml/modules/isar/model.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:langchain/langchain.dart';
import 'package:langchain_openai/langchain_openai.dart';

class ModelDialogNotifier extends AutoDisposeNotifier<bool> {
  @override
  bool build() {
    ref.onDispose(() {
      tryModelController.close();
    });
    return false;
  }

  changeState() {
    state = !state;
  }

  final StreamController<String> tryModelController =
      StreamController<String>.broadcast();

  late final Stream<String> tryModelStream = tryModelController.stream;

  tryModel(String modelName, String baseUrl, ModelType type, {String? apiKey}) {
    if (type == ModelType.llm) {
      final String prompt = """
      You are a helpful assistant.
      Introduce yourself.
      """;
      try {
        late final ChatOpenAI chatOpenAI = ChatOpenAI(
          apiKey: apiKey,
          baseUrl: baseUrl,
          // modelName: widget.modelName,
          defaultOptions: ChatOpenAIOptions(model: modelName),
        );
        chatOpenAI.stream(PromptValue.string(prompt)).listen((e) {
          // logger.d(e.output.content);
          tryModelController.sink.add(e.output.content);
        });
      } catch (e) {
        logger.e(e);
        ToastUtils.error(null, title: "error chat with AI");
      }
    }
  }
}

final modelDialogNotifierProvider =
    AutoDisposeNotifierProvider<ModelDialogNotifier, bool>(
      ModelDialogNotifier.new,
    );
