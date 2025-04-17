import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/dataset/entity/get_all_dataset_response.dart'
    as ds;
import 'package:auto_ml/modules/label/notifiers/label_state.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LabelNotifier
    extends
        AutoDisposeFamilyAsyncNotifier<
          LabelState,
          /* dataset id , annotation id*/ (int, int)
        > {
  final dio = DioClient().instance;

  @override
  FutureOr<LabelState> build((int, int) arg) async {
    try {
      final response = await dio.get(
        Api.details.replaceAll("{id}", arg.$1.toString()),
      );
      final d = BaseResponse.fromJson(
        response.data,
        (json) => ds.Dataset.fromJson(json as Map<String, dynamic>),
      );

      /// TODO: get annotaion
      return LabelState(dataPath: d.data?.url ?? "", labelPath: "");
    } catch (e) {
      return LabelState(dataPath: "", labelPath: "");
    }
  }

  /// add dataset pair TODO remove later
  addDatasetPair(String dataPath, String labelPath) {
    state.value!.dataLabelPairs.add(MapEntry(dataPath, labelPath));
  }

  // void nextData() async {
  //   if (state.dataLabelPairs.isEmpty) {
  //     return;
  //   }

  //   if (state.dataLabelPairs.indexWhere((v) => v.key == state.current) ==
  //       state.dataLabelPairs.length - 1) {
  //     return;
  //   }

  //   String current = "";
  //   String label = "";
  //   List<Annotation> annotations = [];

  //   if (state.current == "") {
  //     // first data
  //     current = state.dataLabelPairs.first.key;
  //     label = state.dataLabelPairs.first.value;

  //     if (label != "") {
  //       Size imageSize = await getImageSizeAsync(FileImage(File(current)));
  //       annotations = parseYoloAnnotations(
  //         label,
  //         imageSize.width,
  //         imageSize.height,
  //       );
  //     }
  //     state = state.copyWith(current: current, currentLabels: annotations);
  //   } else {
  //     current =
  //         state
  //             .dataLabelPairs[state.dataLabelPairs.indexWhere(
  //                   (v) => v.key == state.current,
  //                 ) +
  //                 1]
  //             .key;
  //     label =
  //         state
  //             .dataLabelPairs[state.dataLabelPairs.indexWhere(
  //                   (v) => v.key == state.current,
  //                 ) +
  //                 1]
  //             .value;
  //     if (label != "") {
  //       Size imageSize = await getImageSizeAsync(FileImage(File(current)));
  //       annotations = parseYoloAnnotations(
  //         label,
  //         imageSize.width,
  //         imageSize.height,
  //       );
  //     }
  //     state = state.copyWith(current: current, currentLabels: annotations);
  //   }
  // }
}

final labelNotifierProvider = AutoDisposeAsyncNotifierProvider.family<
  LabelNotifier,
  LabelState,
  (int, int)
>(LabelNotifier.new);
