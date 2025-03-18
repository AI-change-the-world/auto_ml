import 'package:auto_ml/components/isar/dataset.dart';
import 'package:isar/isar.dart';

part 'dataset_file.g.dart';

@collection
class DatasetFile {
  Id id = Isar.autoIncrement;

  String? name;

  String? path;

  String? label;

  final dataset = IsarLink<Dataset>();

  int createAt = DateTime.now().millisecondsSinceEpoch;
}
