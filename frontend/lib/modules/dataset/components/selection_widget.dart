import 'package:flutter/material.dart';

class SelectionWidget extends StatefulWidget {
  SelectionWidget({super.key, required this.items, required this.onChanged}) {
    assert(items.length > 1);
  }
  final List<String> items;
  final Function(String) onChanged;

  @override
  State<SelectionWidget> createState() => _SelectionWidgetState();
}

class _SelectionWidgetState extends State<SelectionWidget> {
  late ValueNotifier<String> notifier = ValueNotifier(widget.items.first);

  @override
  Widget build(BuildContext context) {
    return ValueListenableBuilder<String>(
      valueListenable: notifier,
      builder: (c, s, _) {
        return Material(
          color: Colors.white,
          elevation: 2,
          borderRadius: BorderRadius.circular(4),
          child: Container(
            height: 30,
            padding: EdgeInsets.all(3),
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(4)),
            child: Row(
              spacing: 2,
              children:
                  widget.items
                      .map(
                        (v) => Expanded(
                          child: InkWell(
                            onTap: () {
                              notifier.value = v;
                              widget.onChanged(v);
                            },
                            child: Container(
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(
                                  v == s ? 4 : 0,
                                ),
                                color:
                                    v == s
                                        ? Colors.lightBlueAccent
                                        : Colors.transparent,
                              ),
                              child: Center(
                                child: Text(
                                  v,
                                  style: TextStyle(
                                    color: v == s ? Colors.white : Colors.black,
                                    fontSize: 12,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      )
                      .toList(),
            ),
          ),
        );
      },
    );
  }
}
