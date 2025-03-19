import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'sidebar_notifier.dart';

typedef OnItemClicked = void Function(int index);

class SidebarItem {
  final Widget icon;
  final Widget iconInactive;
  final OnItemClicked onClick;
  final int index;
  String title;

  SidebarItem({
    required this.icon,
    required this.iconInactive,
    required this.onClick,
    required this.index,
    this.title = "",
  });
}

class SidebarItemWidget extends ConsumerWidget {
  const SidebarItemWidget({super.key, required this.item});

  final SidebarItem item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedIndex = ref.watch(sidebarProvider);

    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        child: Tooltip(
          message: item.title,
          child: Container(
            margin: const EdgeInsets.only(top: 10, bottom: 10),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(4),
              color:
                  selectedIndex == item.index ? Colors.grey[200] : Colors.white,
            ),
            width: 30,
            height: 30,
            child: selectedIndex == item.index ? item.icon : item.iconInactive,
          ),
        ),
        onTap: () {
          item.onClick(item.index);
        },
      ),
    );
  }
}
