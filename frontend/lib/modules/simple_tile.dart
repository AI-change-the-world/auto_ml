import 'package:flutter/material.dart';

class SimpleTile extends StatelessWidget {
  const SimpleTile({
    super.key,
    required this.text,
    required this.icon,
    required this.subText,
    this.width = 180,
    this.height = 80,
  });
  final String text;
  final Widget icon;
  final String subText;
  final double width;
  final double height;

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
        child: Row(
          spacing: 10,
          children: [
            Expanded(flex: 2, child: icon),
            Expanded(
              flex: 3,
              child: Column(
                spacing: 4,
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    text,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey,
                    ),
                  ),
                  Text(
                    subText,
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
