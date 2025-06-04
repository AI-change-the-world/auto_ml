// ignore: deprecated_member_use, avoid_web_libraries_in_flutter
import 'dart:html' as html;
// ignore: depend_on_referenced_packages
import 'package:http/http.dart' as http;

Future<void> download(String url, {String? filename}) async {
  final response = await http.get(Uri.parse(url));
  final blob = html.Blob([response.bodyBytes]);
  final url0 = html.Url.createObjectUrlFromBlob(blob);
  final _ =
      html.AnchorElement(href: url0)
        ..setAttribute("download", filename ?? "unknow_file")
        ..click();
  html.Url.revokeObjectUrl(url);
}
