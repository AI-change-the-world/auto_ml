// ignore_for_file: avoid_init_to_null

import 'dart:async';

import 'package:auto_ml/api.dart';
import 'package:auto_ml/common/dialog_wrapper.dart';
import 'package:auto_ml/common/sse/sse.dart';
import 'package:auto_ml/modules/async_state_button.dart';
import 'package:auto_ml/modules/data_augment/components/model_struture_viewer.dart';
import 'package:auto_ml/modules/data_augment/notifiers/gan_notifiers.dart';
import 'package:auto_ml/modules/data_augment/utils.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:auto_ml/utils/toast_utils.dart';
import 'package:basic_dropdown_button/basic_dropwon_button_widget.dart';
import 'package:basic_dropdown_button/custom_dropdown_button.dart';
import 'package:choice/choice.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class GanDialog extends StatefulWidget {
  const GanDialog({super.key});

  @override
  State<GanDialog> createState() => _GanDialogState();
}

class _GanDialogState extends State<GanDialog> {
  late final PageController pageController = PageController(initialPage: 0);

  late List<Widget> pages = [_TrainningPage(), _EvaluationPage()];

  int currentPage = 0;

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return dialogWrapper(
      width: currentPage == 0 ? 500 : MediaQuery.of(context).size.width * 0.9,
      height: MediaQuery.of(context).size.height * 0.9,
      child: Container(
        width: currentPage == 0 ? 500 : MediaQuery.of(context).size.width * 0.9,
        padding: EdgeInsetsGeometry.all(10),
        child: Column(
          spacing: 20,
          children: [
            SizedBox(
              height: 30,
              child: Row(
                mainAxisAlignment: MainAxisAlignment.start,
                spacing: 5,
                children: [
                  InkWell(
                    onTap: () {
                      if (currentPage == 1) {
                        pageController.jumpToPage(0);
                      }
                    },
                    child: Container(
                      height: 30,
                      width: 80,
                      decoration: BoxDecoration(
                        color:
                            currentPage == 0 ? Colors.grey[300] : Colors.white,
                        border: Border.all(color: Colors.grey[300]!),
                      ),

                      child: Center(
                        child: Text(
                          "Train",
                          style:
                              currentPage == 0
                                  ? Styles.defaultButtonTextStyle
                                  : Styles.defaultButtonTextStyleGrey,
                        ),
                      ),
                    ),
                  ),
                  InkWell(
                    onTap: () {
                      if (currentPage == 0) {
                        pageController.jumpToPage(1);
                      }
                    },
                    child: Container(
                      height: 30,
                      width: 80,
                      decoration: BoxDecoration(
                        color:
                            currentPage == 1 ? Colors.grey[300] : Colors.white,
                        border: Border.all(color: Colors.grey[300]!),
                      ),

                      child: Center(
                        child: Text(
                          "Evaluate",
                          style:
                              currentPage == 1
                                  ? Styles.defaultButtonTextStyle
                                  : Styles.defaultButtonTextStyleGrey,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: PageView(
                onPageChanged: (value) {
                  if (currentPage != value) {
                    setState(() {
                      currentPage = value;
                    });
                  }
                },
                physics: NeverScrollableScrollPhysics(),
                controller: pageController,
                children: pages,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EvaluationPage extends StatefulWidget {
  const _EvaluationPage();

  @override
  State<_EvaluationPage> createState() => __EvaluationPageState();
}

class __EvaluationPageState extends State<_EvaluationPage> {
  int generateCount = 5;
  final StreamController<String> ss = StreamController.broadcast();
  List<String> images = [];

  @override
  void dispose() {
    ss.close();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    ss.stream.listen((event) {
      if (event.contains("[DONE]")) {
        ToastUtils.success(null, title: "Generated done");

        buttonState.currentState?.changeCurrentState(FutureButtonState.initial);
      }
      if (event.startsWith("path:") && event.contains("png")) {
        String url = event.split(":")[1];
        Future.microtask(() async {
          final s = await getPresignUrl(url);
          images.add(s);
          setState(() {});
        });
      }
    });
  }

  final GlobalKey<FutureStatusButtonSimpleState> buttonState =
      GlobalKey<FutureStatusButtonSimpleState>();

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          height: 30,
          child: Row(
            children: [
              Text(
                "GAN",
                style: Styles.defaultButtonTextStyle.copyWith(fontSize: 20),
              ),
              Spacer(),

              Text("Generate Count: ", style: Styles.defaultButtonTextStyle),
              SizedBox(
                width: 80,
                child: CustomDropDownButton<int>(
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
                    backgroundColor: WidgetStatePropertyAll(Colors.grey[300]),
                    padding: WidgetStatePropertyAll(
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
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
                  buttonText: generateCount.toString(),
                  position: DropDownButtonPosition.bottomCenter,
                  buttonIconColor: Colors.black,
                  buttonTextStyle: Styles.defaultButtonTextStyle,
                  menuItems:
                      [5, 10, 15, 20]
                          .map(
                            (e) => CustomDropDownButtonItem(
                              value: e,
                              text: e.toString(),
                              onPressed: () {
                                if (e != generateCount) {
                                  setState(() {
                                    generateCount = e;
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
                  selectedValue: generateCount,
                ),
              ),
              const SizedBox(width: 10),

              FutureStatusButtonSimple(
                key: buttonState,
                initialChild: Text(
                  "Submit",
                  style: Styles.defaultButtonTextStyle,
                ),
                onPressed: () {
                  setState(() {
                    images.clear();
                  });

                  Map<String, int> data = {"count": generateCount};
                  sse(Api.gan, data, ss);

                  buttonState.currentState?.changeCurrentState(
                    FutureButtonState.loading,
                  );
                },
              ),
            ],
          ),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: EdgeInsets.all(10),
            child: SizedBox(
              width: double.infinity,
              child: Wrap(
                runAlignment: WrapAlignment.start,
                alignment: WrapAlignment.start,
                spacing: 10,
                runSpacing: 10,
                children:
                    images
                        .map((v) => Image.network(v, width: 256, height: 256))
                        .toList(),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _TrainningPage extends StatefulWidget {
  const _TrainningPage();

  @override
  State<_TrainningPage> createState() => __TrainningPageState();
}

class __TrainningPageState extends State<_TrainningPage> {
  String? selectedModel = null;
  List<String> models = ["SimpleGan"];

  String? selectedDataset = null;
  // List<String> datasets = ["leather"];

  void setSelectedValue(String? value) {
    if (value != selectedModel) setState(() => selectedModel = value);
  }

  int epochs = 100;

  final List<int> options = [1, 2, 4, 8, 16, 32, 64];
  int selectedOption = 0;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      spacing: 10,
      children: [
        SizedBox(
          child: Row(
            children: [
              Text("Select base model:", style: Styles.defaultButtonTextStyle),
              SizedBox(width: 10),
              if (selectedModel != null)
                Text(selectedModel!, style: Styles.defaultButtonTextStyleGrey),
              SizedBox(width: 5),
              if (selectedModel != null)
                Tooltip(
                  message: "View Model Structure",
                  child: InkWell(
                    onTap: () {
                      showGeneralDialog(
                        context: context,
                        barrierDismissible: true,
                        barrierColor: Styles.barriarColor,
                        barrierLabel: "ModelStrutureViewer",
                        pageBuilder: (c, _, _) {
                          return Center(
                            child: ModelStrutureViewer(modelId: selectedModel!),
                          );
                        },
                      );
                    },
                    child: Icon(
                      Icons.visibility,
                      size: Styles.datatableIconSize,
                    ),
                  ),
                ),
            ],
          ),
        ),

        InlineChoice<String>.single(
          clearable: true,
          value: selectedModel,
          onChanged: setSelectedValue,
          itemCount: models.length,
          itemBuilder: (state, i) {
            return ChoiceChip(
              selected: state.selected(models[i]),
              onSelected: state.onSelected(models[i]),
              label: Text(models[i], style: Styles.defaultButtonTextStyle),
            );
          },
          listBuilder: ChoiceList.createWrapped(
            spacing: 10,
            runSpacing: 10,
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
          ),
        ),

        Text("Select dataset:", style: Styles.defaultButtonTextStyle),

        Consumer(
          builder: (context, ref, child) {
            final state = ref.watch(getAllDatasetProvider);
            return state.when(
              data: (d) {
                return InlineChoice<String>.single(
                  clearable: true,
                  onChanged: (value) {
                    if (value != selectedDataset) {
                      selectedDataset = value;
                      setState(() {});
                    }
                  },
                  itemCount: d.length,
                  value: selectedDataset,
                  itemBuilder: (state, i) {
                    return ChoiceChip(
                      selected: state.selected(d[i]),
                      onSelected: state.onSelected(d[i]),
                      label: Text(d[i], style: Styles.defaultButtonTextStyle),
                    );
                  },
                  listBuilder: ChoiceList.createWrapped(
                    spacing: 10,
                    runSpacing: 10,
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 10,
                    ),
                  ),
                );
              },
              error: (e, _) {
                return SizedBox(
                  height: 30,
                  child: Text("Error", style: Styles.defaultButtonTextStyle),
                );
              },
              loading:
                  () => SizedBox(
                    height: 30,
                    child: Center(child: CircularProgressIndicator()),
                  ),
            );
          },
        ),

        Text.rich(
          TextSpan(
            children: [
              TextSpan(
                text: "Trainning epochs:",
                style: Styles.defaultButtonTextStyle,
              ),
              if (selectedModel == "SimpleGan")
                TextSpan(
                  text: " (800-1000 recommended)",
                  style: Styles.defaultButtonTextStyleGrey,
                ),
            ],
          ),
        ),

        Row(
          children: [
            CupertinoSlider(
              value: epochs.toDouble(),
              min: 100,
              max: 2000,
              divisions: 19,
              // label: _strength.toString(),
              onChanged: (double value) {
                setState(() {
                  epochs = value.toInt();
                });
              },
            ),
            SizedBox(width: 10),
            Text('Epochs: $epochs', style: Styles.defaultButtonTextStyleNormal),
          ],
        ),

        Text("Batchsize:", style: Styles.defaultButtonTextStyle),

        Row(
          children: [
            CupertinoSlider(
              value: selectedOption.toDouble(),
              min: 0,
              max: (options.length - 1).toDouble(),
              divisions: options.length - 1,
              onChanged: (value) {
                setState(() {
                  selectedOption = value.round(); // 只能选离散点
                });
              },
            ),
            SizedBox(width: 10),
            Text(
              'Batchsize: ${options[selectedOption]}',
              style: Styles.defaultButtonTextStyleNormal,
            ),
          ],
        ),

        SizedBox(
          height: 30,
          child: Row(
            children: [
              Spacer(),
              ElevatedButton(
                style: ElevatedButton.styleFrom(
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(4), // 设置圆角半径
                  ),
                  padding: EdgeInsets.symmetric(
                    horizontal: 6,
                    vertical: 3,
                  ), // 调整按钮大小
                ),
                onPressed: () {},
                child: Text("Submit", style: Styles.defaultButtonTextStyle),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
