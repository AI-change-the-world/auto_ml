import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/dataset/components/selection_widget.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_state.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_rating_stars/flutter_rating_stars.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NewDatasetDialog extends ConsumerStatefulWidget {
  const NewDatasetDialog({super.key, required this.initialType});
  final DatasetType initialType;

  @override
  ConsumerState<NewDatasetDialog> createState() => _NewDatasetDialogState();
}

class _NewDatasetDialogState extends ConsumerState<NewDatasetDialog> {
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
  late DatasetType type = widget.initialType;
  late DatasetTask task = DatasetTask.classification;
  late double rating = 0;

  late final TextEditingController _nameController = TextEditingController();
  late final TextEditingController _descriptionController =
      TextEditingController();
  late final TextEditingController _dataPathController =
      TextEditingController();
  // late final TextEditingController _labelPathController =
  //     TextEditingController();
  late final TextEditingController _usernameController =
      TextEditingController();
  late final TextEditingController _passwordController =
      TextEditingController();

  @override
  void dispose() {
    _nameController.dispose();
    _descriptionController.dispose();
    _dataPathController.dispose();
    // _labelPathController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  int selectedDatasetFrom = 0;

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
        height:
            selectedDatasetFrom == 0 || selectedDatasetFrom == 3 ? 400 : 530,
        child: SingleChildScrollView(
          padding: EdgeInsets.all(10),
          child: Column(
            spacing: 10,
            children: [
              /// basic info
              Text(t.dialogs.new_dataset.basic, style: titleStyle),
              Row(
                spacing: 10,
                children: [
                  Expanded(
                    flex: 1,
                    child: Text(
                      t.dialogs.new_dataset.dataset_name,
                      style: labelStyle,
                    ),
                  ),
                  Expanded(
                    flex: 1,
                    child: Text(
                      t.dialogs.new_dataset.dataset_type,
                      style: labelStyle,
                    ),
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
                          hintText: t.dialogs.new_dataset.name_hint,
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
                                        const TextStyle(
                                          color: Colors.black,
                                          fontSize: 12,
                                        ),
                                      ),
                                      shape: WidgetStatePropertyAll(
                                        RoundedRectangleBorder(
                                          borderRadius: BorderRadius.zero,
                                        ),
                                      ),
                                    ),
                                    textStyle: TextStyle(
                                      color: Colors.black,
                                      fontSize: 12,
                                    ),
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
              // dataset type
              SizedBox(
                child: Row(
                  spacing: 5,
                  children: [
                    Text(
                      t.dialogs.new_dataset.dataset_location,
                      style: labelStyle,
                    ),
                    Tooltip(
                      waitDuration: Duration(milliseconds: 500),
                      message: t.dialogs.new_dataset.tool_tip,
                      child: Icon(Icons.warning_amber_outlined, size: 18),
                    ),
                    Spacer(),
                  ],
                ),
              ),
              SizedBox(
                height: 30,
                child: SelectionWidget(
                  items: DatasetFrom.values.map((e) => e.name).toList(),
                  onChanged: (s) {
                    switch (s) {
                      case "Empty":
                        selectedDatasetFrom = 0;
                        break;
                      case "S3":
                        selectedDatasetFrom = 1;
                        break;
                      case "WebDAV":
                        selectedDatasetFrom = 2;
                        break;
                      default:
                        selectedDatasetFrom = 3;
                        break;
                    }
                    setState(() {});
                  },
                ),
              ),

              if (selectedDatasetFrom == 1 || selectedDatasetFrom == 2)
                Row(
                  children: [
                    Expanded(
                      flex: 1,
                      child: Text(
                        selectedDatasetFrom == 1 ? "AK*" : "Username*",
                        style: labelStyle,
                      ),
                    ),
                    Expanded(
                      flex: 1,
                      child: Text(
                        selectedDatasetFrom == 1 ? "SK*" : "Password*",
                        style: labelStyle,
                      ),
                    ),
                  ],
                ),
              if (selectedDatasetFrom == 1 || selectedDatasetFrom == 2)
                SizedBox(
                  height: 30,
                  child: Row(
                    spacing: 10,
                    children: [
                      Expanded(
                        flex: 1,
                        child: TextField(
                          controller: _usernameController,
                          // controller: _nameController,
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
                                selectedDatasetFrom == 1 ? "AK" : "Username",
                          ),
                        ),
                      ),
                      Expanded(
                        flex: 1,
                        child: TextField(
                          controller: _passwordController,
                          // controller: _nameController,
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
                                selectedDatasetFrom == 1 ? "SK" : "Password",
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              if (selectedDatasetFrom == 1 || selectedDatasetFrom == 2)
                // dataset path
                SizedBox(
                  child: Row(
                    children: [
                      Text(t.dialogs.new_dataset.path, style: labelStyle),
                      Spacer(),
                    ],
                  ),
                ),
              if (selectedDatasetFrom == 1 || selectedDatasetFrom == 2)
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
                      // SizedBox(
                      //   width: 20,
                      //   child: InkWell(
                      //     onTap: () async {
                      //       if (kIsWeb) {
                      //         ToastUtils.error(
                      //           context,
                      //           title: "Not supported",
                      //           description:
                      //               "Sorry, this feature is not supported in web, please input local path instead.",
                      //         );
                      //         return;
                      //       }

                      //       final String? directoryPath =
                      //           await getDirectoryPath();
                      //       if (directoryPath == null) {
                      //         // Operation was canceled by the user.
                      //         return;
                      //       }
                      //       _dataPathController.text = directoryPath;
                      //     },
                      //     child: Icon(
                      //       Icons.file_open,
                      //       size: 14,
                      //       color: Colors.grey,
                      //     ),
                      //   ),
                      // ),
                    ],
                  ),
                ),
              // label path
              // SizedBox(
              //   child: Row(
              //     children: [Text("Label Path", style: labelStyle), Spacer()],
              //   ),
              // ),
              // SizedBox(
              //   height: 30,
              //   child: Row(
              //     spacing: 10,
              //     children: [
              //       Expanded(
              //         flex: 1,
              //         child: TextField(
              //           controller: _labelPathController,
              //           style: textStyle,
              //           decoration: InputDecoration(
              //             hintStyle: hintStyle,
              //             contentPadding: EdgeInsets.only(
              //               top: 10,
              //               left: 10,
              //               right: 10,
              //             ),
              //             border: OutlineInputBorder(),
              //             focusedBorder: OutlineInputBorder(
              //               borderSide: BorderSide(color: Colors.blueAccent),
              //             ),
              //             hintText:
              //                 "Label Path (If empty, will generate automatically)",
              //           ),
              //         ),
              //       ),
              //       SizedBox(
              //         width: 20,
              //         child: InkWell(
              //           onTap: () async {
              //             final String? directoryPath =
              //                 await getDirectoryPath();
              //             if (directoryPath == null) {
              //               // Operation was canceled by the user.
              //               return;
              //             }
              //             _labelPathController.text = directoryPath;
              //           },
              //           child: Icon(
              //             Icons.file_open,
              //             size: 14,
              //             color: Colors.grey,
              //           ),
              //         ),
              //       ),
              //     ],
              //   ),
              // ),
              // additional information
              Text(t.dialogs.new_dataset.additional, style: titleStyle),
              Row(
                spacing: 10,
                children: [
                  Expanded(
                    flex: 1,
                    child: Text(t.dialogs.new_dataset.rank, style: labelStyle),
                  ),
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
                  children: [
                    Text(t.dialogs.new_dataset.description, style: labelStyle),
                    Spacer(),
                  ],
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
                  hintText: t.dialogs.new_dataset.description_hint,
                ),
              ),

              SizedBox(
                height: 30,
                child: Row(
                  children: [
                    Spacer(),
                    ElevatedButton(
                      style: Styles.getDefaultButtonStyle(),
                      onPressed: () {
                        if (_nameController.text.isEmpty) {
                          ToastUtils.error(
                            context,
                            title: t.global.errors.name_cannot_be_empty,
                          );
                          return;
                        }
                        Dataset dataset =
                            Dataset()
                              ..datasetPath = _dataPathController.text
                              // ..labelPath = _labelPathController.text
                              ..name = _nameController.text
                              ..description = _descriptionController.text
                              ..type = type
                              ..storageType = selectedDatasetFrom
                              ..username = _usernameController.text
                              ..password = _passwordController.text
                              ..ranking = rating;
                        Navigator.of(context).pop(dataset);
                      },
                      child: Text(
                        t.submit,
                        style: Styles.defaultButtonTextStyle,
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
