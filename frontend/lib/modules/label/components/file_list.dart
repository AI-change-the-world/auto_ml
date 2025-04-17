import 'package:auto_ml/modules/label/notifiers/label_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class FileList extends ConsumerWidget {
  const FileList({
    super.key,
    required this.current,
    required this.data,
    required this.dl,
  });
  final String current;
  final List<MapEntry<String, String>> data;
  final (String, String) dl;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
                        if (data[index].key == current) {
                          return _wrapper(
                            Container(
                              decoration: BoxDecoration(
                                color: Colors.blueAccent,
                              ),
                              child: Tooltip(
                                waitDuration: Duration(milliseconds: 500),
                                message: data[index].key,
                                child: Text(
                                  data[index].key,
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
                              message: data[index].key,
                              child: Text(
                                data[index].key,
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
      child: GestureDetector(onDoubleTap: () {}, child: child),
    );
  }
}
