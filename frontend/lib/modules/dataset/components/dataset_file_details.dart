import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/dataset/components/simple_tile.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_file_list_notifier.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DatasetFileDetails extends ConsumerWidget {
  const DatasetFileDetails({super.key});

  String getStatus(int status) {
    switch (status) {
      case 0:
        return "Scanning";
      case 1:
        return "Scan complete";
      case 2:
        return "Scan failed";
      default:
        return "Others";
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dataset = ref.read(datasetNotifierProvider).value?.current;

    if (dataset == null) {
      return Center(child: Text(t.dataset_screen.files.file_details.empty));
    }

    final state = ref.watch(datasetFileListNotifierProvider);

    return state.when(
      data: (data) {
        return SingleChildScrollView(
          padding: EdgeInsetsGeometry.all(10),
          child: Column(
            spacing: 20,
            children: [
              SizedBox(
                height: 80,
                child: Row(
                  spacing: 20,
                  children: [
                    SimpleTile(
                      text: "File Count",
                      icon: Container(
                        width: 50, // 任意你想要的直径
                        height: 50,
                        decoration: BoxDecoration(
                          color: const Color.fromARGB(255, 196, 213, 242),
                          shape: BoxShape.circle, // 关键：设置为圆形
                        ),
                        child: Icon(Icons.library_books, color: Colors.blue),
                      ),
                      subText: "${dataset.fileCount}",
                    ),
                    SimpleTile(
                      text: "Annotations count",
                      icon: Container(
                        width: 50, // 任意你想要的直径
                        height: 50,
                        decoration: BoxDecoration(
                          color: const Color.fromARGB(255, 196, 242, 225),
                          shape: BoxShape.circle, // 关键：设置为圆形
                        ),
                        child: Icon(Icons.label_outline, color: Colors.green),
                      ),
                      subText: "${dataset.annotationCount}",
                    ),
                    SimpleTile(
                      text: "Used count",
                      icon: Container(
                        width: 50, // 任意你想要的直径
                        height: 50,
                        decoration: BoxDecoration(
                          color: const Color.fromARGB(255, 236, 242, 196),
                          shape: BoxShape.circle, // 关键：设置为圆形
                        ),
                        child: Icon(Icons.toll_outlined, color: Colors.yellow),
                      ),
                      subText: "${data.usedCount}",
                    ),
                  ],
                ),
              ),
              Material(
                borderRadius: BorderRadius.circular(20),
                elevation: 4,
                child: Container(
                  padding: EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  width: double.infinity,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      SizedBox(
                        height: 40,
                        child: Text(
                          "Data preview",
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      Wrap(
                        spacing: 10, // 横向间距
                        runSpacing: 10, // 纵向间距
                        alignment: WrapAlignment.spaceEvenly,
                        children:
                            data.samples.map((e) {
                              return SizedBox(
                                width:
                                    (MediaQuery.of(context).size.width * 0.8 -
                                        100) /
                                    3, // 每行3个，减去间距
                                height: 200,
                                child: Image.network(e, fit: BoxFit.cover),
                              );
                            }).toList(),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
      loading: () {
        return Center(child: CircularProgressIndicator());
      },
      error: (error, stackTrace) {
        return Center(child: Text(error.toString()));
      },
    );
  }
}
