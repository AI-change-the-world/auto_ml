import 'package:isar/isar.dart';

part 'dataset.g.dart';

enum DatasetType { image, video, audio, text, other }

@collection
class Dataset {
  Id id = Isar.autoIncrement;

  @Index(unique: true)
  String? name;

  String? description;

  String? dataPath;

  @enumerated
  DatasetType type = DatasetType.image;

  String? labelPath;

  int createAt = DateTime.now().millisecondsSinceEpoch;
}
