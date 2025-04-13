import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:flutter_rating_stars/flutter_rating_stars.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ModifyDatasetDialog extends ConsumerStatefulWidget {
  const ModifyDatasetDialog({super.key, required this.dataset});
  final Dataset dataset;

  @override
  ConsumerState<ModifyDatasetDialog> createState() =>
      _ModifyDatasetDialogState();
}

class _ModifyDatasetDialogState extends ConsumerState<ModifyDatasetDialog> {
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
  late DatasetType type = widget.dataset.type;
  // late DatasetTask task = widget.dataset.task;
  late double rating = widget.dataset.ranking;

  late final TextEditingController _nameController =
      TextEditingController()..text = widget.dataset.name;
  late final TextEditingController _descriptionController =
      TextEditingController()..text = widget.dataset.description;
  late final TextEditingController _dataPathController =
      TextEditingController()..text = widget.dataset.datasetPath;
  late final TextEditingController _labelPathController =
      TextEditingController()..text = widget.dataset.labelPath;

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _dataPathController.dispose();
    _labelPathController.dispose();
    super.dispose();
  }

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
        height: 460,
        child: SingleChildScrollView(
          padding: EdgeInsets.all(10),
          child: Column(
            spacing: 10,
            children: [
              /// basic info
              Text("Basic Info", style: titleStyle),
              Row(
                spacing: 10,
                children: [
                  Expanded(
                    flex: 1,
                    child: Text("Dataset Name*", style: labelStyle),
                  ),
                  Expanded(
                    flex: 1,
                    child: Text("Dataset Type", style: labelStyle),
                  ),
                ],
              ),
              SizedBox(
                height: 30,
                child: Row(
                  spacing: 10,
                  children: [
                    Expanded(
                      flex: 1,
                      child: TextField(
                        controller: _nameController,
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

                    Expanded(
                      flex: 1,
                      child: CustomDropDownButton<DatasetType>(
                        buttonIcon:
                            ({required showedMenu}) => SizedBox(
                              height: 30,
                              // width: 30,
                              child: Center(
                                child: Icon(
                                  Icons.arrow_drop_down,
                                  color: Colors.black,
                                ),
                              ),
                            ),
                        buttonIconFirst: false,
                        buttonStyle: ButtonStyle(
                          fixedSize: WidgetStateProperty.all(Size(100, 20)),
                          backgroundColor: WidgetStatePropertyAll(
                            Colors.grey[300],
                          ),
                          padding: WidgetStatePropertyAll(
                            const EdgeInsets.symmetric(
                              horizontal: 16,
                              vertical: 12,
                            ),
                          ),
                          textStyle: WidgetStatePropertyAll(
                            const TextStyle(
                              color: Colors.white,
                              fontWeight: FontWeight.w400,
                            ),
                          ),
                          shape: WidgetStatePropertyAll(
                            RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(4.0),
                            ),
                          ),
                        ),
                        buttonText: type.name,
                        position: DropDownButtonPosition.bottomCenter,
                        buttonIconColor: Colors.black,
                        buttonTextStyle: TextStyle(color: Colors.black),
                        menuItems:
                            DatasetType.values
                                .map(
                                  (e) => CustomDropDownButtonItem(
                                    value: e,
                                    text: e.name,
                                    onPressed: () {
                                      if (e != type) {
                                        setState(() {
                                          type = e;
                                        });
                                      }
                                    },
                                    buttonStyle: ButtonStyle(
                                      fixedSize: WidgetStateProperty.all(
                                        Size(100, 20),
                                      ),
                                      backgroundColor: WidgetStatePropertyAll(
                                        Colors.grey[300],
                                      ),
                                      textStyle: WidgetStatePropertyAll(
                                        const TextStyle(color: Colors.black),
                                      ),
                                      shape: WidgetStatePropertyAll(
                                        RoundedRectangleBorder(
                                          borderRadius: BorderRadius.zero,
                                        ),
                                      ),
                                    ),
                                    textStyle: TextStyle(color: Colors.black),
                                  ),
                                )
                                .toList(),
                        menuBorderRadius: BorderRadius.circular(8),
                        selectedValue: type,
                      ),
                    ),
                  ],
                ),
              ),
              // dataset path
              SizedBox(
                child: Row(
                  children: [
                    Text("Dataset Path*", style: labelStyle),
                    Spacer(),
                  ],
                ),
              ),
              SizedBox(
                height: 30,
                child: Row(
                  spacing: 10,
                  children: [
                    Expanded(
                      flex: 1,
                      child: TextField(
                        controller: _dataPathController,
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
                          hintText: "Dataset Path (required)",
                        ),
                      ),
                    ),
                    SizedBox(
                      width: 20,
                      child: InkWell(
                        onTap: () async {
                          final String? directoryPath =
                              await getDirectoryPath();
                          if (directoryPath == null) {
                            // Operation was canceled by the user.
                            return;
                          }
                          _dataPathController.text = directoryPath;
                        },
                        child: Icon(
                          Icons.file_open,
                          size: 14,
                          color: Colors.grey,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              // label path
              SizedBox(
                child: Row(
                  children: [Text("Label Path", style: labelStyle), Spacer()],
                ),
              ),
              SizedBox(
                height: 30,
                child: Row(
                  spacing: 10,
                  children: [
                    Expanded(
                      flex: 1,
                      child: TextField(
                        controller: _labelPathController,
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
                          hintText:
                              "Label Path (If empty, will generate automatically)",
                        ),
                      ),
                    ),
                    SizedBox(
                      width: 20,
                      child: InkWell(
                        onTap: () async {
                          final String? directoryPath =
                              await getDirectoryPath();
                          if (directoryPath == null) {
                            // Operation was canceled by the user.
                            return;
                          }
                          _labelPathController.text = directoryPath;
                        },
                        child: Icon(
                          Icons.file_open,
                          size: 14,
                          color: Colors.grey,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              // additional information
              Text("Additional Information", style: titleStyle),
              Row(
                spacing: 10,
                children: [
                  Expanded(flex: 1, child: Text("Ranking", style: labelStyle)),
                  Expanded(
                    flex: 1,
                    child: RatingStars(
                      value: rating,
                      onValueChanged: (v) {
                        //
                        setState(() {
                          rating = v;
                        });
                      },
                      starBuilder:
                          (index, color) => Icon(Icons.star, color: color),
                      starCount: 5,
                      starSize: 20,
                      valueLabelColor: const Color(0xff9b9b9b),
                      valueLabelTextStyle: const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w400,
                        fontStyle: FontStyle.normal,
                        fontSize: 12.0,
                      ),
                      valueLabelRadius: 10,
                      maxValue: 5,
                      starSpacing: 2,
                      maxValueVisibility: true,
                      valueLabelVisibility: false,
                      animationDuration: Duration(milliseconds: 1000),
                      valueLabelPadding: const EdgeInsets.symmetric(
                        vertical: 1,
                        horizontal: 8,
                      ),
                      valueLabelMargin: const EdgeInsets.only(right: 8),
                      starOffColor: const Color(0xffe7e8ea),
                      starColor: Colors.yellow,
                    ),
                  ),
                ],
              ),

              SizedBox(
                child: Row(
                  children: [Text("Description", style: labelStyle), Spacer()],
                ),
              ),
              TextField(
                controller: _descriptionController,
                style: textStyle,
                maxLines: 4,
                decoration: InputDecoration(
                  hintStyle: hintStyle,
                  contentPadding: EdgeInsets.only(top: 10, left: 10, right: 10),
                  border: OutlineInputBorder(),
                  focusedBorder: OutlineInputBorder(
                    borderSide: BorderSide(color: Colors.blueAccent),
                  ),
                  hintText: "Dataset Description",
                ),
              ),

              SizedBox(
                height: 30,
                child: Row(
                  children: [
                    Spacer(),
                    ElevatedButton(
                      style: ButtonStyle(
                        fixedSize: WidgetStateProperty.all(Size(100, 20)),
                        backgroundColor: WidgetStatePropertyAll(
                          Colors.grey[300],
                        ),
                        padding: WidgetStatePropertyAll(
                          const EdgeInsets.symmetric(
                            horizontal: 16,
                            vertical: 12,
                          ),
                        ),
                        textStyle: WidgetStatePropertyAll(
                          const TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.w400,
                          ),
                        ),
                        shape: WidgetStatePropertyAll(
                          RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(4.0),
                          ),
                        ),
                      ),
                      onPressed: () {
                        if (_nameController.text.isEmpty ||
                            _dataPathController.text.isEmpty) {
                          ToastUtils.error(context, title: "Input Error");
                          return;
                        }
                        Dataset dataset =
                            Dataset()
                              ..datasetPath = _dataPathController.text
                              ..labelPath = _labelPathController.text
                              ..name = _nameController.text
                              ..description = _descriptionController.text
                              ..type = type
                              ..ranking = rating
                              ..id = widget.dataset.id
                              ..createdAt = widget.dataset.createdAt;
                        Navigator.of(context).pop(dataset);
                      },
                      child: Text(
                        "Submit",
                        style: TextStyle(color: Colors.black),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
