import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/base_response.dart';
import 'package:auto_ml/modules/aether_agent/models/agent_simple_response.dart';
import 'package:auto_ml/modules/annotation/components/faded_text.dart';
import 'package:auto_ml/modules/annotation/components/short_cut_dialog.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/models/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/models/get_all_dataset_response.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
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
        SizedBox(width: 1),
        Tooltip(
          message: 'Back',
          child: InkWell(
            onTap: () {
              ref
                  .read(currentDatasetAnnotationNotifierProvider.notifier)
                  .changeDatasetAndAnnotation(
                    Dataset.fake(),
                    Annotation.fake(),
                  );
            },
            child: Icon(Icons.chevron_left, color: Colors.black),
          ),
        ),
        Tooltip(
          message: 'Shortcuts',
          child: InkWell(
            onTap: () {
              showGeneralDialog(
                context: context,
                barrierColor: Styles.barriarColor,
                barrierDismissible: true,
                barrierLabel: "ShortCutDialog",
                pageBuilder: (c, _, __) {
                  return Center(child: ShortCutDialog());
                },
              );
            },
            child: Icon(Icons.info, color: Colors.blue),
          ),
        ),
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

class _DropDownButton extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncData = ref.watch(agentSimpleListProvider);
    return SizedBox(
      width: 15,
      height: 15,
      child: asyncData.when(
        data: (data) {
          return DropdownButton2<AgentSimple>(
            customButton: const Icon(
              Icons.settings,
              size: 15,
              color: Colors.black,
            ),
            items:
                data.map((e) {
                  logger.d(e.name);
                  return DropdownMenuItem<AgentSimple>(
                    value: e,
                    child: Tooltip(
                      message: e.name,
                      waitDuration: Duration(milliseconds: 500),
                      child: Row(
                        spacing: 5,
                        children: [
                          Icon(
                            e.isRecommended == 1 ? Icons.check : Icons.error,
                            size: Styles.datatableIconSize,
                            color:
                                e.isRecommended == 1
                                    ? Colors.green
                                    : Colors.amber,
                          ),
                          Text(
                            e.name,
                            style: TextStyle(fontSize: 12),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                  );
                }).toList(),
            onChanged: (value) async {
              if (value == null) {
                return;
              }

              /// TODO:  do something
              /// FIXME: 应该从后端获取访问参数列表，暂时先前端定制
              ref
                  .read(annotationNotifierProvider.notifier)
                  .handleAgent(value.id, stream: false);
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
        },
        error: (e, s) => Icon(Icons.error),
        loading: () {
          return const CircularProgressIndicator();
        },
      ),
    );
  }
}

final agentSimpleListProvider = FutureProvider<List<AgentSimple>>((ref) async {
  final dio = DioClient().instance;
  final response = await dio.get(Api.aetherAgentSimpleList);

  final baseResponse = BaseResponse.fromJson(
    response.data,
    (json) => AgentSimpleResponse.fromJson({'data': json}),
  );

  return baseResponse.data?.data ?? [];
}, name: "agentSimpleListProvider");
