import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/utils/globals.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class SidebarItem {
  final Widget icon;
  final Widget iconInactive;
  final int index;
  final String route; // ✅ 新增路由字段
  String title;

  SidebarItem({
    required this.icon,
    required this.iconInactive,
    required this.index,
    required this.route, // ✅ 新增
    this.title = "",
  });
}

class SidebarItemWidget extends StatelessWidget {
  const SidebarItemWidget({
    super.key,
    this.item,
    this.isSelected = false,
    this.onTap,
    required this.isDivider,
  }) : assert(
         item != null || isDivider,
         "item cannot be null if isDivider is false",
       );

  final SidebarItem? item;
  final bool isSelected;
  final VoidCallback? onTap;
  final bool isDivider;

  @override
  Widget build(BuildContext context) {
    if (isDivider) {
      return Container(
        margin: EdgeInsets.only(top: 10, bottom: 10),
        width: Styles.sidebarWidthExpanded,
        child: Divider(height: 1, thickness: 1, color: Colors.white),
      );
    }

    return MouseRegion(
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: onTap,
        child: Tooltip(
          message: item!.title,
          child: Container(
            margin: const EdgeInsets.symmetric(vertical: 2),
            decoration: BoxDecoration(
              // borderRadius: BorderRadius.circular(4),
              color:
                  isSelected
                      ? Colors.white.withValues(alpha: 0.75)
                      : Colors.transparent,
            ),
            width: Styles.sidebarWidthExpanded,
            height: 40,
            child: SizedBox(
              width: Styles.sidebarItemWidth,
              child: Row(
                children: [
                  SizedBox(width: 20),
                  isSelected ? item!.icon : item!.iconInactive,
                  SizedBox(width: 15),
                  Text(
                    item!.title,
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color:
                          isSelected
                              ? Styles.sidebarItemActiveColor
                              : Styles.sidebarItemInactiveColor,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class SimpleLayout extends StatelessWidget {
  const SimpleLayout({
    super.key,
    required this.child,
    required this.selectedIndex,
    required this.onIndexChanged,
    this.decoration,
    this.elevation = 10,
    this.padding = 10,
    this.backgroundColor = Colors.white,
  });

  final Widget child;
  final int selectedIndex;
  final ValueChanged<int> onIndexChanged;

  final Decoration? decoration;
  final double elevation;
  final double padding;
  final Color backgroundColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      color: backgroundColor,
      child: Row(
        children: [
          Padding(
            padding: EdgeInsets.only(top: 10, bottom: 10, left: 5, right: 5),
            child: Material(
              elevation: elevation,
              borderRadius: BorderRadius.circular(30),
              child: Container(
                width: Styles.sidebarWidthExpanded,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(30),
                  // color: Theme.of(context).primaryColorLight,
                  gradient: LinearGradient(
                    stops: [0.4, 1.0],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [
                      Theme.of(context).primaryColor,
                      Theme.of(context).primaryColorLight,
                    ],
                  ),
                ),
                child: Column(
                  children: [
                    Stack(
                      children: [
                        SizedBox(
                          height: 80,
                          width: Styles.sidebarWidthExpanded,
                          child: Center(
                            child: Image.asset(
                              "assets/transparent_logo.png",
                              width: Styles.sidebarItemWidthExpanded,
                              // height: 100,
                              fit: BoxFit.fitWidth,
                            ),
                          ),
                        ),
                        Positioned.fill(
                          // bottom: 1,
                          child: Align(
                            alignment: Alignment.bottomCenter,
                            child: Text(
                              "v${Globals.appVersion}",
                              style: TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),

                    SidebarItemWidget(isDivider: true),
                    Expanded(
                      child: SingleChildScrollView(
                        child: Column(
                          children: [
                            SidebarItemWidget(
                              isDivider: false,
                              item: items.getByName("dataset"),
                              isSelected: selectedIndex == 0,
                              onTap: () => onIndexChanged(0),
                            ),
                            SidebarItemWidget(
                              isDivider: false,
                              item: items.getByName("annotation"),
                              isSelected: selectedIndex == 1,
                              onTap: () => onIndexChanged(1),
                            ),
                            SidebarItemWidget(isDivider: true),
                            SidebarItemWidget(
                              isDivider: false,
                              item: items.getByName("tool_model"),
                              isSelected: selectedIndex == 2,
                              onTap: () => onIndexChanged(2),
                            ),
                            SidebarItemWidget(
                              isDivider: false,
                              item: items.getByName("agent"),
                              isSelected: selectedIndex == 3,
                              onTap: () => onIndexChanged(3),
                            ),
                            SidebarItemWidget(
                              isDivider: false,
                              item: items.getByName("task"),
                              isSelected: selectedIndex == 4,
                              onTap: () => onIndexChanged(4),
                            ),
                            SidebarItemWidget(isDivider: true),
                            SidebarItemWidget(
                              isDivider: false,
                              item: items.getByName("predict"),
                              isSelected: selectedIndex == 5,
                              onTap: () => onIndexChanged(5),
                            ),
                            SidebarItemWidget(isDivider: true),
                            SidebarItemWidget(
                              isDivider: false,
                              item: items.getByName("deploy"),
                              isSelected: selectedIndex == 6,
                              onTap: () => onIndexChanged(6),
                            ),
                          ],
                        ),
                      ),
                    ),

                    Container(
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(20),
                      ),
                      width: Styles.sidebarItemWidthExpanded,
                      height: 40,
                      child: Row(
                        spacing: 10,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.supervised_user_circle),
                          Text("User info"),
                        ],
                      ),
                    ),
                    SizedBox(height: 10),
                  ],
                ),
              ),
            ),
          ),
          Expanded(
            child: Padding(
              padding: EdgeInsets.all(padding),
              child: Material(
                borderRadius: BorderRadius.circular(10),
                elevation: elevation,
                child: Container(decoration: decoration, child: child),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

extension SidebarListExtension on List<SidebarItem> {
  SidebarItem? getByName(String name) {
    switch (name) {
      case "dataset":
        return firstWhere((item) => item.index == 0);
      case "annotation":
        return firstWhere((item) => item.index == 1);
      case "tool_model":
        return firstWhere((item) => item.index == 2);
      case "agent":
        return firstWhere((item) => item.index == 3);
      case "task":
        return firstWhere((item) => item.index == 4);
      case "predict":
        return firstWhere((item) => item.index == 5);
      case "deploy":
        return firstWhere((item) => item.index == 6);
      default:
        return null;
    }
  }
}

final List<SidebarItem> items = [
  SidebarItem(
    icon: const Icon(Icons.dataset, color: Styles.sidebarItemActiveColor),
    iconInactive: const Icon(
      Icons.dataset,
      color: Styles.sidebarItemInactiveColor,
    ),
    index: 0,
    title: t.sidebar.dataset,
    route: "/",
  ),
  SidebarItem(
    icon: const Icon(
      Icons.square_outlined,
      color: Styles.sidebarItemActiveColor,
    ),
    iconInactive: const Icon(
      Icons.square_outlined,
      color: Styles.sidebarItemInactiveColor,
    ),
    index: 1,
    title: t.sidebar.annotation,
    route: "/annotation",
  ),
  SidebarItem(
    icon: const Icon(Icons.list, color: Styles.sidebarItemActiveColor),
    iconInactive: const Icon(
      Icons.list,
      color: Styles.sidebarItemInactiveColor,
    ),
    index: 2,
    title: t.sidebar.tool_model,
    route: "/tool-models",
  ),
  SidebarItem(
    icon: const Icon(Icons.rocket, color: Styles.sidebarItemActiveColor),
    iconInactive: const Icon(
      Icons.rocket,
      color: Styles.sidebarItemInactiveColor,
    ),
    index: 3,
    title: t.sidebar.agent,
    route: "/aether/agent",
  ),
  SidebarItem(
    icon: const Icon(Icons.rule, color: Styles.sidebarItemActiveColor),
    iconInactive: const Icon(
      Icons.rule,
      color: Styles.sidebarItemInactiveColor,
    ),
    index: 4,
    title: t.sidebar.task,
    route: "/task",
  ),
  SidebarItem(
    icon: const Icon(Icons.text_fields, color: Styles.sidebarItemActiveColor),
    iconInactive: const Icon(
      Icons.text_fields,
      color: Styles.sidebarItemInactiveColor,
    ),
    index: 6,
    title: t.sidebar.predict,
    route: "/predict",
  ),
  SidebarItem(
    icon: const Icon(Icons.line_axis, color: Styles.sidebarItemActiveColor),
    iconInactive: const Icon(
      Icons.line_axis,
      color: Styles.sidebarItemInactiveColor,
    ),
    index: 5,
    title: t.sidebar.deploy,
    route: "/deploy",
  ),
]..sort((a, b) => a.index.compareTo(b.index));

class SimpleLayoutShell extends StatelessWidget {
  final Widget child;
  const SimpleLayoutShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    final location =
        GoRouter.of(context).routerDelegate.currentConfiguration.uri.toString();

    final currentIndex = items.indexWhere((item) => item.route == location);

    return SimpleLayout(
      selectedIndex: currentIndex < 0 ? 0 : currentIndex,
      onIndexChanged: (index) {
        final route = items[index].route;
        if (location != route) {
          context.go(route);
        }
      },
      child: child,
    );
  }
}
