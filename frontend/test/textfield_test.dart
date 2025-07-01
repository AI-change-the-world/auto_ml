import 'package:flutter/material.dart';

void main() => runApp(MyApp());

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(home: ExpandableTextAreaPage());
  }
}

class ExpandableTextAreaPage extends StatefulWidget {
  @override
  _ExpandableTextAreaPageState createState() => _ExpandableTextAreaPageState();
}

class _ExpandableTextAreaPageState extends State<ExpandableTextAreaPage> {
  TextEditingController _controller = TextEditingController();

  void _showExpandedEditor() async {
    final result = await showDialog<String>(
      context: context,
      builder: (context) {
        TextEditingController _dialogController = TextEditingController(
          text: _controller.text,
        );
        return AlertDialog(
          title: Text('详细编辑'),
          content: SizedBox(
            width: double.maxFinite,
            child: TextField(
              controller: _dialogController,
              maxLines: 15,
              decoration: InputDecoration(border: OutlineInputBorder()),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('取消'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, _dialogController.text),
              child: Text('确认'),
            ),
          ],
        );
      },
    );

    if (result != null) {
      setState(() {
        _controller.text = result;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('可展开编辑框')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Stack(
          alignment: Alignment.bottomRight,
          children: [
            TextField(
              controller: _controller,
              maxLines: 5,
              decoration: InputDecoration(
                labelText: '内容',
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.fromLTRB(12, 12, 36, 12), // 给按钮留空间
              ),
            ),
            Positioned(
              right: 8,
              bottom: 8,
              child: GestureDetector(
                onTap: _showExpandedEditor,
                child: Container(
                  padding: EdgeInsets.all(4),
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    shape: BoxShape.circle,
                  ),
                  child: Icon(Icons.open_in_full, size: 18),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
