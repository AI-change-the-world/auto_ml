import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';

class AppendAnntationFilesDialog extends StatefulWidget {
  const AppendAnntationFilesDialog({super.key, required this.annotationId});
  final int annotationId;

  @override
  State<AppendAnntationFilesDialog> createState() =>
      _AppendAnnotationFilesDialogState();
}

class _AppendAnnotationFilesDialogState
    extends State<AppendAnntationFilesDialog> {
  @override
  void dispose() {
    super.dispose();
  }

  static const XTypeGroup typeGroup = XTypeGroup(
    label: 'files',
    extensions: <String>['txt', 'json'],
  );

  List<XFile> files = [];

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: MediaQuery.of(context).size.width * 0.4,
      height: MediaQuery.of(context).size.height * 0.8,
      child: Container(
        padding: EdgeInsets.all(10),
        child: Column(
          spacing: 10,
          children: [
            Expanded(
              child: Container(
                padding: EdgeInsets.all(10),
                decoration: BoxDecoration(color: Colors.white),
                child: ListView.builder(
                  itemBuilder: (c, i) {
                    return Container(
                      margin: EdgeInsets.only(bottom: 10),
                      child: Row(
                        spacing: 10,
                        children: [
                          Icon(
                            Icons.file_upload,
                            size: Styles.datatableIconSize,
                          ),
                          Text(
                            files[i].name,
                            style: Styles.defaultButtonTextStyle,
                          ),
                        ],
                      ),
                    );
                  },
                  itemCount: files.length,
                ),
              ),
            ),
            SizedBox(
              height: 30,
              child: Row(
                spacing: 10,
                children: [
                  Spacer(),
                  ElevatedButton(
                    style: Styles.getDefaultButtonStyle(),
                    onPressed: () async {
                      files = await openFiles(acceptedTypeGroups: [typeGroup]);
                      if (files.isEmpty) {
                        return;
                      }
                      setState(() {});
                      // FormData formData = FormData.fromMap({"files": files});

                      List<MultipartFile> filesList = [];
                      for (var file in files) {
                        filesList.add(
                          MultipartFile.fromBytes(
                            await file.readAsBytes(),
                            filename: file.name,
                          ),
                        );
                      }
                      FormData formData = FormData.fromMap({
                        "files": filesList,
                      });

                      DioClient().instance
                          .post(
                            Api.appendAnnotationFiles.replaceAll(
                              "{id}",
                              widget.annotationId.toString(),
                            ),
                            data: formData,
                          )
                          .then((v) {
                            if (v.data != null) {
                              ToastUtils.info(
                                null,
                                title: t.dataset_screen.add_annotation
                                    .res_message(message: v.data["message"]),
                              );
                            }
                          });
                    },
                    child: Text(
                      t.dataset_screen.add_annotation.add_file,
                      style: Styles.defaultButtonTextStyle,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
