import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_page_result.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/deploy/model/available_models_response.dart';
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
}

final deployNotifierProvider =
    AutoDisposeAsyncNotifierProvider<DeployNotifier, DeployState>(() {
      return DeployNotifier();
    });
