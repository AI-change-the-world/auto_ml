// ignore_for_file: avoid_init_to_null

import 'dart:convert';
import 'dart:typed_data';

import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/modules/deploy/models/predict_single_image_request.dart';
import 'package:auto_ml/modules/deploy/notifier/predict_single_image_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class PredictSingleImageDialog extends StatefulWidget {
  const PredictSingleImageDialog({super.key, required this.modelId});
  final int modelId;

  @override
  State<PredictSingleImageDialog> createState() =>
      _PredictSingleImageDialogState();
}

class _PredictSingleImageDialogState extends State<PredictSingleImageDialog> {
  static const XTypeGroup typeGroup = XTypeGroup(
    label: 'images',
    extensions: <String>['jpg', 'png', 'jpeg'],
  );

  Uint8List? image;
  PredictSingleImageRequest? _request;

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: MediaQuery.of(context).size.width * 0.9,
      height: MediaQuery.of(context).size.height * 0.9,
      child: Container(
        padding: EdgeInsets.all(10),
        child: Row(
          children: [
            Expanded(
              flex: 1,
              child:
                  image == null
                      ? Column(
                        spacing: 10,
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Text(
                            "No image selected",
                            style: Styles.defaultButtonTextStyle,
                          ),
                          ElevatedButton(
                            style: ButtonStyle(
                              fixedSize: WidgetStateProperty.all(Size(200, 20)),
                              backgroundColor: WidgetStatePropertyAll(
                                Colors.grey[300],
                              ),
                              padding: WidgetStatePropertyAll(
                                const EdgeInsets.symmetric(
                                  horizontal: 16,
                                  vertical: 12,
                                ),
                              ),
                              textStyle: WidgetStatePropertyAll(
                                const TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w400,
                                ),
                              ),
                              shape: WidgetStatePropertyAll(
                                RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(4.0),
                                ),
                              ),
                            ),
                            onPressed: pickImageFile,
                            child: Text(
                              "Select Image",
                              style: Styles.defaultButtonTextStyle,
                            ),
                          ),
                        ],
                      )
                      : InkWell(
                        onTap: pickImageFile,
                        child: Image.memory(image!),
                      ),
            ),
            if (image != null && _request != null)
              Expanded(
                flex: 1,
                child: Consumer(
                  builder: (ctx, ref, _) {
                    final predictDetail = ref.watch(
                      predictSingleImageProvider(_request!),
                    );
                    return predictDetail.when(
                      data: (d) => Container(),
                      error: (e, _) => Center(child: Text(e.toString())),
                      loading: () => Center(child: CircularProgressIndicator()),
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future pickImageFile() async {
    final XFile? file = await openFile(acceptedTypeGroups: [typeGroup]);
    if (file != null) {
      final bytes = await file.readAsBytes();
      final req = PredictSingleImageRequest(
        modelId: widget.modelId,
        data: base64Encode(bytes),
      );
      setState(() {
        image = bytes;
        _request = req;
      });
      // ignore: use_build_context_synchronously
      final container = ProviderScope.containerOf(context);
      container.refresh(predictSingleImageProvider(_request!));
    }
  }
}
