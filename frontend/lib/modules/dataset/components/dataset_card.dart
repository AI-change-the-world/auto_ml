import 'package:auto_ml/modules/dataset/components/left_right_background_container.dart';
import 'package:auto_ml/modules/dataset/components/modify_dataset_dialog.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/notifier/annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:auto_ml/modules/dataset/notifier/delete_zone_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class _CardState {
  final double xRotation;
  final double yRotation;
  final bool showIcon;

  const _CardState({
    this.xRotation = 0,
    this.yRotation = 0,
    this.showIcon = false,
  });

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;

    return other is _CardState &&
        other.xRotation == xRotation &&
        other.yRotation == yRotation &&
        other.showIcon == showIcon;
  }

  @override
  int get hashCode =>
      xRotation.hashCode ^ yRotation.hashCode ^ showIcon.hashCode;

  _CardState copyWith({double? xRotation, double? yRotation, bool? showIcon}) {
    return _CardState(
      xRotation: xRotation ?? this.xRotation,
      yRotation: yRotation ?? this.yRotation,
      showIcon: showIcon ?? this.showIcon,
    );
  }
}

class DatasetCard extends ConsumerStatefulWidget {
  const DatasetCard({super.key, required this.dataset});
  final Dataset dataset;

  @override
  ConsumerState<DatasetCard> createState() => _DatasetCardState();
}

class _DatasetCardState extends ConsumerState<DatasetCard> {
  late ValueNotifier<_CardState> _cardState = ValueNotifier(_CardState());
  final double maxAngle = 0.15; // 最大旋转角度（弧度）

  @override
  void initState() {
    super.initState();
    _cardState = ValueNotifier(_CardState());
  }

  @override
  void dispose() {
    _cardState.dispose();
    super.dispose();
  }

  void _updateRotation(Offset position, Size size) {
    double dx = (position.dx - size.width / 2) / (size.width / 2); // -1 ~ 1
    double dy = (position.dy - size.height / 2) / (size.height / 2); // -1 ~ 1

    // 计算旋转角度，映射到 [-maxAngle, maxAngle]
    double newXRotation = dy * -maxAngle;
    double newYRotation = dx * maxAngle;
    _CardState newState = _cardState.value.copyWith(
      xRotation: newXRotation, // 控制前后倾斜
      yRotation: newYRotation, // 控制左右倾斜
    );
    if (_cardState.value != newState) {
      _cardState.value = newState;
    }
  }

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder(
      valueListenable: _cardState,
      builder: (c, s, _) {
        return MouseRegion(
          cursor: SystemMouseCursors.click,
          onEnter: (event) {
            _cardState.value = _CardState(showIcon: true);
          },
          onHover: (event) {
            final RenderBox box = context.findRenderObject() as RenderBox;
            final Offset localPosition = box.globalToLocal(event.position);
            _updateRotation(localPosition, box.size);
          },
          onExit: (_) => _cardState.value = _CardState(),
          child: Transform(
            alignment: Alignment.center,
            transform:
                Matrix4.identity()
                  ..setEntry(3, 2, 0.0015) // 透视效果
                  ..rotateX(s.xRotation)
                  ..rotateY(s.yRotation),
            child: Draggable<Dataset>(
              data: widget.dataset,
              onDragStarted: () {
                ref.read(deleteZoneNotifierProvider.notifier).show();
              },
              onDragEnd: (details) {
                ref.read(deleteZoneNotifierProvider.notifier).hide();
              },
              feedback: Opacity(opacity: 0.5, child: _child(s)),
              child: GestureDetector(
                onTap: () {
                  ref
                      .read(datasetNotifierProvider.notifier)
                      .changeCurrent(widget.dataset);
                  GlobalDrawer.showDrawer();
                },
                onDoubleTap: () async {
                  showGeneralDialog(
                    barrierColor: Styles.barriarColor,
                    barrierDismissible: true,
                    barrierLabel: 'ModifyDatasetDialog',
                    // ignore: use_build_context_synchronously
                    context: context,
                    pageBuilder: (c, _, _) {
                      return Center(
                        child: ModifyDatasetDialog(dataset: widget.dataset),
                      );
                    },
                  ).then((v) {
                    if (v == null) {
                      return;
                    }
                    ref
                        .read(datasetNotifierProvider.notifier)
                        .updateDataset(v as Dataset);

                    widget.dataset.name = v.name;
                    widget.dataset.description = v.description;
                    widget.dataset.datasetPath = v.datasetPath;
                    widget.dataset.labelPath = v.labelPath;
                    widget.dataset.type = v.type;
                    // widget.dataset.task = v.task;
                    widget.dataset.ranking = v.ranking;
                    setState(() {});
                  });
                },
                child: _child(s),
              ),
            ),
          ),
        );
      },
    );
  }

  double iconSize = 18;
  Color iconColor = Colors.white;

  Widget _child(_CardState s) {
    return LeftRightBackgroundContainer(
      width: 400,
      height: 300,
      rightBackgroundImage:
          widget.dataset.type == DatasetType.image
              ? widget.dataset.sampleFilePath
              : null,
      children: [
        Positioned(
          top: 20,
          left: 20,
          child: Text(
            widget.dataset.name,
            maxLines: 1,
            softWrap: true,
            overflow: TextOverflow.ellipsis,
            style: Styles.defaultButtonTextStyle.copyWith(fontSize: 20),
          ),
        ),
        Positioned(
          top: 60,
          left: 20,
          child: SizedBox(
            width: 400 - 40,
            child: Text(
              widget.dataset.description,
              style: Styles.defaultButtonTextStyle.copyWith(fontSize: 14),
              maxLines: 3,
              softWrap: true,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),

        Positioned(
          left: 20,
          bottom: 20,
          child: Material(
            elevation: 4,
            borderRadius: BorderRadius.circular(20),
            child: Container(
              width: 80,
              height: 30,
              decoration: BoxDecoration(
                color: const Color.fromARGB(255, 245, 243, 246),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Center(
                child: Text.rich(
                  TextSpan(
                    text: widget.dataset.fileCount.toString(),
                    style: Styles.defaultButtonTextStyle.copyWith(
                      fontSize: 14,
                      color: Colors.green,
                    ),
                    children: [
                      TextSpan(
                        text: '   files',
                        style: Styles.defaultButtonTextStyle.copyWith(
                          fontSize: 12,
                          color: Colors.black,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
