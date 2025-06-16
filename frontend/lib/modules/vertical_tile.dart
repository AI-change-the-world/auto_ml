import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';

class VerticalTile extends StatelessWidget {
  const VerticalTile({
    super.key,
    required this.icon,
    required this.text,
    required this.subText,
    this.button,
    this.height = 300,
    this.width = 100,
    this.onTap,
  }) : assert((button != null && onTap != null) || button == null);
  final double height;
  final double width;
  final String icon;
  final String text;
  final String subText;
  final String? button;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 4,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        padding: EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(10),
        ),
        width: width,
        height: height,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            Image.asset(icon, width: 80, height: 80, fit: BoxFit.fill),
            Text(
              text,
              style: TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
            ),
            Text(
              subText,
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.normal),
            ),
            button == null
                ? SizedBox(height: 30, width: 100)
                : ElevatedButton(
                  style: Styles.getDefaultButtonStyle(
                    width: 100,
                    radius: 20,
                    height: 30,
                  ),
                  onPressed: () {
                    onTap!();
                  },
                  child: Text(button!),
                ),
          ],
        ),
      ),
    );
  }
}
