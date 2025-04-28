import 'package:auto_ml/i18n/strings.g.dart';
import 'package:flutter/material.dart';

class PredictScreen extends StatefulWidget {
  const PredictScreen({super.key});

  @override
  State<PredictScreen> createState() => _PredictScreenState();
}

class _PredictScreenState extends State<PredictScreen> {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(10),
      child: Column(
        children: [
          SizedBox(
            height: 30,
            child: Row(
              children: [
                Spacer(),
                ElevatedButton(
                  style: ButtonStyle(
                    fixedSize: WidgetStateProperty.all(Size(200, 20)),
                    backgroundColor: WidgetStatePropertyAll(Colors.grey[300]),
                    padding: WidgetStatePropertyAll(
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    ),
                    textStyle: WidgetStatePropertyAll(
                      const TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                    shape: WidgetStatePropertyAll(
                      RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(4.0),
                      ),
                    ),
                  ),
                  onPressed: () {},
                  child: Text(t.predict_screen.upload),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
