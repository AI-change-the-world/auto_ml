import 'package:xml/xml.dart';

String formatXml(String rawXml) {
  try {
    final document = XmlDocument.parse(rawXml);
    return document.toXmlString(pretty: true, indent: '  ');
  } catch (e) {
    // 如果解析失败，返回原始内容
    return rawXml;
  }
}
