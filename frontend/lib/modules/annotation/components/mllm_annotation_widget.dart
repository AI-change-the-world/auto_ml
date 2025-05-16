import 'package:flutter/material.dart';

class MllmAnnotationWidget extends StatefulWidget {
  const MllmAnnotationWidget({super.key});

  @override
  State<MllmAnnotationWidget> createState() => _MllmAnnotationWidgetState();
}

class _MllmAnnotationWidgetState extends State<MllmAnnotationWidget> {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(10),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(10),

        gradient: LinearGradient(
          begin: Alignment.centerLeft,
          end: Alignment.centerRight,
          stops: [0.1, 0.9, 1.0],
          colors: [Colors.grey[200]!, Colors.white, Colors.grey[200]!],
        ),
      ),
      child: Row(
        spacing: 10,
        children: [
          Expanded(
            child: Container(decoration: BoxDecoration(color: Colors.white)),
          ),
          Expanded(
            child: Column(
              spacing: 10,
              children: [
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(color: Colors.white),
                  ),
                ),
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(color: Colors.white),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
