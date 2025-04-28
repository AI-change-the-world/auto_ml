import 'package:flutter_riverpod/flutter_riverpod.dart';

class I18nNotifier extends Notifier<String> {
  final supported = ["zh-CN", "en"];

  @override
  String build() {
    return supported.first;
  }

  void changeLanguage(String language) {
    if (!supported.contains(language)) {
      return;
    }
    state = language;
  }
}

final i18nProvider = NotifierProvider<I18nNotifier, String>(I18nNotifier.new);
