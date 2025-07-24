import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/dataset/models/get_all_dataset_response.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final showModelStrutureProvider =
    AutoDisposeFutureProvider.family<String, String>((ref, arg) async {
      final dio = Dio();
      final response = await dio.get(Api.graph.replaceAll("{model_id}", arg));

      if (response.statusCode == 200 && response.data != null) {
        return response.data["data"];
      }

      return "";
    }, name: "sdClientIsOnProvider");

final getAllDatasetProvider = AutoDisposeFutureProvider<List<String>>((
  ref,
) async {
  final client = DioClient().instance;
  final response = await client.get(Api.getAllDatasets);
  try {
    final d = BaseResponse.fromJson(
      response.data,
      (json) => GetAllDatasetResponse.fromJson({"datasets": json}),
    );
    if (d.data != null) {
      return d.data!.datasets.map((e) => e.name).toList();
    }
    logger.w("No dataset");
    return [];
  } catch (e) {
    logger.e(e);
    return [];
  }
}, name: "getAllDatasetProvider");
