import 'package:auto_ml/api.dart';
import 'package:auto_ml/i18n/i18n_notifier.dart';
import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/app/route.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:auto_ml/utils/globals.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:media_kit/media_kit.dart';
import 'package:toastification/toastification.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized(); // add this
  LocaleSettings.useDeviceLocale(); // and this
  MediaKit.ensureInitialized();

  DioClient().init(baseUrl: 'http://localhost:8080/automl');
  Api.setBaseUrl('http://localhost:8080/automl');
  // local test
  // DioClient().init(baseUrl: 'http://192.168.2.10:8080/automl');
  // Api.setBaseUrl('http://192.168.2.10:8080/automl');
  await Globals.init();

  runApp(
    ToastificationWrapper(
      child: ProviderScope(
        child: Consumer(
          builder: (c, ref, _) {
            return MaterialApp.router(
              title: t.appname,
              locale: Locale(ref.watch(i18nProvider)),
              theme: ThemeData(
                fontFamily: "ph",
                colorScheme: ColorScheme.fromSeed(
                  seedColor: const Color.fromARGB(255, 128, 180, 217),
                  brightness: Brightness.light,
                ),
              ),
              // showPerformanceOverlay: true,
              debugShowCheckedModeBanner: false,
              routerConfig: router,
            );
          },
        ),
      ),
    ),
  );
}
