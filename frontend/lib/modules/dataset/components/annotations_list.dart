import 'package:auto_ml/modules/dataset/constants.dart';
import 'package:auto_ml/modules/dataset/entity/annotation_list_response.dart';
import 'package:auto_ml/modules/dataset/notifier/annotation_notifier.dart';
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
  Widget build(BuildContext context) {
    final state = ref.watch(annotationListProvider);

    return Material(
      borderRadius: BorderRadius.only(
        topLeft: Radius.circular(10),
        bottomLeft: Radius.circular(10),
      ),
      elevation: 10,
      child: Container(
        width: MediaQuery.of(context).size.width * 0.8,
        height: double.infinity,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(10),
            bottomLeft: Radius.circular(10),
          ),
        ),
        child: state.when(
          data: (data) {
            return Padding(
              padding: EdgeInsets.all(10),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.start,
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: 10,
                children: [
                  Text(
                    "Id: ${data.current?.id}  ${data.current?.name}",
                    style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                  ),
                  Expanded(
                    child: DataTable2(
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
        ),
      ),
    );
  }

  late List<DataColumn> columns = [
    DataColumn2(label: Text('Id', style: defaultTextStyle2), fixedWidth: 40),
    DataColumn2(
      label: Text('File count', style: defaultTextStyle2),
      fixedWidth: 80,
    ),
    DataColumn(label: Text('Type', style: defaultTextStyle2)),
    DataColumn(label: Text('Created at', style: defaultTextStyle2)),
    DataColumn(label: Text('Updated at', style: defaultTextStyle2)),
    DataColumn(label: Text('Operations', style: defaultTextStyle2)),
  ];

  List<DataRow> getRows(List<Annotation> annotations) {
    return annotations.map((annotation) {
      return DataRow(
        cells: [
          DataCell(Text(annotation.id.toString(), style: defaultTextStyle)),
          DataCell(
            Text(
              annotation.annotatedFileCount.toString(),
              style: defaultTextStyle,
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
              children: [
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
