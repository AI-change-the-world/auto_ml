import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

void main() {
  runApp(MyApp());
}

final _router = GoRouter(
  initialLocation: '/',
  routes: [
    ShellRoute(
      builder: (context, state, child) => MainShell(child: child),
      routes: [
        GoRoute(
          path: '/',
          name: 'home',
          builder: (context, state) => const HomeContent(),
        ),
        GoRoute(
          path: '/settings',
          name: 'settings',
          builder: (context, state) => const SettingsContent(),
        ),
      ],
    ),
  ],
);

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'NavigationRail + ShellRoute Demo',
      routerConfig: _router,
    );
  }
}

class MainShell extends StatelessWidget {
  final Widget child;
  const MainShell({super.key, required this.child});

  static final List<_NavItem> _items = [
    _NavItem('Home', Icons.home, '/'),
    _NavItem('Settings', Icons.settings, '/settings'),
  ];

  @override
  Widget build(BuildContext context) {
    final String location =
        GoRouter.of(context).routerDelegate.currentConfiguration.uri.toString();
    final int selectedIndex = _items.indexWhere(
      (item) => location == item.route,
    );

    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: selectedIndex,
            onDestinationSelected: (index) {
              final route = _items[index].route;
              if (route != location) {
                context.go(route);
              }
            },
            labelType: NavigationRailLabelType.all,
            destinations:
                _items
                    .map(
                      (item) => NavigationRailDestination(
                        icon: Icon(item.icon),
                        label: Text(item.label),
                      ),
                    )
                    .toList(),
          ),
          const VerticalDivider(thickness: 1, width: 1),
          Expanded(child: child), // <-- 中间区域才根据路由变化
        ],
      ),
    );
  }
}

class _NavItem {
  final String label;
  final IconData icon;
  final String route;
  const _NavItem(this.label, this.icon, this.route);
}

class HomeContent extends StatelessWidget {
  const HomeContent({super.key});
  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('This is the Home page'));
  }
}

class SettingsContent extends StatelessWidget {
  const SettingsContent({super.key});
  @override
  Widget build(BuildContext context) {
    return const Center(child: Text('This is the Settings page'));
  }
}
