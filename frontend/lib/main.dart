import 'package:auto_ml/modules/app/app.dart';
import 'package:auto_ml/modules/isar/database.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:toastification/toastification.dart';
import 'package:window_manager/window_manager.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  IsarDatabase database = IsarDatabase();
  await database.initialDatabase();

  await windowManager.ensureInitialized();
  WindowOptions windowOptions = WindowOptions(
    size: Styles.size,
    minimumSize: Styles.size,
    backgroundColor: Colors.white,
    skipTaskbar: false,
  );
  windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.show();
    await windowManager.focus();
  });

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
