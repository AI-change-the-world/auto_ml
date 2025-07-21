import 'package:auto_ml/api.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final sdClientIsOnProvider = AutoDisposeFutureProvider<bool>((ref) async {
  final dio = Dio();
  final response = await dio.get(Api.sdIsOn);

  if (response.statusCode == 200 && response.data != null) {
    return response.data["data"];
  }

  return false;
}, name: "sdClientIsOnProvider");
