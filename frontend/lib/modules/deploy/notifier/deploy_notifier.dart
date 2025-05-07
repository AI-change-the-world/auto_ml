import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_page_result.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/deploy/models/available_models_response.dart';
import 'package:auto_ml/modules/deploy/models/running_models_response.dart';
import 'package:auto_ml/modules/task/models/paginate_request.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DeployState {
  final int pageId;
  final int pageSize;
  final List<AvailableModel> models;
  final int total;

  DeployState({
    this.pageId = 1,
    this.pageSize = 10,
    this.models = const [],
    this.total = 0,
  });

  DeployState copyWith({
    int? pageId,
    int? pageSize,
    List<AvailableModel>? models,
    int? total,
  }) {
    return DeployState(
      pageId: pageId ?? this.pageId,
      pageSize: pageSize ?? this.pageSize,
      models: models ?? this.models,
      total: total ?? this.total,
    );
  }
}

class DeployNotifier extends AutoDisposeAsyncNotifier<DeployState> {
  final dioInstance = DioClient().instance;
  @override
  FutureOr<DeployState> build() async {
    try {
      PaginateRequest paginateRequest = PaginateRequest(
        pageId: 1,
        pageSize: 10,
      );
      final response = await dioInstance.post(
        Api.deployList,
        data: paginateRequest.toJson(),
      );

      final bs = BaseResponse<BasePageResult<AvailableModel>>.fromJson(
        response.data,
        (d) => BasePageResult.fromJson(d as Map<String, dynamic>, (j) {
          return AvailableModel.fromJson(j);
        }),
      );

      final response2 = await dioInstance.get(Api.runningModels);

      final rbs = BaseResponse<RunningModelsResponse>.fromJson(response2.data, (
        d,
      ) {
        return RunningModelsResponse.fromJson(d as Map<String, dynamic>);
      });

      for (final model in bs.data?.records ?? []) {
        model.isOn = rbs.data?.runningModels.contains(model.id) ?? false;
      }

      return DeployState(
        models: bs.data?.records ?? [],
        total: bs.data?.total ?? 0,
      );
    } catch (e, s) {
      logger.e(e);
      logger.e(s);
      ToastUtils.error(null, title: "Get Deploy Error");
      return DeployState();
    }
  }

  refreshStartStopStatus(int modelId) async {
    state = AsyncLoading();
    state = await AsyncValue.guard(() async {
      return state.value!.copyWith(
        models:
            state.value!.models.map((e) {
              if (e.id == modelId) {
                e.isOn = !e.isOn;
              }
              return e;
            }).toList(),
      );
    });
  }

  startModel(int id) async {
    try {
      final rbs = await dioInstance.get(
        Api.startModel.replaceAll("{id}", id.toString()),
      );
      if (rbs.data['code'] != 200) {
        ToastUtils.error(null, title: "Start Model Error");
        return;
      }
      ToastUtils.sucess(null, title: "Start Model Success");
      refreshStartStopStatus(id);
    } catch (e, s) {
      logger.e(e);
      logger.e(s);
      ToastUtils.error(null, title: "Start Model Error");
    }
  }

  stopModel(int id) async {
    try {
      final rbs = await dioInstance.get(
        Api.stopModel.replaceAll("{id}", id.toString()),
      );
      if (rbs.data['code'] != 200) {
        ToastUtils.error(null, title: "Stop Model Error");
        return;
      }
      ToastUtils.sucess(null, title: "Stop Model Success");
      refreshStartStopStatus(id);
    } catch (e, s) {
      logger.e(e);
      logger.e(s);
      ToastUtils.error(null, title: "Stop Model Error");
    }
  }
}

final deployNotifierProvider =
    AutoDisposeAsyncNotifierProvider<DeployNotifier, DeployState>(() {
      return DeployNotifier();
    });
