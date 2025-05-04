import 'package:auto_ml/modules/annotation/models/new_annotation_request.dart';
import 'package:auto_ml/modules/dataset/components/annotations_list.dart';
import 'package:auto_ml/modules/dataset/components/dataset_file_details.dart';
import 'package:auto_ml/modules/dataset/components/new_annotation_dialog.dart';
import 'package:auto_ml/modules/dataset/notifier/annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
// ignore: depend_on_referenced_packages
import 'package:collection/collection.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DatasetDetailsWidget extends ConsumerStatefulWidget {
  const DatasetDetailsWidget({super.key});

  @override
  ConsumerState<DatasetDetailsWidget> createState() =>
      _DatasetDetailsWidgetState();
}

class _DatasetDetailsWidgetState extends ConsumerState<DatasetDetailsWidget> {
  final PageController _pageController = PageController();
  int currentPageIndex = 0;
  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();

    _pageController.addListener(() {
      final newPage = _pageController.page?.round() ?? 0;
      if (newPage != currentPageIndex) {
        setState(() {
          currentPageIndex = newPage;
        });
      }
    });
  }

  late List<Widget> widgets = [DatasetFileDetails(), AnnotationsList()];

  @override
  Widget build(BuildContext context) {
    final current = ref.read(datasetNotifierProvider).value?.current;

    return Material(
      borderRadius: BorderRadius.only(
        topLeft: Radius.circular(10),
        bottomLeft: Radius.circular(10),
      ),
      elevation: 10,
      child: Container(
        padding: EdgeInsets.all(10),
        width: MediaQuery.of(context).size.width * 0.8,
        height: double.infinity,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(10),
            bottomLeft: Radius.circular(10),
          ),
        ),
        child: Column(
          children: [
            Text(
              "Id: ${current?.id} Name: ${current?.name}",
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 5),
            SizedBox(
              height: 35,
              child: Row(
                spacing: 10,
                children: [
                  ...["Details", "Annotations"].mapIndexed((i, entry) {
                    return Column(
                      children: [
                        SizedBox(
                          height: 30,
                          child: InkWell(
                            borderRadius: BorderRadius.circular(4),
                            child: Ink(
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.only(
                                  topLeft: Radius.circular(4),
                                  topRight: Radius.circular(4),
                                ),
                              ),
                              width: 100,
                              height: 28,
                              child: Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                spacing: 5,
                                children: [
                                  Text(
                                    entry,
                                    style: TextStyle(
                                      fontWeight:
                                          i == currentPageIndex
                                              ? FontWeight.bold
                                              : null,
                                      color:
                                          i == currentPageIndex
                                              ? Colors.black
                                              : Colors.grey,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            onTap: () {
                              _pageController.jumpToPage(i);
                            },
                          ),
                        ),
                        Spacer(),
                        Container(
                          width: 100,
                          height: 2,
                          color:
                              i == currentPageIndex
                                  ? color
                                  : Colors.transparent,
                        ),
                      ],
                    );
                  }),
                  Spacer(),
                  Material(
                    borderRadius: BorderRadius.circular(20),
                    child: MouseRegion(
                      cursor: SystemMouseCursors.click,
                      child: GestureDetector(
                        onTap: () async {
                          if (currentPageIndex == 1) {
                            showGeneralDialog(
                              barrierColor: Styles.barriarColor,
                              barrierDismissible: true,
                              barrierLabel: "NewAnnotationDialog",
                              context: context,
                              pageBuilder: (c, _, __) {
                                return Center(child: NewAnnotationDialog());
                              },
                            ).then((v) {
                              if (v != null && v is Map<String, dynamic>) {
                                NewAnnotationRequest request =
                                    NewAnnotationRequest(
                                      datasetId: current!.id,
                                      storageType: v['storageType'],
                                      savePath: v['labelPath'],
                                      username: v['username'],
                                      password: v['password'],
                                      type: v['type'],
                                      classes: v['classes'],
                                    );

                                ref
                                    .read(annotationListProvider.notifier)
                                    .newAnnotation(request);
                              }
                            });
                          }
                        },
                        child: Container(
                          decoration: BoxDecoration(
                            color: Colors.green,
                            borderRadius: BorderRadius.circular(20),
                          ),
                          padding: EdgeInsets.all(1),
                          child: Icon(
                            currentPageIndex == 0 ? Icons.refresh : Icons.add,
                            color: Colors.white,
                            size: 18,
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Divider(height: 0.5),
            SizedBox(height: 10),
            Expanded(
              child: PageView.builder(
                itemBuilder: (ctx, index) {
                  return PageView.builder(
                    physics: NeverScrollableScrollPhysics(),
                    controller: _pageController,
                    itemCount: 2,
                    itemBuilder: (context, index) {
                      final isVisible = index == currentPageIndex;

                      return isVisible
                          ? widgets[index]
                          : const SizedBox.shrink(); // 不渲染页面
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  static const Color color = Color.fromARGB(255, 118, 156, 222);
}
