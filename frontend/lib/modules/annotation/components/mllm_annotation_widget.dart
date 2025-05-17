// ignore_for_file: avoid_init_to_null

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/aether_base_response.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/annotation/components/file_list.dart';
import 'package:auto_ml/modules/annotation/models/api/update_annotation_prompt_request.dart';
import 'package:auto_ml/modules/annotation/models/api/update_annotation_request.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/models/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_request.dart';
import 'package:auto_ml/modules/dataset/models/file_preview_response.dart';
import 'package:auto_ml/modules/dataset/models/get_all_dataset_response.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:markdown_widget/markdown_widget.dart';

class MllmAnnotationWidget extends ConsumerStatefulWidget {
  const MllmAnnotationWidget({super.key, required this.data});
  final List<(String, String)> data;

  @override
  ConsumerState<MllmAnnotationWidget> createState() =>
      _MllmAnnotationWidgetState();
}

class _MllmAnnotationWidgetState extends ConsumerState<MllmAnnotationWidget> {
  late Dataset? currentDataset = null;
  late Annotation? currentAnnotation = null;
  late String selectedImage = "";
  late String selectedAnnotation = "";
  late TextEditingController controller = TextEditingController();
  late TextEditingController controller2 = TextEditingController();
  bool loading = false;

  @override
  void dispose() {
    controller.dispose();
    controller2.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant MllmAnnotationWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    controller2.text = "";
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.read(currentDatasetAnnotationNotifierProvider);
    currentDataset = state.dataset;
    currentAnnotation = state.annotation;
    selectedImage = state.currentData?.$1 ?? "";
    selectedAnnotation = state.currentData?.$2 ?? "";
    logger.i(
      "selectedImage   $selectedImage  selectedAnnotation  $selectedAnnotation!",
    );
    if (currentAnnotation != null && currentAnnotation!.prompt != null) {
      controller.text = currentAnnotation!.prompt!;
    }

    return Row(
      children: [
        FileList(data: widget.data),
        Expanded(
          child: Container(
            padding: EdgeInsets.all(10),
            child: Row(
              spacing: 10,
              children: [
                Expanded(
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
                Expanded(
                  child: Column(
                    spacing: 10,
                    children: [
                      Expanded(
                        child: Container(
                          padding: EdgeInsets.all(10),
                          decoration: BoxDecoration(color: Colors.white),
                          child: Column(
                            spacing: 10,
                            children: [
                              Expanded(
                                child: TextField(
                                  keyboardType: TextInputType.multiline,
                                  textAlignVertical:
                                      TextAlignVertical.top, // ← 关键属性
                                  expands: true,
                                  controller: controller,
                                  style: const TextStyle(fontSize: 12),
                                  maxLines: null,
                                  decoration: InputDecoration(
                                    hintStyle: Styles.hintStyle,
                                    contentPadding: EdgeInsets.only(
                                      top: 10,
                                      left: 10,
                                      right: 10,
                                    ),
                                    border: OutlineInputBorder(),
                                    focusedBorder: OutlineInputBorder(
                                      borderSide: BorderSide(
                                        color: Colors.blueAccent,
                                      ),
                                    ),
                                    hintText: "Input prompt",
                                  ),
                                ),
                              ),

                              SizedBox(
                                height: 30,
                                child: Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  spacing: 10,
                                  children: [
                                    ElevatedButton(
                                      style: Styles.getDefaultButtonStyle(
                                        width: 150,
                                      ),
                                      onPressed: () {
                                        if (controller.text == "") {
                                          return;
                                        }
                                        UpdateAnnotationPromptRequest request =
                                            UpdateAnnotationPromptRequest(
                                              controller.text,
                                              currentAnnotation!.id,
                                            );
                                        DioClient().instance
                                            .post(
                                              Api.annotationUpdatePrompt,
                                              data: request.toJson(),
                                            )
                                            .then((v) {
                                              if (v.statusCode == 200) {
                                                ToastUtils.success(
                                                  null,
                                                  title: "Success",
                                                );
                                              } else {
                                                ToastUtils.error(
                                                  null,
                                                  title: "Error",
                                                );
                                              }
                                            });
                                      },
                                      child: Text(
                                        "Update prompt",
                                        style: Styles.defaultButtonTextStyle,
                                      ),
                                    ),
                                    InkWell(
                                      onTap: () {
                                        controller.text = """
你现在是一个视觉理解专家，擅长将图像的内容转换为结构清晰、逻辑分明的 Markdown 格式回答。

请根据下方提供的图像内容，输出一段 Markdown 格式的说明，分点总结图像中的主要信息。要求如下：

## 要求：

- 使用 Markdown 列表语法（`-` 或 `1.`）进行分点描述。
- 每个点只描述一类视觉要素，内容简明但具有信息量。
- 如图中有人物、物体、场景、文字等，请按类别分别归纳。
- 若存在推理空间（如天气、时间、人物身份、情绪），请进行合理推测并标明为“推测”。
- 不要生成图像的标题或总结句，只输出 Markdown 列表正文。
- 避免主观修饰，保持客观、清晰。

请根据以下图像进行分析：
""";
                                      },
                                      child: Tooltip(
                                        message: "Paste template",
                                        child: Icon(
                                          Icons.paste,
                                          size: Styles.datatableIconSize,
                                        ),
                                      ),
                                    ),
                                    InkWell(
                                      onTap:
                                          selectedImage == "" ||
                                                  controller.text == ""
                                              ? null
                                              : () async {
                                                final image = selectedImage;
                                                final annotationId =
                                                    currentAnnotation!.id;
                                                Map<String, dynamic> request = {
                                                  "imgPath": image,
                                                  "annotationId": annotationId,
                                                  "agentId": 9,
                                                };

                                                setState(() {
                                                  loading = true;
                                                });

                                                await DioClient().instance
                                                    .post(
                                                      Api.agent,
                                                      data: request,
                                                    )
                                                    .then((v) {
                                                      logger.d(v.data);
                                                      setState(() {
                                                        loading = false;
                                                      });
                                                      BaseResponse<
                                                        AetherBaseResponse<
                                                          String
                                                        >
                                                      >
                                                      b = BaseResponse.fromJson(
                                                        v.data,
                                                        (j) =>
                                                            AetherBaseResponse.fromJson(
                                                              j
                                                                  as Map<
                                                                    String,
                                                                    dynamic
                                                                  >,
                                                              (j) =>
                                                                  j as String,
                                                            ),
                                                      );
                                                      controller2.text =
                                                          b.data?.output ?? "";
                                                    });
                                              },
                                      child: Tooltip(
                                        message: "Evaluate",
                                        child: Icon(
                                          Icons.task,
                                          size: Styles.datatableIconSize,
                                          color:
                                              selectedImage == "" ||
                                                      controller.text == ""
                                                  ? Colors.grey
                                                  : Colors.black,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                      Expanded(
                        child: Container(
                          padding: EdgeInsets.all(10),
                          height: double.infinity,
                          width: double.infinity,
                          decoration: BoxDecoration(color: Colors.white),
                          child: Column(
                            spacing: 10,
                            children: [
                              Expanded(
                                child: Center(
                                  child:
                                      loading
                                          ? CircularProgressIndicator()
                                          : Consumer(
                                            builder: (c, ref, _) {
                                              if (controller2.text.isNotEmpty) {
                                                logger.d("Into this section");
                                                return _text2;
                                              }

                                              if (selectedImage == "") {
                                                return MarkdownBlock(
                                                  data:
                                                      "**No image selected yet**",
                                                );
                                              }

                                              if (selectedAnnotation == "") {
                                                return MarkdownBlock(
                                                  data:
                                                      "**This image is not annotated yet.**",
                                                );
                                              }

                                              if (currentDataset == null ||
                                                  currentAnnotation == null) {
                                                return MarkdownBlock(
                                                  data: "**No image selected**",
                                                );
                                              }
                                              final asyncDetail = ref.watch(
                                                getAnnotationContent((
                                                  currentAnnotation!,
                                                  selectedAnnotation,
                                                )),
                                              );
                                              return asyncDetail.when(
                                                data: (data) {
                                                  logger.d(
                                                    "Into this section after request",
                                                  );
                                                  controller2.text = data;
                                                  return _text2;
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
                              SizedBox(
                                height: 30,
                                child: ElevatedButton(
                                  style: Styles.getDefaultButtonStyle(
                                    width: 100,
                                  ),
                                  onPressed: () {
                                    if (controller2.text.isNotEmpty) {
                                      final String filename =
                                          "${ref.read(currentDatasetAnnotationNotifierProvider).annotation?.annotationSavePath}/${ref.read(currentDatasetAnnotationNotifierProvider).currentData?.$1.split("/").last.split(".").first}.txt";
                                      UpdateAnnotationRequest request =
                                          UpdateAnnotationRequest(
                                            content: controller2.text,
                                            annotationPath: filename,
                                          );

                                      DioClient().instance
                                          .post(
                                            Api.annotationUpdate,
                                            data: request.toJson(),
                                          )
                                          .then((v) {
                                            if (v.statusCode == 200) {
                                              ToastUtils.success(
                                                null,
                                                title: "更新成功",
                                              );
                                              ref
                                                  .read(
                                                    currentDatasetAnnotationNotifierProvider
                                                        .notifier,
                                                  )
                                                  .updateDataAfterAnnotationUpdate();
                                            } else {
                                              ToastUtils.error(
                                                null,
                                                title: "更新失败",
                                              );
                                            }
                                          });
                                    }
                                  },
                                  child: Text(
                                    "Save",
                                    style: Styles.defaultButtonTextStyle,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  late final Widget _text2 = TextField(
    keyboardType: TextInputType.multiline,
    textAlignVertical: TextAlignVertical.top, // ← 关键属性
    expands: true,
    controller: controller2,
    style: const TextStyle(fontSize: 12),
    maxLines: null,
    decoration: InputDecoration(
      hintStyle: Styles.hintStyle,
      contentPadding: EdgeInsets.only(top: 10, left: 10, right: 10),
      border: OutlineInputBorder(),
      focusedBorder: OutlineInputBorder(
        borderSide: BorderSide(color: Colors.blueAccent),
      ),
      hintText: "Input description",
    ),
  );
}

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
