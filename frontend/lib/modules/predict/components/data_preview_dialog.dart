// ignore_for_file: prefer_typing_uninitialized_variables

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_response.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:flutter/material.dart';
import 'package:he/he.dart';
import 'package:media_kit/media_kit.dart';
import 'package:media_kit_video/media_kit_video.dart';

class DataPreviewDialog extends StatefulWidget {
  const DataPreviewDialog({
    super.key,
    required this.fileId,
    required this.fileType,
  });
  final int fileId;
  final int fileType;

  @override
  State<DataPreviewDialog> createState() => _DataPreviewDialogState();
}

class _DataPreviewDialogState extends State<DataPreviewDialog> {
  late Future<String> future;
  final dio = DioClient().instance;

  // Create a [Player] to control playback.
  late final player = Player();
  // Create a [VideoController] to handle video output from [Player].
  late final controller = VideoController(player);

  @override
  void initState() {
    super.initState();
    future = getData();
  }

  @override
  void dispose() {
    player.dispose();
    super.dispose();
  }

  Future<String> getData() async {
    try {
      final response = await dio.get(
        Api.getPreview.replaceAll("{id}", widget.fileId.toString()),
      );
      BaseResponse<FilePreviewResponse> baseResponse = BaseResponse.fromJson(
        response.data,
        (json) => FilePreviewResponse.fromJson(json as Map<String, dynamic>),
      );
      return baseResponse.data?.content ?? "";
    } catch (e) {
      logger.e(e);
      return "";
    }
  }

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: MediaQuery.of(context).size.width * 0.8,
      height: MediaQuery.of(context).size.height * 0.8,
      child: FutureBuilder(
        future: future,
        builder: (c, s) {
          return s.when(
            data: (data) {
              if (widget.fileType == 1) {
                return Image.network(data.toString());
              }
              if (widget.fileType == 2) {
                player.open(Media(data.toString()));
                return Video(controller: controller);
              }

              return Text(data.toString());
            },
            error: (Object error, StackTrace stackTrace) {
              return Center(child: CircularProgressIndicator());
            },
            loading: () {
              return Center(child: CircularProgressIndicator());
            },
          );
        },
      ),
    );
  }
}
