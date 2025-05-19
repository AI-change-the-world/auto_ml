// ignore_for_file: avoid_init_to_null

import 'package:auto_ml/modules/annotation/components/file_list.dart';
import 'package:auto_ml/modules/annotation/notifiers/request_notifier.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/models/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/models/get_all_dataset_response.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ClsAnnotationWidget extends ConsumerStatefulWidget {
  const ClsAnnotationWidget({super.key, required this.data});
  final List<(String, String)> data;

  @override
  ConsumerState<ClsAnnotationWidget> createState() =>
      _ClsAnnotationWidgetState();
}

class _ClsAnnotationWidgetState extends ConsumerState<ClsAnnotationWidget> {
  late Dataset? currentDataset = null;
  late Annotation? currentAnnotation = null;
  late String selectedImage = "";
  late String annotationClass = "";

  @override
  Widget build(BuildContext context) {
    final state = ref.read(currentDatasetAnnotationNotifierProvider);
    currentDataset = state.dataset;
    currentAnnotation = state.annotation;

    selectedImage = state.currentData?.$1 ?? "";

    logger.d("currentData: $selectedImage");

    return Row(
      children: [
        FileList(data: widget.data),
        Expanded(
          flex: 2,
          child: Container(
            padding: EdgeInsets.all(10),
            child: Container(
              height: double.infinity,
              decoration: BoxDecoration(color: Colors.white),
              child: Center(
                child: Consumer(
                  builder: (c, ref, _) {
                    if (currentDataset == null || selectedImage == "") {
                      return Text(
                        "No image selected",
                        style: Styles.defaultButtonTextStyle,
                      );
                    }

                    final asyncDetail = ref.watch(
                      getDatasetPreview((currentDataset!, selectedImage)),
                    );

                    return asyncDetail.when(
                      data: (data) {
                        return Image.network(data, fit: BoxFit.contain);
                      },
                      error: (e, _) {
                        return Text("Error: $e");
                      },
                      loading: () {
                        return CircularProgressIndicator();
                      },
                    );
                  },
                ),
              ),
            ),
          ),
        ),
        Expanded(
          flex: 1,
          child: Container(
            child:
                currentAnnotation?.classItems == null
                    ? Center(
                      child: Text(
                        "No classes found, please add at least 2 class",
                        style: Styles.defaultButtonTextStyle,
                      ),
                    )
                    : Container(
                      height: double.infinity,
                      width: double.infinity,
                      padding: EdgeInsets.all(10),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        spacing: 10,
                        children: [
                          Center(
                            child: Text(
                              "Supported classes",
                              style: Styles.defaultButtonTextStyle,
                            ),
                          ),
                          Expanded(
                            child: Wrap(
                              spacing: 10,
                              runSpacing: 10,
                              alignment: WrapAlignment.start,
                              runAlignment: WrapAlignment.start,
                              children:
                                  currentAnnotation!.classItems!.split(";").map(
                                    (e) {
                                      return InkWell(
                                        onTap: () {
                                          if (selectedImage == "") {
                                            ToastUtils.info(
                                              context,
                                              title: "No image selected",
                                            );
                                            return;
                                          }
                                        },
                                        child: Container(
                                          decoration: BoxDecoration(
                                            border: Border.all(
                                              color: Colors.grey[200]!,
                                            ),
                                          ),
                                          alignment: Alignment.centerLeft,
                                          padding: EdgeInsets.only(
                                            left: 5,
                                            right: 5,
                                          ),
                                          height: 30,
                                          width: 100,
                                          child: Text(
                                            e,
                                            style:
                                                Styles.defaultButtonTextStyle,
                                          ),
                                        ),
                                      );
                                    },
                                  ).toList(),
                            ),
                          ),
                        ],
                      ),
                    ),
          ),
        ),
      ],
    );
  }
}
