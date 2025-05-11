import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';

class ModifyAnnotationClassesDialog extends StatefulWidget {
  const ModifyAnnotationClassesDialog({
    super.key,
    required this.annotationString,
  });
  final String annotationString;

  @override
  State<ModifyAnnotationClassesDialog> createState() =>
      _ModifyAnnotationClassesDialogState();
}

class _ModifyAnnotationClassesDialogState
    extends State<ModifyAnnotationClassesDialog> {
  late List<String> annotationClasses = [];

  @override
  void initState() {
    super.initState();
    annotationClasses = widget.annotationString.split(';');
  }

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: 300,
      height: 400,

      child: Container(
        padding: EdgeInsets.all(10),
        child: Column(
          children: [
            Expanded(
              child: ListView.builder(
                itemBuilder: (context, index) {
                  if (index == annotationClasses.length) {
                    return SizedBox(
                      height: 40,
                      child: AddTagButton(
                        onSave: (tag) {
                          if (tag.isEmpty) {
                            return;
                          }
                          if (annotationClasses.contains(tag)) {
                            return;
                          }
                          setState(() {
                            annotationClasses.add(tag);
                          });
                        },
                      ),
                    );
                  }
                  return Row(
                    children: [
                      Text(
                        annotationClasses[index],
                        style: Styles.defaultButtonTextStyle,
                      ),
                      Spacer(),
                      InkWell(
                        child: Icon(
                          Icons.delete,
                          size: Styles.datatableIconSize,
                        ),
                        onTap: () {
                          setState(() {
                            annotationClasses.remove(annotationClasses[index]);
                          });
                        },
                      ),
                      SizedBox(width: 20),
                    ],
                  );
                },
                itemCount: annotationClasses.length + 1,
              ),
            ),
            const SizedBox(height: 10),
            SizedBox(
              height: 30,
              child: Row(
                children: [
                  Spacer(),
                  ElevatedButton(
                    style: Styles.getDefaultButtonStyle(width: 70),
                    onPressed: () {
                      Navigator.of(context).pop(annotationClasses.join(';'));
                    },
                    child: Text('Save'),
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

typedef OnSave = void Function(String);

class AddTagButton extends StatefulWidget {
  const AddTagButton({super.key, required this.onSave});
  final OnSave onSave;

  @override
  State<AddTagButton> createState() => _AddTagButtonState();
}

class _AddTagButtonState extends State<AddTagButton> {
  bool isActivate = false;
  final TextEditingController controller = TextEditingController();

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  late TextStyle hintStyle = TextStyle(fontSize: 12, color: Colors.grey);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(6),
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(15)),
      child: SizedBox(
        child:
            !isActivate
                ? InkWell(
                  onTap: () {
                    setState(() {
                      isActivate = !isActivate;
                    });
                  },
                  child: Icon(Icons.add, size: Styles.datatableIconSize),
                )
                : SizedBox(
                  width: 400,
                  height: 40,
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: controller,
                          style: const TextStyle(fontSize: 12),
                          keyboardType: TextInputType.text,
                          decoration: InputDecoration(
                            hintStyle: hintStyle,
                            contentPadding: EdgeInsets.only(
                              top: 10,
                              left: 10,
                              right: 10,
                            ),
                            border: OutlineInputBorder(),
                            focusedBorder: OutlineInputBorder(
                              borderSide: BorderSide(color: Colors.blueAccent),
                            ),
                            hintText: "Input new class name",
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      InkWell(
                        child: Icon(
                          Icons.check,
                          size: Styles.datatableIconSize,
                        ),
                        onTap: () {
                          setState(() {
                            widget.onSave(controller.text);
                            isActivate = !isActivate;
                          });
                        },
                      ),
                      const SizedBox(width: 10),
                      InkWell(
                        child: Icon(
                          Icons.refresh,
                          size: Styles.datatableIconSize,
                        ),
                        onTap: () {
                          controller.text = "";
                        },
                      ),
                    ],
                  ),
                ),
      ),
    );
  }
}
