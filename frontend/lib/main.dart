import 'package:auto_ml/modules/app/app.dart';
import 'package:auto_ml/utils/dio_instance.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:toastification/toastification.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  DioClient().init(baseUrl: 'http://localhost:8080');

  runApp(
    ToastificationWrapper(
      child: ProviderScope(
        child: MaterialApp(
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: const Color(0xFF0D6EFD),
              brightness: Brightness.light,
            ),
          ),
          // showPerformanceOverlay: true,
          debugShowCheckedModeBanner: false,
          home: App(),
        ),
      ),
    ),
  );
}
