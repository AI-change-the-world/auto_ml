import 'package:auto_ml/modules/annotation/notifiers/annotation_notifier.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AnnotationListWidget extends ConsumerWidget {
  const AnnotationListWidget({super.key, required this.classes});
  final List<String> classes;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(annotationNotifierProvider);

    return Container(
      margin: EdgeInsets.only(top: 10, bottom: 10),
      width: 200,
      height: double.infinity,
      padding: EdgeInsets.all(5),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        color: Colors.grey[100],
      ),
      child: Column(
        spacing: 10,
        children: [
          Text(
            "Annotation List",
            style: TextStyle(fontWeight: FontWeight.bold),
          ),
          Expanded(
            child:
                state.annotations.isEmpty
                    ? Center(child: Text("annotations is empty"))
                    : ListView.builder(
                      itemBuilder: (context, index) {
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
                                  label: state.annotations[index].getLabel(
                                    classes,
                                  ),
                                  onSubmit: (value) {
                                    if (classes.contains(value)) {
                                      // state.annotations[index].id = classes
                                      //     .indexOf(value);
                                      ref
                                          .read(
                                            annotationNotifierProvider.notifier,
                                          )
                                          .changeAnnotationClassId(
                                            state.annotations[index].uuid,
                                            classes.indexOf(value),
                                          );
                                    } else {
                                      ref
                                          .read(
                                            currentDatasetAnnotationNotifierProvider
                                                .notifier,
                                          )
                                          .addClassType(value);
                                      classes.add(value);
                                      ref
                                          .read(
                                            annotationNotifierProvider.notifier,
                                          )
                                          .changeAnnotationClassId(
                                            state.annotations[index].uuid,
                                            classes.indexOf(value),
                                          );
                                    }
                                  },
                                ),
                              ),
                              InkWell(
                                onTap: () {
                                  ref
                                      .read(annotationNotifierProvider.notifier)
                                      .changeAnnotationVisibility(
                                        state.annotations[index].uuid,
                                      );
                                },
                                child: Icon(
                                  state.annotations[index].visible
                                      ? Icons.visibility_off
                                      : Icons.visibility,
                                  size: 20,
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

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    controller.dispose();
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
      },
      child: SizedBox(
        height: 20,
        child:
            isEditing
                ? TextField(
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
