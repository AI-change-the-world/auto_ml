import 'package:auto_ml/utils/dio_instance.dart';
import 'package:path_provider/path_provider.dart';

void download(String url, {String? filename}) async {
  String saveFolder = (await getApplicationDocumentsDirectory()).path;
  String fn = filename ?? "unknown_file";
  String savePath = "$saveFolder/$fn";

  await DioClient().instance.download(url, savePath);
}
