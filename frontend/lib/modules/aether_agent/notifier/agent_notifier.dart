import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_page_result.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/aether_agent/models/agent_response.dart';
import 'package:auto_ml/modules/task/models/paginate_request.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AgentState {
  final List<Agent> agents;
  final int pageId;
  final int pageSize;
  final int total;

  AgentState({
    required this.agents,
    this.pageId = 1,
    this.pageSize = 10,
    this.total = 0,
  });

  AgentState copyWith({
    List<Agent>? agents,
    int? pageId,
    int? pageSize,
    int? total,
  }) {
    return AgentState(
      agents: agents ?? this.agents,
      pageId: pageId ?? this.pageId,
      pageSize: pageSize ?? this.pageSize,
      total: total ?? this.total,
    );
  }
}

class AgentNotifier extends AutoDisposeAsyncNotifier<AgentState> {
  final dio = DioClient().instance;

  @override
  FutureOr<AgentState> build() async {
    PaginateRequest request = PaginateRequest(pageId: 1, pageSize: 10);
    try {
      final response = await dio.post(
        Api.aetherAgentList,
        data: request.toJson(),
      );

      BaseResponse<BasePageResult<Agent>> result = BaseResponse.fromJson(
        response.data,
        (json) => BasePageResult<Agent>.fromJson(
          json as Map<String, dynamic>,
          (json) => Agent.fromJson(json),
        ),
      );

      return AgentState(
        agents: result.data?.records ?? [],
        pageId: 1,
        pageSize: 10,
        total: result.data?.total ?? 0,
      );
    } catch (e) {
      ToastUtils.error(null, title: "Error get agent list");
      logger.e(e);
      return AgentState(agents: [], pageId: 1, pageSize: 10, total: 0);
    }
  }
}

final agentProvider =
    AutoDisposeAsyncNotifierProvider<AgentNotifier, AgentState>(() {
      return AgentNotifier();
    });
