import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_page_result.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/task/models/paginate_request.dart';
import 'package:auto_ml/modules/task/models/task.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class TaskState {
  final int pageId;
  final int pageSize;
  final List<Task> tasks;
  final int total;

  TaskState({
    this.pageId = 1,
    this.pageSize = 10,
    this.tasks = const [],
    this.total = 0,
  });

  TaskState copyWith({
    int? pageId,
    int? pageSize,
    List<Task>? tasks,
    int? total,
  }) {
    return TaskState(
      pageId: pageId ?? this.pageId,
      pageSize: pageSize ?? this.pageSize,
      tasks: tasks ?? this.tasks,
      total: total ?? this.total,
    );
  }
}

class TaskNotifier extends AutoDisposeAsyncNotifier<TaskState> {
  final dioInstance = DioClient().instance;
  @override
  FutureOr<TaskState> build() async {
    try {
      PaginateRequest paginateRequest = PaginateRequest(
        pageId: 1,
        pageSize: 10,
      );
      final response = await dioInstance.post(
        Api.taskList,
        data: paginateRequest.toJson(),
      );

      final bs = BaseResponse<BasePageResult<Task>>.fromJson(
        response.data,
        (d) => BasePageResult.fromJson(d as Map<String, dynamic>, (j) {
          return Task.fromJson(j);
        }),
      );

      return TaskState(
        tasks: bs.data?.records ?? [],
        total: bs.data?.total ?? 0,
      );
    } catch (e, s) {
      logger.e(e);
      logger.e(s);
      ToastUtils.error(null, title: "Get Task Error");
      return TaskState();
    }
  }

  nextPage(int totalPage) async {
    if (state.value!.pageId == totalPage) {
      return;
    }

    state = await AsyncValue.guard(() async {
      try {
        PaginateRequest paginateRequest = PaginateRequest(
          pageId: state.value!.pageId + 1,
          pageSize: 10,
        );
        final response = await dioInstance.post(
          Api.taskList,
          data: paginateRequest.toJson(),
        );

        final bs = BaseResponse<BasePageResult<Task>>.fromJson(
          response.data,
          (d) => BasePageResult.fromJson(d as Map<String, dynamic>, (j) {
            return Task.fromJson(j);
          }),
        );

        return TaskState(
          pageId: state.value!.pageId + 1,
          tasks: bs.data?.records ?? [],
          total: bs.data?.total ?? 0,
        );
      } catch (e, s) {
        logger.e(e);
        logger.e(s);
        ToastUtils.error(null, title: "Get Task Error");
        return TaskState();
      }
    });
  }

  prevPage() async {
    if (state.value!.pageId == 1) {
      return;
    }

    state = await AsyncValue.guard(() async {
      try {
        PaginateRequest paginateRequest = PaginateRequest(
          pageId: state.value!.pageId - 1,
          pageSize: 10,
        );
        final response = await dioInstance.post(
          Api.taskList,
          data: paginateRequest.toJson(),
        );

        final bs = BaseResponse<BasePageResult<Task>>.fromJson(
          response.data,
          (d) => BasePageResult.fromJson(d as Map<String, dynamic>, (j) {
            return Task.fromJson(j);
          }),
        );

        return TaskState(
          pageId: state.value!.pageId - 1,
          tasks: bs.data?.records ?? [],
          total: bs.data?.total ?? 0,
        );
      } catch (e, s) {
        logger.e(e);
        logger.e(s);
        ToastUtils.error(null, title: "Get Task Error");
        return TaskState();
      }
    });
  }
}

final taskNotifierProvider =
    AutoDisposeAsyncNotifierProvider<TaskNotifier, TaskState>(() {
      return TaskNotifier();
    });
