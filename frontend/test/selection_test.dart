import 'package:auto_ml/modules/dataset/components/selection_widget.dart';
import 'package:flutter/material.dart';

void main() {
  runApp(MaterialApp(home: App()));
}

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SelectionWidget(
          items: ["1", "2", "3", "4"],
          onChanged: (p0) {
            // ignore: avoid_print
            print(p0);
          },
        ),
      ),
    );
  }
}
