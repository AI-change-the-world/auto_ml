import 'package:auto_ml/modules/dataset/components/dataset_card.dart';
import 'package:auto_ml/modules/isar/dataset.dart';
import 'package:flutter/material.dart';

class DatasetCardWrap extends StatelessWidget {
  const DatasetCardWrap({
    super.key,
    required this.type,
    required this.datasets,
  });
  final DatasetType type;
  final List<Dataset> datasets;

  @override
  Widget build(BuildContext context) {
    return Column(
      spacing: 5,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          height: 30,
          width: double.infinity,
          child: Row(
            spacing: 8,
            children: [
              Text("${type.name} (${datasets.length})"),
              Material(
                borderRadius: BorderRadius.circular(20),
                child: MouseRegion(
                  cursor: SystemMouseCursors.click,
                  child: GestureDetector(
                    onTap: () async {},
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.green,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      padding: EdgeInsets.all(1),
                      child: Icon(Icons.add, color: Colors.white, size: 18),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
        Padding(
          padding: EdgeInsets.only(left: 10, right: 10),
          child: Wrap(
            spacing: 10,
            runSpacing: 10,
            children: datasets.map((e) => DatasetCard(dataset: e)).toList(),
          ),
        ),
      ],
    );
  }
}
