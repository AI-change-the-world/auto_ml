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
    return Padding(
      padding: EdgeInsets.only(left: 10, right: 10),
      child: Wrap(
        spacing: 10,
        runSpacing: 10,
        children: datasets.map((e) => DatasetCard(dataset: e)).toList(),
      ),
    );
  }
}
