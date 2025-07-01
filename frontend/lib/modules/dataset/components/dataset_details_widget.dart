import 'dart:ui';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/download/download.dart';
import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/annotation/models/api/new_annotation_request.dart';
import 'package:auto_ml/modules/dataset/components/annotations_list.dart';
import 'package:auto_ml/modules/dataset/components/dataset_file_details.dart';
import 'package:auto_ml/modules/dataset/components/new_annotation_dialog.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/notifier/annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
// ignore: depend_on_referenced_packages
import 'package:collection/collection.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class _DatasetDetailCard extends StatelessWidget {
  const _DatasetDetailCard({required this.dataset});
  final Dataset dataset;

  @override
  Widget build(BuildContext context) {
    return Material(
      borderRadius: BorderRadius.circular(20),
      elevation: 8,
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
        ),
        width: double.infinity,
        height: 300,
        child: Column(
          children: [
            Container(
              height: 240,
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.horizontal(
                  left: Radius.circular(20),
                  right: Radius.circular(20),
                ),
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(20),
                  topRight: Radius.circular(20),
                ),
                child: Stack(
                  children: [
                    SizedBox.expand(
                      child: Image(
                        fit: BoxFit.fill,
                        image:
                            dataset.sampleFilePath == null
                                ? AssetImage('assets/bg.jpeg')
                                : NetworkImage(dataset.sampleFilePath!)
                                    as ImageProvider,
                      ),
                    ),
                    BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 5, sigmaY: 5),
                      child: Container(
                        width: double.infinity,
                        height: 300,
                        color: Colors.white.withValues(alpha: 0.2),
                      ),
                    ),
                    Positioned(
                      left: 20,
                      bottom: 100,
                      child: Text(
                        dataset.name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontSize: 27,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    Positioned(
                      left: 20,
                      bottom: 60,
                      child: Text(
                        dataset.description,
                        style: TextStyle(fontSize: 16, color: Colors.white),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        textAlign: TextAlign.left,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            SizedBox(
              height: 60,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  SizedBox(width: 20),
                  Icon(Icons.person_2_outlined, size: 18),
                  SizedBox(width: 5),
                  Text("user info"),
                  SizedBox(width: 20),
                  Icon(Icons.calendar_month_outlined, size: 18),
                  SizedBox(width: 5),
                  Text("创建于 ${dataset.createdAt.split(".").first}"),
                  SizedBox(width: 20),
                  Icon(Icons.update, size: 18),
                  SizedBox(width: 5),
                  Text("更新于 ${dataset.updatedAt.split(".").first}"),
                  SizedBox(width: 20),
                  Container(
                    padding: EdgeInsets.only(
                      left: 4,
                      right: 4,
                      top: 1,
                      bottom: 1,
                    ),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: dataset.type.color),
                      color: dataset.type.color.withValues(alpha: 0.1),
                    ),
                    child: Text(
                      dataset.type.name,
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

    if (current == null) {
      return const Center(child: Text('No dataset selected'));
    }

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
            _DatasetDetailCard(dataset: current),
            SizedBox(height: 20),
            SizedBox(
              height: 35,
              child: Row(
                spacing: 10,
                children: [
                  ...[
                    t.dataset_screen.table.details,
                    t.dataset_screen.table.annotations,
                  ].mapIndexed((i, entry) {
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
                  if (currentPageIndex == 0)
                    Material(
                      borderRadius: BorderRadius.circular(20),
                      child: MouseRegion(
                        cursor: SystemMouseCursors.click,
                        child: GestureDetector(
                          onTap: () async {
                            String url =
                                "${DioClient().instance.options.baseUrl}${Api.datasetExport.replaceAll("{id}", current.id.toString())}";
                            logger.i("Download URL: $url");
                            download(url, filename: "${current.name}.zip");
                          },
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.greenAccent,
                              borderRadius: BorderRadius.circular(20),
                            ),
                            padding: EdgeInsets.all(1),
                            child: Icon(
                              Icons.download,
                              color: Colors.white,
                              size: 18,
                            ),
                          ),
                        ),
                      ),
                    ),
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
                              pageBuilder: (c, _, _) {
                                return Center(child: NewAnnotationDialog());
                              },
                            ).then((v) {
                              if (v != null && v is Map<String, dynamic>) {
                                NewAnnotationRequest request =
                                    NewAnnotationRequest(
                                      datasetId: current.id,
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
