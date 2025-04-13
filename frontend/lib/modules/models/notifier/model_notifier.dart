import 'dart:async';

import 'package:auto_ml/modules/models/notifier/model_state.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ModelNotifier extends AutoDisposeAsyncNotifier<ModelState> {
  @override
  FutureOr<ModelState> build() async {
    return ModelState(models: []);
  }
}

final modelNotifierProvider =
    AutoDisposeAsyncNotifierProvider<ModelNotifier, ModelState>(
      ModelNotifier.new,
    );
