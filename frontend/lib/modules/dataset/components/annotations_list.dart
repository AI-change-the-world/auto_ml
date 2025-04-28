import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/entity/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/notifier/annotation_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:data_table_2/data_table_2.dart';

class AnnotationsList extends ConsumerStatefulWidget {
  const AnnotationsList({super.key});

  @override
  ConsumerState<AnnotationsList> createState() => _AnnotationsListState();
}

class _AnnotationsListState extends ConsumerState<AnnotationsList> {
  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(annotationListProvider.notifier).updateData();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(annotationListProvider);

    return state.when(
      data: (data) {
        final current = ref.read(datasetNotifierProvider).value?.current;
        if (current == null) {
          return Center(
            child: Text(
              "No dataset selected",
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
          );
        }

        return Padding(
          padding: EdgeInsets.all(10),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            spacing: 10,
            children: [
              Expanded(
                child: DataTable2(
                  empty: Center(
                    child: Text(t.annotation_screen.list_widget.no_data),
                  ),
                  columnSpacing: 10,
                  headingRowDecoration: BoxDecoration(
                    color: Colors.grey.shade200,
                  ),
                  columns: columns,
                  rows: getRows(data.annotations),
                ),
              ),
            ],
          ),
        );
      },
      error: (e, s) {
        return Center(child: Text(e.toString()));
      },
      loading: () => Center(child: CircularProgressIndicator()),
    );
  }

  late List<DataColumn> columns = [
    DataColumn2(label: Text('Id', style: defaultTextStyle2), fixedWidth: 40),
    DataColumn2(
      label: Text('Annotation path', style: defaultTextStyle2),
      size: ColumnSize.L,
    ),
    DataColumn2(label: Text('Type', style: defaultTextStyle2), fixedWidth: 100),
    DataColumn2(
      label: Text('Created at', style: defaultTextStyle2),
      size: ColumnSize.M,
    ),
    DataColumn2(
      label: Text('Updated at', style: defaultTextStyle2),
      size: ColumnSize.M,
    ),
    DataColumn2(
      label: Text('Operations', style: defaultTextStyle2),
      fixedWidth: 120,
    ),
  ];

  List<DataRow> getRows(List<Annotation> annotations) {
    return annotations.map((annotation) {
      return DataRow(
        cells: [
          DataCell(Text(annotation.id.toString(), style: defaultTextStyle)),
          DataCell(
            Tooltip(
              message: annotation.annotationPath.toString(),
              child: Text(
                annotation.annotationPath.toString(),
                style: defaultTextStyle,
                maxLines: 1,
                softWrap: true,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
          DataCell(
            Text(
              datasetTaskGetById(annotation.annotationType).name,
              style: defaultTextStyle,
            ),
          ),
          DataCell(
            Text(
              annotation.createdAt.toString().split(".").first,
              style: defaultTextStyle,
            ),
          ),
          DataCell(
            Text(
              annotation.updatedAt.toString().split(".").first,
              style: defaultTextStyle,
            ),
          ),
          DataCell(
            Row(
              spacing: 10,
              children: [
                InkWell(
                  onTap: () {},
                  child: Tooltip(
                    message: "Edit",
                    child: Icon(Icons.edit, size: 20),
                  ),
                ),
                InkWell(
                  onTap: () {},
                  child: Tooltip(
                    message: "Annotate",
                    child: Icon(Icons.square_outlined, size: 20),
                  ),
                ),
                InkWell(
                  onTap: () {},
                  child: Tooltip(
                    message: "Train",
                    child: Icon(Icons.work_outline_outlined, size: 20),
                  ),
                ),
                InkWell(
                  onTap: () {},
                  child: Tooltip(
                    message: "classes",
                    child: Icon(Icons.class_outlined, size: 20),
                  ),
                ),
              ],
            ),
          ),
        ],
      );
    }).toList();
  }

  TextStyle defaultTextStyle = TextStyle(fontSize: 12);
  TextStyle defaultTextStyle2 = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.bold,
  );
}
