import 'package:flutter/material.dart';

class EditableLabel extends StatefulWidget {
  const EditableLabel({
    super.key,
    required this.label,
    required this.onSubmit,
    required this.onTap,
    this.isEdit = false,
  });
  final String label;
  final void Function(String) onSubmit;
  final VoidCallback onTap;
  final bool isEdit;

  @override
  State<EditableLabel> createState() => _EditableLabelState();
}

class _EditableLabelState extends State<EditableLabel> {
  late bool isEditing = widget.isEdit;

  late final TextEditingController controller =
      TextEditingController()..text = widget.label;

  FocusNode focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
  }

  @override
  void didUpdateWidget(covariant EditableLabel oldWidget) {
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
                : Align(
                  alignment: Alignment.centerLeft,
                  child: Text(controller.text),
                ),
      ),
    );
  }
}
