import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/dataset/entity/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/entity/get_all_dataset_response.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SelectDatasetAnnotationState {
  final List<Dataset> datasets;
  final Map<int, List<Annotation>> anntations;

  final int currentDatasetId;

  SelectDatasetAnnotationState({
    this.datasets = const [],
    this.anntations = const {},
    this.currentDatasetId = 0,
  });

  SelectDatasetAnnotationState copyWith({
    List<Dataset>? datasets,
    Map<int, List<Annotation>>? anntations,
    int? currentDatasetId,
  }) {
    return SelectDatasetAnnotationState(
      datasets: datasets ?? this.datasets,
      anntations: anntations ?? this.anntations,
      currentDatasetId: currentDatasetId ?? this.currentDatasetId,
    );
  }
}

class SelectDatasetAnnotationNotifier
    extends AutoDisposeAsyncNotifier<SelectDatasetAnnotationState> {
  final dio = DioClient().instance;

  @override
  FutureOr<SelectDatasetAnnotationState> build() async {
    final response = await dio.get(Api.getAllDatasets);
    try {
      final d = BaseResponse.fromJson(
        response.data,
        (json) => GetAllDatasetResponse.fromJson({"datasets": json}),
      );
      if (d.data != null) {
        return SelectDatasetAnnotationState(datasets: d.data!.datasets);
      }
      return SelectDatasetAnnotationState(datasets: []);
    } catch (e) {
      logger.e(e);
      ToastUtils.error(null, title: "Get dataset failed");
      return SelectDatasetAnnotationState(datasets: []);
    }
  }

  onDatasetSelectionChanged(int datasetId) async {
    // state = AsyncLoading();
    if (state.value!.anntations.keys.contains(datasetId)) {
      state = AsyncValue.data(
        SelectDatasetAnnotationState(
          datasets: state.value!.datasets,
          anntations: state.value!.anntations,
          currentDatasetId: datasetId,
        ),
      );
      return;
    }

    state = await AsyncValue.guard(() async {
      try {
        final r = await dio.get(
          Api.getAnnotationByDatasetId.replaceAll("{id}", datasetId.toString()),
        );
        final res = BaseResponse.fromJson(
          r.data,
          (v) => AnnotationListResponse.fromJson({"annotations": v}),
        );

        // return AnnotationState(annotations: res.data?.annotations ?? []);
        return SelectDatasetAnnotationState(
          datasets: state.value!.datasets,
          anntations: {
            ...state.value!.anntations,
            datasetId: res.data?.annotations ?? [],
          },
          currentDatasetId: datasetId,
        );
      } catch (e) {
        logger.e(e);
        ToastUtils.error(
          null,
          title: "Failed to get annotations",
          description: e.toString(),
        );
        return SelectDatasetAnnotationState();
      }
    });
  }
}

final selectDatasetAnnotationNotifierProvider =
    AutoDisposeAsyncNotifierProvider<
      SelectDatasetAnnotationNotifier,
      SelectDatasetAnnotationState
    >(SelectDatasetAnnotationNotifier.new);
