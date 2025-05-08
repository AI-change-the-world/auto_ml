import 'dart:async';

import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/api.dart';
import 'package:auto_ml/modules/annotation/models/api/new_annotation_request.dart';
import 'package:auto_ml/modules/dataset/models/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/notifier/annotation_state.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class GlobalDrawer {
  GlobalDrawer._();
  static GlobalKey<ScaffoldState> scaffoldKey = GlobalKey<ScaffoldState>();

  static showDrawer() {
    GlobalDrawer.scaffoldKey.currentState?.openEndDrawer();
  }

  static hideDrawer() {
    GlobalDrawer.scaffoldKey.currentState?.closeEndDrawer();
  }
}

class AnnotationNotifier extends AutoDisposeAsyncNotifier<AnnotationState> {
  final dio = DioClient().instance;

  @override
  FutureOr<AnnotationState> build() async {
    // final _ = ref.keepAlive();
    ref.onDispose(() {
      logger.d('AnnotationNotifier disposed');
    });
    return AnnotationState(annotations: []);
  }

  Future<void> updateData() async {
    final current = ref.read(datasetNotifierProvider).value?.current;
    if (current == null) {
      return;
    }
    state = AsyncLoading();

    state = await AsyncValue.guard(() async {
      try {
        final r = await dio.get(
          Api.getAnnotationByDatasetId.replaceAll(
            "{id}",
            current.id.toString(),
          ),
        );
        final res = BaseResponse.fromJson(
          r.data,
          (v) => AnnotationListResponse.fromJson({"annotations": v}),
        );

        return AnnotationState(annotations: res.data?.annotations ?? []);
      } catch (e) {
        logger.e(e);
        ToastUtils.error(
          null,
          title: "Failed to get annotations",
          description: e.toString(),
        );
        return AnnotationState(annotations: []);
      }
    });
  }

  newAnnotation(NewAnnotationRequest request) async {
    try {
      final response = await dio.post(
        Api.annotationNew,
        data: request.toJson(),
      );
      final r = BaseResponse.fromJson(response.data, (json) => null);
      if (r.code == 200) {
        ToastUtils.sucess(null, title: "New annotation success");
        updateData();
      } else {
        ToastUtils.error(null, title: "New annotation failed");
      }
    } catch (e) {
      logger.e("error: $e");
      ToastUtils.error(null, title: "Create annotation error");
    }
  }
}

final annotationListProvider =
    AutoDisposeAsyncNotifierProvider<AnnotationNotifier, AnnotationState>(
      AnnotationNotifier.new,
    );
