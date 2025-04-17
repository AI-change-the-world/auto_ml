import 'package:auto_ml/modules/current_dataset_annotation_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class FileList extends ConsumerWidget {
  const FileList({super.key, required this.data});
  final List<(String, String)> data;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final current = ref.watch(
      currentDatasetAnnotationNotifierProvider.select((v) => v.currentFilePath),
    );

    return Container(
      margin: EdgeInsets.only(top: 10, bottom: 10),
      width: 200,
      height: double.infinity,
      padding: EdgeInsets.all(5),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(4),
        color: Colors.grey[100],
      ),
      child: Column(
        spacing: 10,
        children: [
          Text("File List", style: TextStyle(fontWeight: FontWeight.bold)),
          Expanded(
            child:
                data.isEmpty
                    ? Center(child: Text("Dateset is empty"))
                    : ListView.builder(
                      itemBuilder: (context, index) {
                        if (data[index].$1 == current) {
                          return _wrapper(
                            Container(
                              decoration: BoxDecoration(
                                color: Colors.blueAccent,
                              ),
                              child: Tooltip(
                                waitDuration: Duration(milliseconds: 500),
                                message: data[index].$1,
                                child: Text(
                                  data[index].$1,
                                  style: TextStyle(color: Colors.white),
                                  maxLines: 1,
                                  softWrap: true,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                            ),
                            ref,
                            index,
                          );
                        }
                        return _wrapper(
                          Container(
                            decoration: BoxDecoration(
                              color: Colors.transparent,
                            ),
                            child: Tooltip(
                              waitDuration: Duration(milliseconds: 500),
                              message: data[index].$1,
                              child: Text(
                                data[index].$1,
                                style: TextStyle(color: Colors.black),
                                maxLines: 1,
                                softWrap: true,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ),
                          ref,
                          index,
                        );
                      },
                      itemCount: data.length,
                    ),
          ),
          SizedBox(
            height: 30,
            child: Row(
              spacing: 10,
              children: [
                Spacer(),
                TextButton(onPressed: () {}, child: Text("Prev")),
                TextButton(
                  onPressed: () {
                    /// TODO: next data
                    // ref.read(labelNotifierProvider(dl).notifier).nextData();
                  },
                  child: Text("Next"),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _wrapper(Widget child, WidgetRef ref, int index) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: () {
          // print("a");
          ref
              .read(currentDatasetAnnotationNotifierProvider.notifier)
              .changeCurrentData(data[index]);
        },
        child: child,
      ),
    );
  }
}
