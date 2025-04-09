import 'dart:async';
import 'dart:convert';

import 'package:auto_ml/modules/isar/model.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/services.dart';
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

  tryModel(
    String modelName,
    String baseUrl,
    ModelType type, {
    String? apiKey,
  }) async {
    logger.d("try model $type");
    try {
      late final ChatOpenAI chatOpenAI = ChatOpenAI(
        apiKey: apiKey,
        baseUrl: baseUrl,
        // modelName: widget.modelName,
        defaultOptions: ChatOpenAIOptions(model: modelName),
      );
      if (type == ModelType.llm) {
        final String prompt = """
      hello
      """;
        chatOpenAI.stream(PromptValue.string(prompt)).listen((e) {
          // logger.d(e.output.content);
          tryModelController.sink.add(e.output.content);
        });
      } else {
        final String prompt = """
      Describe this image
      """;
        final bytes =
            (await rootBundle.load("assets/test.png")).buffer.asUint8List();

        final base64Data = base64Encode(bytes);
        final imageData = 'data:image/png;base64,$base64Data';

        chatOpenAI
            .stream(
              PromptValue.chat([
                ChatMessage.human(
                  ChatMessageContent.image(
                    data: imageData,
                    mimeType: "image/png",
                  ),
                ),
                ChatMessage.humanText(prompt),
              ]),
            )
            .listen((e) {
              // logger.d(e.output.content);
              tryModelController.sink.add(e.output.content);
            });
      }
    } catch (e) {
      logger.e(e);
      ToastUtils.error(null, title: "error chat with AI");
    }
  }
}

final modelDialogNotifierProvider =
    AutoDisposeNotifierProvider<ModelDialogNotifier, bool>(
      ModelDialogNotifier.new,
    );
