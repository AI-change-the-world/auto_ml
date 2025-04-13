import 'package:auto_ml/modules/dataset/components/modify_dataset_dialog.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:flutter/material.dart';
import 'package:flutter_context_menu/flutter_context_menu.dart';
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
        return ContextMenuRegion(
          menuType: MenuType.desktop,
          contextMenu: ContextMenu(
            entries: [
              MenuItem(
                label: 'Delete',
                icon: Icon(Icons.copy, size: 16),
                onSelected: () {
                  // implement copy
                  ref
                      .read(datasetNotifierProvider.notifier)
                      .deleteDataset(widget.dataset.id);
                },
              ),
            ],
          ),
          child: MouseRegion(
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
              child: GestureDetector(
                onDoubleTap: () {
                  // 双击进入编辑模式
                },
                onTap: () async {
                  await ref
                      .read(datasetNotifierProvider.notifier)
                      .getDatasetStorage(widget.dataset);

                  showGeneralDialog(
                    barrierColor: Colors.black.withValues(alpha: 0.1),
                    barrierDismissible: true,
                    barrierLabel: 'ModifyDatasetDialog',
                    // ignore: use_build_context_synchronously
                    context: context,
                    pageBuilder: (c, _, __) {
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
                child: Container(
                  width: 200,
                  height: 150,
                  decoration: BoxDecoration(
                    color: widget.dataset.type.color,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.2),
                        blurRadius: 10,
                        spreadRadius: 2,
                        offset: Offset(-s.yRotation * 20, s.xRotation * 20),
                      ),
                    ],
                  ),

                  child: Stack(
                    children: [
                      // Center(
                      //   child: Text(
                      //     widget.dataset.name ?? "Unknown",
                      //     style: TextStyle(fontSize: 20, color: Colors.white),
                      //   ),
                      // ),
                      AnimatedAlign(
                        duration: Duration(milliseconds: 300),
                        alignment:
                            s.showIcon ? Alignment.topLeft : Alignment.center,
                        child: Padding(
                          padding: EdgeInsets.all(10),
                          child: Text(
                            widget.dataset.name.isNotEmpty
                                ? widget.dataset.name
                                : "Unknown",
                            style: TextStyle(fontSize: 20, color: Colors.white),
                            maxLines: 1,
                            softWrap: true,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ),

                      Positioned(
                        left: 10,
                        top: 40,
                        child: AnimatedOpacity(
                          opacity: s.showIcon ? 1 : 0,
                          duration: Duration(milliseconds: 300),
                          child: SizedBox(
                            width: 180,
                            child: Text(
                              widget.dataset.description.isNotEmpty
                                  ? widget.dataset.description
                                  : "This dataset is saved at ${widget.dataset.datasetPath}",
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.white70,
                              ),
                              maxLines: 4,
                              softWrap: true,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        ),
                      ),
                      if (s.showIcon)
                        Positioned(
                          bottom: 10,
                          right: 10,
                          child: widget.dataset.type.icon(
                            color: iconColor,
                            size: iconSize,
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  double iconSize = 18;
  Color iconColor = Colors.white;
}
