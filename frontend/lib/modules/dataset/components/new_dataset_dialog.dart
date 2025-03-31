import 'package:auto_ml/modules/isar/dataset.dart';
import 'package:flutter/material.dart';

class NewDatasetDialog extends StatefulWidget {
  const NewDatasetDialog({super.key, required this.type});
  final DatasetType type;

  @override
  State<NewDatasetDialog> createState() => _NewDatasetDialogState();
}

class _NewDatasetDialogState extends State<NewDatasetDialog> {
  late TextStyle titleStyle = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.bold,
  );

  late TextStyle labelStyle = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.bold,
  );

  late TextStyle textStyle = TextStyle(fontSize: 12);

  late TextStyle hintStyle = TextStyle(fontSize: 12, color: Colors.grey);

  @override
  Widget build(BuildContext context) {
    return Material(
      borderRadius: BorderRadius.circular(4),
      elevation: 10,
      child: Container(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(4),
          color: Colors.white,
        ),
        width: 400,
        height: 500,
        child: SingleChildScrollView(
          padding: EdgeInsets.all(10),
          child: Column(
            spacing: 10,
            children: [
              // Text(
              //   "New Dataset (${widget.type.name})",
              //   style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              // ),
              Text("1. Basic Info", style: titleStyle),
              Row(
                children: [Text("Dataset Name", style: labelStyle), Spacer()],
              ),
              SizedBox(
                height: 30,
                child: TextField(
                  style: textStyle,
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
                    hintText: "Dataset Name (required)",
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
