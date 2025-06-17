import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AnnotationListWidget extends ConsumerStatefulWidget {
  const AnnotationListWidget({super.key, required this.classes});
  final List<String> classes;

  @override
  ConsumerState<AnnotationListWidget> createState() =>
      _AnnotationListWidgetState();
}

class _AnnotationListWidgetState extends ConsumerState<AnnotationListWidget> {
  String lastLabel = "";
  bool showSearch = false;

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(annotationNotifierProvider);

    return Material(
      borderRadius: BorderRadius.circular(10),
      color: Colors.grey[100],
      elevation: 4,
      child: Container(
        margin: EdgeInsets.only(top: 10, bottom: 10),
        width: 200,
        height: double.infinity,
        padding: EdgeInsets.all(5),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          color: Colors.grey[100],
        ),
        child: Column(
          spacing: 10,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              spacing: 10,
              children: [
                Text(
                  t.annotation_screen.list.annotation_list,
                  style: TextStyle(fontWeight: FontWeight.bold),
                ),
                InkWell(
                  child:
                      !showSearch
                          ? Icon(
                            Icons.search,
                            size: Styles.datatableIconSize,
                            color: Colors.black,
                          )
                          : Icon(
                            Icons.search_off,
                            size: Styles.datatableIconSize,
                            color: Colors.black,
                          ),
                  onTap: () {
                    setState(() {
                      showSearch = !showSearch;
                    });
                  },
                ),
              ],
            ),
            Expanded(
              child:
                  state.annotations.isEmpty
                      ? Center(
                        child: Text(t.annotation_screen.list_widget.empty),
                      )
                      : ListView.builder(
                        itemBuilder: (context, index) {
                          String label = state.annotations[index].getLabel(
                            widget.classes,
                          );
                          if ((label == "unknown" || label.isEmpty) &&
                              lastLabel.isNotEmpty) {
                            label = lastLabel;
                            state.annotations[index].id = widget.classes
                                .indexOf(lastLabel);
                          }

                          return Container(
                            decoration: BoxDecoration(
                              color:
                                  state.annotations[index].selected
                                      ? Colors.lightBlueAccent
                                      : Colors.transparent,
                            ),
                            child: Row(
                              children: [
                                Expanded(
                                  child: _EditableLabel(
                                    onTap: () {
                                      ref
                                          .read(
                                            annotationNotifierProvider.notifier,
                                          )
                                          .changeCurrentAnnotation(
                                            state.annotations[index].uuid,
                                          );
                                    },
                                    label: label,
                                    onSubmit: (value) {
                                      lastLabel = value;
                                      if (widget.classes.contains(value)) {
                                        // state.annotations[index].id = classes
                                        //     .indexOf(value);
                                        ref
                                            .read(
                                              annotationNotifierProvider
                                                  .notifier,
                                            )
                                            .changeAnnotationClassId(
                                              state.annotations[index].uuid,
                                              widget.classes.indexOf(value),
                                            );
                                      } else {
                                        ref
                                            .read(
                                              currentDatasetAnnotationNotifierProvider
                                                  .notifier,
                                            )
                                            .addClassType(value);
                                        widget.classes.add(value);
                                        ref
                                            .read(
                                              annotationNotifierProvider
                                                  .notifier,
                                            )
                                            .changeAnnotationClassId(
                                              state.annotations[index].uuid,
                                              widget.classes.indexOf(value),
                                            );
                                      }
                                    },
                                  ),
                                ),
                                // InkWell(
                                //   onTap: () {
                                //     ref
                                //         .read(annotationNotifierProvider.notifier)
                                //         .findSimilarAnnotation(classes);
                                //   },
                                //   child: Tooltip(
                                //     message: "Find similar",
                                //     child: Icon(
                                //       Icons.bolt,
                                //       size: Styles.datatableIconSize,
                                //     ),
                                //   ),
                                // ),
                                InkWell(
                                  onTap: () {
                                    ref
                                        .read(
                                          annotationNotifierProvider.notifier,
                                        )
                                        .changeAnnotationVisibility(
                                          state.annotations[index].uuid,
                                        );
                                  },
                                  child: Icon(
                                    state.annotations[index].visible
                                        ? Icons.visibility_off
                                        : Icons.visibility,
                                    size: Styles.datatableIconSize,
                                  ),
                                ),
                                InkWell(
                                  onTap: () {
                                    ref
                                        .read(
                                          annotationNotifierProvider.notifier,
                                        )
                                        .removeAnnotationById(
                                          state.annotations[index].uuid,
                                        );
                                  },
                                  child: Icon(
                                    Icons.delete,
                                    size: Styles.datatableIconSize,
                                  ),
                                ),
                              ],
                            ),
                          );
                        },
                        itemCount: state.annotations.length,
                      ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EditableLabel extends StatefulWidget {
  const _EditableLabel({
    required this.label,
    required this.onSubmit,
    required this.onTap,
  });
  final String label;
  final void Function(String) onSubmit;
  final VoidCallback onTap;

  @override
  State<_EditableLabel> createState() => __EditableLabelState();
}

class __EditableLabelState extends State<_EditableLabel> {
  bool isEditing = false;

  late final TextEditingController controller =
      TextEditingController()..text = widget.label;

  FocusNode focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
  }

  @override
  void didUpdateWidget(covariant _EditableLabel oldWidget) {
    super.didUpdateWidget(oldWidget);
    controller.text = widget.label;
  }

  @override
  void dispose() {
    controller.dispose();
    focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        widget.onTap();
      },
      onDoubleTap: () {
        setState(() {
          isEditing = true;
        });
        focusNode.requestFocus();
      },
      child: SizedBox(
        height: 20,
        child:
            isEditing
                ? TextField(
                  focusNode: focusNode,
                  style: TextStyle(fontSize: 12),
                  decoration: InputDecoration(
                    contentPadding: EdgeInsets.only(
                      top: 10,
                      left: 10,
                      right: 10,
                    ),
                    border: OutlineInputBorder(),
                    focusedBorder: OutlineInputBorder(
                      borderSide: BorderSide(color: Colors.blueAccent),
                    ),
                    hintText: "New Type",
                    hintStyle: TextStyle(fontSize: 12, color: Colors.grey),
                  ),
                  controller: controller,
                  onSubmitted: (value) {
                    setState(() {
                      isEditing = false;
                    });
                    widget.onSubmit(controller.text);
                  },
                )
                : Text(controller.text),
      ),
    );
  }
}
