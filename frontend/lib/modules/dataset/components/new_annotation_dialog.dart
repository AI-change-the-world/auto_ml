import 'package:auto_ml/modules/dataset/components/selection_widget.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:file_selector/file_selector.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class NewAnnotationDialog extends StatefulWidget {
  const NewAnnotationDialog({super.key});

  @override
  State<NewAnnotationDialog> createState() => _NewAnnotationDialogState();
}

class _NewAnnotationDialogState extends State<NewAnnotationDialog> {
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

  int selectedDatasetFrom = 0;
  late DatasetTask type = DatasetTask.detection;

  late final TextEditingController _labelPathController =
      TextEditingController();

  late final TextEditingController _usernameController =
      TextEditingController();
  late final TextEditingController _passwordController =
      TextEditingController();
  late final TextEditingController _classesController = TextEditingController();
  @override
  Widget build(BuildContext context) {
    return Material(
      borderRadius: BorderRadius.circular(4),
      elevation: 10,
      child: Container(
        padding: EdgeInsets.all(10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(4),
          color: Colors.white,
        ),
        width: 400,
        height:
            selectedDatasetFrom == 0 || selectedDatasetFrom == 3 ? 300 : 370,
        child: Column(
          spacing: 10,
          children: [
            Text("Select annotation folder or create new", style: titleStyle),
            SizedBox(
              child: Row(
                spacing: 5,
                children: [
                  Text("Original annotation folder*", style: labelStyle),
                  Tooltip(
                    waitDuration: Duration(milliseconds: 500),
                    message: "2025.05.03版本开始，所有非对象存储的数据将全部同步到对象存储上",
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
                    case "Local":
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

            SizedBox(
              height: 30,
              child: Row(
                spacing: 10,
                children: [
                  Expanded(flex: 1, child: Text("标注任务类型", style: labelStyle)),
                  Expanded(
                    flex: 1,
                    child: CustomDropDownButton<DatasetTask>(
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
                          DatasetTask.values
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

            SizedBox(
              height: 30,
              child: Row(
                spacing: 10,
                children: [
                  Expanded(flex: 1, child: Text("标注类型", style: labelStyle)),
                  Expanded(
                    flex: 2,
                    child: TextField(
                      controller: _classesController,
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
                        hintText: "标注类型(必填，以英文分号';'隔开)",
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // dataset path
            SizedBox(
              child: Row(
                spacing: 5,
                children: [
                  Text("Annotation path", style: labelStyle),
                  Tooltip(
                    waitDuration: Duration(milliseconds: 500),
                    message: "如果为空，则默认创建一个新的空标注集",
                    child: Icon(Icons.info, size: 18),
                  ),
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
                        hintText: "Annotation Path",
                      ),
                    ),
                  ),
                  SizedBox(
                    width: 20,
                    child: InkWell(
                      onTap: () async {
                        if (kIsWeb) {
                          ToastUtils.error(
                            context,
                            title: "Not supported",
                            description:
                                "Sorry, this feature is not supported in web, please input local path instead.",
                          );
                          return;
                        }

                        final String? directoryPath = await getDirectoryPath();
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
            SizedBox(
              height: 30,
              child: Row(
                children: [
                  Spacer(),
                  ElevatedButton(
                    style: ButtonStyle(
                      fixedSize: WidgetStateProperty.all(Size(100, 20)),
                      backgroundColor: WidgetStatePropertyAll(Colors.grey[300]),
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
                      if (_classesController.text.isEmpty) {
                        ToastUtils.error(context, title: "类别不能为空");
                        return;
                      }

                      Map<String, dynamic> annotation = {
                        "labelPath": _labelPathController.text,
                        "storageType": selectedDatasetFrom,
                        "username": _usernameController.text,
                        "password": _passwordController.text,
                        "type": type.index,
                        "classes": _classesController.text,
                      };

                      Navigator.of(context).pop(annotation);
                    },
                    child: Text("Submit", style: Styles.defaultButtonTextStyle),
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
