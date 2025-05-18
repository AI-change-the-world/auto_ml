import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/dataset/models/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_request.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_response.dart';
import 'package:auto_ml/modules/dataset/models/get_all_dataset_response.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final getDatasetPreview = FutureProvider.autoDispose
    .family<String, (Dataset, String)>((ref, d) async {
      try {
        final request = FilePreviewRequest(
          baseUrl: d.$1.localS3StoragePath ?? "",
          storageType: d.$1.storageType,
          path: d.$2,
        );

        final response = await DioClient().instance.post(
          Api.preview,
          data: request.toJson(),
        );
        if (response.statusCode == 200) {
          BaseResponse<FilePreviewResponse> baseResponse =
              BaseResponse.fromJson(
                response.data,
                (j) => FilePreviewResponse.fromJson(j as Map<String, dynamic>),
              );

          return baseResponse.data?.content ?? "";
        } else {
          throw Exception('Failed to load task detail');
        }
      } catch (e) {
        logger.e(e);
        ToastUtils.error(null, title: "Failed to get image");
        return "";
      }
    });

final getAnnotationContent = FutureProvider.autoDispose
    .family<String, (Annotation, String)>((ref, a) async {
      try {
        final request2 = FilePreviewRequest(
          baseUrl: a.$1.annotationSavePath ?? "",
          storageType: 1,
          path: a.$2,
        );

        final response = await DioClient().instance.post(
          Api.annotationContent,
          data: request2.toJson(),
        );
        if (response.statusCode == 200) {
          BaseResponse<FilePreviewResponse> baseResponse =
              BaseResponse.fromJson(
                response.data,
                (j) => FilePreviewResponse.fromJson(j as Map<String, dynamic>),
              );

          return baseResponse.data?.content ?? "";
        } else {
          throw Exception('Failed to load task detail');
        }
      } catch (e) {
        logger.e(e);
        ToastUtils.error(null, title: "Failed to get image");
        return "";
      }
    });
