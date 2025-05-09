import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/annotation/components/faded_text.dart';
import 'package:auto_ml/modules/annotation/models/api/tool_models_response.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/modules/annotation/notifiers/image_notifier.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/predict/models/video_result.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:dropdown_button2/dropdown_button2.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class TopToBottomIconPainter extends CustomPainter {
  final bool isSelected;

  TopToBottomIconPainter(this.isSelected);

  @override
  void paint(Canvas canvas, Size size) {
    final borderPaint =
        Paint()
          ..color = isSelected ? Colors.white : Colors.black
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.0;

    final double topHeight = size.height * 0.7;
    final double bottomHeight = size.height * 0.3;
    final double bottomWidth = size.width / 2;

    // 上方矩形
    Rect topRect = Rect.fromLTWH(0, 0, size.width, topHeight);
    canvas.drawRect(topRect, borderPaint);

    // 左下矩形
    Rect bottomLeftRect = Rect.fromLTWH(
      0,
      topHeight,
      bottomWidth,
      bottomHeight,
    );
    canvas.drawRect(bottomLeftRect, borderPaint);

    // 右下矩形
    Rect bottomRightRect = Rect.fromLTWH(
      bottomWidth,
      topHeight,
      bottomWidth,
      bottomHeight,
    );
    canvas.drawRect(bottomRightRect, borderPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class LeftToRightIconPainter extends CustomPainter {
  final bool isSelected;

  LeftToRightIconPainter(this.isSelected);

  @override
  void paint(Canvas canvas, Size size) {
    final borderPaint =
        Paint()
          ..color = isSelected ? Colors.white : Colors.black
          ..style = PaintingStyle.stroke
          ..strokeWidth = 1.0;

    final double rectWidth = size.width / 5;
    final double middleWidth = rectWidth * 3; // 中间矩形宽度
    final double gap = 0; // 计算缝隙宽度

    // 左边矩形
    Rect leftRect = Rect.fromLTWH(0, 0, rectWidth, size.height);
    canvas.drawRect(leftRect, borderPaint);

    // 右边矩形
    Rect rightRect = Rect.fromLTWH(
      size.width - rectWidth,
      0,
      rectWidth,
      size.height,
    );
    canvas.drawRect(rightRect, borderPaint);

    // 中间矩形（带缝隙）
    Rect middleRect = Rect.fromLTWH(
      rectWidth + gap,
      0,
      middleWidth - 2 * gap,
      size.height,
    );
    canvas.drawRect(middleRect, borderPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class LayoutIcons extends ConsumerWidget {
  const LayoutIcons({super.key, required this.onIconSelected});
  final Function(int type) onIconSelected;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    bool modified = ref.watch(
      annotationNotifierProvider.select((v) => v.modified),
    );
    return Row(
      spacing: 10,
      crossAxisAlignment: CrossAxisAlignment.end,
      mainAxisAlignment: MainAxisAlignment.center,

      children: [
        Expanded(
          child: SizedBox(
            child: Center(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  if (modified)
                    ElevatedButton(
                      style: Styles.getDefaultButtonStyle(),
                      onPressed: () {
                        ref
                            .read(annotationNotifierProvider.notifier)
                            .putYoloAnnotation()
                            .then((v) {
                              ref
                                  .read(annotationNotifierProvider.notifier)
                                  .changeModifiedStatus(v != 0);
                              ref
                                  .read(
                                    currentDatasetAnnotationNotifierProvider
                                        .notifier,
                                  )
                                  .updateDataAfterAnnotationUpdate();
                            });
                      },
                      child: Row(
                        children: [
                          Icon(
                            Icons.check,
                            color: Colors.green,
                            size: Styles.menuBarIconSize,
                          ),
                          SizedBox(width: 5),
                          Text("Save", style: Styles.defaultButtonTextStyle),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ),
        ),
        if (modified) FadedText(),
        _DropDownButton(),
        SizedBox(
          height: 15,
          child: VerticalDivider(width: 2, color: Colors.grey),
        ),
        InkWell(
          onTap: () {
            onIconSelected(0);
          },
          child: SizedBox(
            width: 15,
            height: 15,
            child: CustomPaint(painter: LeftToRightIconPainter(false)),
          ),
        ),
        InkWell(
          onTap: () {
            onIconSelected(1);
          },
          child: SizedBox(
            width: 15,
            height: 15,
            child: CustomPaint(painter: TopToBottomIconPainter(false)),
          ),
        ),
        SizedBox(width: 1),
      ],
    );
  }
}

class _DropDownButton extends ConsumerStatefulWidget {
  @override
  ConsumerState<_DropDownButton> createState() => __DropDownButtonState();
}

class __DropDownButtonState extends ConsumerState<_DropDownButton> {
  final dio = DioClient().instance;

  initData() async {
    try {
      final response = await dio.get(Api.getToolModels);
      BaseResponse<ToolModels> baseResponse = BaseResponse.fromJson(
        response.data,
        (json) => ToolModels.fromJson({"models": json}),
      );
      return baseResponse.data;
    } catch (e) {
      logger.e(e);
    }
  }

  // ignore: prefer_typing_uninitialized_variables
  var future;

  @override
  void initState() {
    super.initState();
    future = initData();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 15,
      height: 15,
      child: FutureBuilder(
        future: future,
        builder: (c, s) {
          if (s.connectionState == ConnectionState.done) {
            if (s.hasData) {
              return DropdownButton2<ModelConfig>(
                customButton: const Icon(
                  Icons.settings,
                  size: 15,
                  color: Colors.black,
                ),
                items:
                    (s.data! as ToolModels).models.map((e) {
                      logger.d(e.name);
                      return DropdownMenuItem<ModelConfig>(
                        value: e,
                        child: Text.rich(
                          TextSpan(
                            children: [
                              TextSpan(
                                text: "Auto label with ",
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              TextSpan(
                                text: e.name,
                                style: TextStyle(fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
                onChanged: (value) async {
                  // do something
                  if (value == null) {
                    return;
                  }
                  final imgName = ref.read(imageNotifierProvider).imgKey;
                  if (imgName == "") {
                    return;
                  }

                  final state = ref.read(
                    currentDatasetAnnotationNotifierProvider,
                  );

                  // AutoAnnotationRequest autoAnnotationRequest =
                  //     AutoAnnotationRequest(
                  //       content: imgName,
                  //       prompt: null,
                  //       modelId: value.id,
                  //       annotationId: state.annotationId,
                  //       datasetId: state.datasetId,
                  //       image: true,
                  //     );
                  // // logger.i(autoAnnotationRequest.toJson());
                  // try {
                  //   final response = await dio.post(
                  //     Api.autoLabel,
                  //     data: autoAnnotationRequest.toJson(),
                  //   );
                  //   BaseResponse<String> baseResponse = BaseResponse.fromJson(
                  //     response.data,
                  //     (json) => json.toString(),
                  //   );
                  //   logger.i("annotaiton ${baseResponse.data}");
                  //   if (baseResponse.data != null) {
                  //     ref
                  //         .read(annotationNotifierProvider.notifier)
                  //         .setAnnotationsWithClasses(baseResponse.data!);
                  //   }
                  // } catch (e, s) {
                  //   logger.e(e);
                  //   logger.e(s);
                  // }

                  Map<String, dynamic> map = {
                    "annotationId": state.annotationId,
                    "imgPath": imgName,
                  };
                  try {
                    final response = await dio.post(
                      Api.autoLabelMultiple,
                      data: map,
                    );
                    BaseResponse<SingleImageResponse> baseResponse =
                        BaseResponse.fromJson(
                          response.data,
                          (json) => SingleImageResponse.fromJson(
                            json as Map<String, dynamic>,
                          ),
                        );
                    logger.i("annotaiton ${baseResponse.data}");
                    if (baseResponse.data != null) {
                      if (baseResponse.data!.results.isNotEmpty) {
                        ref
                            .read(annotationNotifierProvider.notifier)
                            .setAnnotationsInDetections(baseResponse.data!);
                      } else {
                        ToastUtils.info(null, title: "");
                      }
                    }
                  } catch (e, s) {
                    logger.e(e);
                    logger.e(s);
                  }
                },
                menuItemStyleData: MenuItemStyleData(
                  height: 30,
                  padding: const EdgeInsets.only(left: 16, right: 16),
                ),
                dropdownStyleData: DropdownStyleData(
                  width: 200,
                  // maxHeight: 35,
                  // padding: const EdgeInsets.symmetric(vertical: 6),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(4),
                    color: Colors.white,
                  ),
                  offset: const Offset(0, 8),
                ),
              );
            } else {
              return Icon(Icons.error);
            }
          }
          return CircularProgressIndicator();
        },
      ),
    );
  }
}
