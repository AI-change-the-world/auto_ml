import 'package:file_selector/file_selector.dart';
import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';

class Globals {
  Globals._();

  static String appVersion = '';

  static GlobalKey globalImageBoardKey = GlobalKey();

  static const XTypeGroup imageType = XTypeGroup(
    label: 'images',
    extensions: <String>['jpg', 'png', 'jpeg'],
  );

  static Future init() async {
    final packageInfo = await PackageInfo.fromPlatform();

    String version = packageInfo.version; // 例如：1.0.0
    String buildNumber = packageInfo.buildNumber; // 例如：1

    if (buildNumber.isEmpty) {
      appVersion = version; // 如果没有 buildNumber，则只使用 version
    } else {
      appVersion = '$version+$buildNumber'; // 格式化为 1.0.0+1
    }
  }
}
