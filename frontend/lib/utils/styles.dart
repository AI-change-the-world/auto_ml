import 'package:flutter/material.dart';

class Styles {
  Styles._();

  static double datatableIconSize = 20;
  static double menuBarIconSize = 15;

  static double structureWidth = 200;
  static double toolbarMinSize = 110;

  static Color textButtonColor = Colors.blue;

  static Color barriarColor = Colors.black.withValues(alpha: 0.1);

  static TextStyle defaultButtonTextStyle = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.bold,
  );

  static TextStyle defaultButtonTextStyleGrey = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.bold,
    color: Colors.grey[500],
  );

  static TextStyle defaultButtonTextStyleNormal = TextStyle(fontSize: 12);

  static TextStyle titleStyle = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.bold,
  );

  static TextStyle hintStyle = TextStyle(fontSize: 12, color: Colors.grey);

  static ThemeData lightTheme = ThemeData(
    brightness: Brightness.light,
    primaryColor: Colors.blue,
    scaffoldBackgroundColor: Colors.white,
    appBarTheme: AppBarTheme(
      color: Colors.blue,
      iconTheme: IconThemeData(color: Colors.white),
    ),
    textTheme: TextTheme(
      headlineLarge: TextStyle(
        fontSize: 32.0,
        fontWeight: FontWeight.bold,
        color: Colors.black,
      ),
      bodyLarge: TextStyle(fontSize: 16.0, color: Colors.black87),
    ),
    buttonTheme: ButtonThemeData(
      buttonColor: Colors.blue,
      textTheme: ButtonTextTheme.primary,
    ),
  );

  static const List<Color> cardColors = [
    Color(0xFF42A5F5), // 亮蓝色
    Color(0xFF66BB6A), // 绿色
    Color(0xFFFFCA28), // 黄色
    Color(0xFFEF5350), // 红色
    Color(0xFF78909C), // 灰蓝色
  ];

  static ButtonStyle getDefaultButtonStyle({
    double width = 100,
    double height = 20,
  }) {
    return ButtonStyle(
      fixedSize: WidgetStateProperty.all(Size(width, height)),
      backgroundColor: WidgetStatePropertyAll(Colors.grey[100]),
      padding: WidgetStatePropertyAll(
        const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
      textStyle: WidgetStatePropertyAll(
        const TextStyle(color: Colors.white, fontWeight: FontWeight.w400),
      ),
      shape: WidgetStatePropertyAll(
        RoundedRectangleBorder(borderRadius: BorderRadius.circular(4.0)),
      ),
    );
  }
}
