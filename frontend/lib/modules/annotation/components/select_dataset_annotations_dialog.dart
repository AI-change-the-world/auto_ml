import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/annotation/notifiers/select_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SelectDatasetAnnotationsDialog extends ConsumerStatefulWidget {
  const SelectDatasetAnnotationsDialog({super.key});

  @override
  ConsumerState<SelectDatasetAnnotationsDialog> createState() =>
      _SelectDatasetAnnotationsDialogState();
}

class _SelectDatasetAnnotationsDialogState
    extends ConsumerState<SelectDatasetAnnotationsDialog> {
  bool showSearch = false;
  String searchText = "";
  @override
  Widget build(BuildContext context) {
    final state = ref.watch(selectDatasetAnnotationNotifierProvider);

    return Material(
      elevation: 10,
      borderRadius: BorderRadius.circular(10),
      color: Colors.transparent,
      child: Container(
        width: 400,
        height: 400,
        // padding: EdgeInsets.all(10),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          color: Colors.grey[200],
        ),
        child: state.when(
          data: (data) {
            return Column(
              children: [
                Container(
                  width: double.infinity,
                  height: 40,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.only(
                      topLeft: Radius.circular(10),
                      topRight: Radius.circular(10),
                    ),
                    // color: Theme.of(context).primaryColorLight,
                    gradient: LinearGradient(
                      begin: Alignment.centerLeft,
                      end: Alignment.centerRight,
                      stops: [0.0, 0.25, 0.75, 1.0],
                      colors: [
                        Theme.of(context).primaryColor,
                        Theme.of(context).primaryColorLight,
                        Theme.of(context).primaryColorLight,
                        Theme.of(context).primaryColor,
                      ],
                    ),
                  ),
                  child: Center(
                    child: Text(
                      "Create/Restore Annotation Task",
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Colors.black54,
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: Padding(
                    padding: const EdgeInsets.all(8.0),
                    child: Row(
                      spacing: 10,
                      children: [
                        Expanded(
                          child: Container(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(10),
                              color: Colors.white,
                            ),
                            padding: EdgeInsets.all(10),
                            child: Column(
                              spacing: 5,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Text(
                                      "${t.annotation_screen.select_dataset}: ",
                                      style: Styles.defaultButtonTextStyleGrey,
                                    ),
                                    Spacer(),
                                    InkWell(
                                      child:
                                          !showSearch
                                              ? Icon(
                                                Icons.search,
                                                size: Styles.datatableIconSize,
                                                color: Colors.grey[500],
                                              )
                                              : Icon(
                                                Icons.search_off,
                                                size: Styles.datatableIconSize,
                                                color: Colors.grey[500],
                                              ),
                                      onTap: () {
                                        setState(() {
                                          showSearch = !showSearch;
                                        });
                                      },
                                    ),
                                  ],
                                ),
                                AnimatedContainer(
                                  height: showSearch ? 30 : 0,
                                  duration: Duration(milliseconds: 300),
                                  child: TextField(
                                    style: TextStyle(fontSize: 12),
                                    onChanged: (value) {
                                      setState(() {
                                        searchText = value;
                                      });
                                    },
                                    decoration: InputDecoration(
                                      hintStyle:
                                          Styles.defaultButtonTextStyleGrey,
                                      contentPadding: EdgeInsets.only(
                                        top: 10,
                                        left: 10,
                                        right: 10,
                                      ),
                                      border:
                                          showSearch
                                              ? OutlineInputBorder()
                                              : InputBorder.none,
                                      focusedBorder: OutlineInputBorder(
                                        borderSide:
                                            showSearch
                                                ? BorderSide(
                                                  color: Colors.blueAccent,
                                                )
                                                : BorderSide.none,
                                      ),
                                      hintText: "Search Dataset",
                                    ),
                                  ),
                                ),
                                Expanded(
                                  child: ListView.builder(
                                    itemBuilder: (c, i) {
                                      return Visibility(
                                        visible:
                                            data.datasets[i].name
                                                .toLowerCase()
                                                .contains(
                                                  searchText.toLowerCase(),
                                                ) ||
                                            searchText.isEmpty,
                                        child: InkWell(
                                          onTap: () {
                                            ref
                                                .read(
                                                  selectDatasetAnnotationNotifierProvider
                                                      .notifier,
                                                )
                                                .onDatasetSelectionChanged(
                                                  data.datasets[i].id,
                                                );
                                          },
                                          child: Container(
                                            decoration: BoxDecoration(
                                              color:
                                                  data.currentDatasetId ==
                                                          data.datasets[i].id
                                                      ? Colors.lightBlueAccent
                                                      : Colors.transparent,
                                            ),
                                            child: Text(
                                              data.datasets[i].name,
                                              maxLines: 1,
                                              softWrap: true,
                                              overflow: TextOverflow.ellipsis,
                                              style: TextStyle(
                                                color:
                                                    data.currentDatasetId ==
                                                            data.datasets[i].id
                                                        ? Colors.white
                                                        : Colors.black,
                                                fontSize: 12,
                                              ),
                                            ),
                                          ),
                                        ),
                                      );
                                    },
                                    itemCount: data.datasets.length,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        Expanded(
                          child: Container(
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(10),
                              color: Colors.white,
                            ),
                            padding: EdgeInsets.all(10),
                            child: Column(
                              spacing: 5,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  "${t.annotation_screen.select_annotation}:",
                                  style: Styles.defaultButtonTextStyleGrey,
                                ),
                                Expanded(
                                  child: ListView.builder(
                                    itemBuilder: (c, i) {
                                      var dataset = data.datasets.firstWhere(
                                        (v) => v.id == data.currentDatasetId,
                                      );
                                      return InkWell(
                                        onTap: () {
                                          ref
                                              .read(
                                                currentDatasetAnnotationNotifierProvider
                                                    .notifier,
                                              )
                                              .changeDatasetAndAnnotation(
                                                dataset,
                                                data.anntations[data
                                                    .currentDatasetId]![i],
                                              );
                                          Navigator.of(context).pop();
                                        },
                                        child: Tooltip(
                                          message:
                                              data
                                                  .anntations[data
                                                      .currentDatasetId]![i]
                                                  .annotationSavePath ??
                                              "",
                                          child: Text.rich(
                                            TextSpan(
                                              children: [
                                                TextSpan(
                                                  text:
                                                      "${datasetTaskGetById(data.anntations[data.currentDatasetId]![i].annotationType).name}: ",
                                                  style:
                                                      Styles
                                                          .defaultButtonTextStyle,
                                                ),
                                                TextSpan(
                                                  text:
                                                      "  ${data.anntations[data.currentDatasetId]![i].annotationSavePath}",
                                                  style:
                                                      Styles
                                                          .defaultButtonTextStyleGrey,
                                                ),
                                              ],
                                            ),
                                            maxLines: 1,
                                            softWrap: true,
                                            overflow: TextOverflow.ellipsis,
                                          ),
                                        ),
                                      );
                                    },
                                    itemCount:
                                        data
                                            .anntations[data.currentDatasetId]
                                            ?.length ??
                                        0,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            );
          },
          error: (e, _) {
            return Center(child: Text(e.toString()));
          },
          loading: () => Center(child: CircularProgressIndicator()),
        ),
      ),
    );
  }
}
