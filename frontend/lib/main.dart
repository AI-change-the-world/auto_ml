import 'package:auto_ml/modules/app/route.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:toastification/toastification.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  DioClient().init(baseUrl: 'http://localhost:8080/automl');

  runApp(
    ToastificationWrapper(
      child: ProviderScope(
        child: MaterialApp.router(
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: const Color.fromARGB(255, 61, 124, 219),
              brightness: Brightness.light,
            ),
          ),
          // showPerformanceOverlay: true,
          debugShowCheckedModeBanner: false,
          routerConfig: router,
        ),
      ),
    ),
  );
}
