import 'package:auto_ml/modules/annotation/annotation_screen.dart';
import 'package:auto_ml/modules/app/_simple_layout.dart';
import 'package:auto_ml/modules/dataset/dataset_screen.dart';
import 'package:auto_ml/modules/label/label_screen.dart';
import 'package:auto_ml/modules/label/label_screen_test.dart';
import 'package:auto_ml/modules/models/model_screen.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

final GoRouter router = GoRouter(
  initialLocation: '/',
  routes: [
    ShellRoute(
      builder: (context, state, child) => SimpleLayoutShell(child: child),
      routes: [
        GoRoute(
          path: '/',
          name: 'datasets',
          pageBuilder:
              (context, state) => noTransitionPage(child: DatasetScreen()),
        ),
        GoRoute(
          path: '/annotation',
          name: 'annotation',
          pageBuilder:
              (context, state) => noTransitionPage(child: AnnotationScreen()),
        ),
        GoRoute(
          path: '/tool-models',
          name: 'tool-models',
          // builder: (context, state) => const ModelScreen(),
          pageBuilder:
              (context, state) => noTransitionPage(child: ModelScreen()),
        ),
        GoRoute(
          path: '/label',
          name: 'label',
          // pageBuilder:
          //     (context, state) => noTransitionPage(child: LabelScreen()),
          pageBuilder:
              (context, state) => noTransitionPage(
                child: TestLabelScreen(
                  assetImg: "assets/test.png",
                  assetLabel: "assets/test.txt",
                ),
              ),
        ),
        GoRoute(
          path: '/test',
          name: 'test',
          // builder: (context, state) => Container(),
          pageBuilder: (context, state) => noTransitionPage(child: Container()),
        ),
      ],
    ),
  ],
);

CustomTransitionPage<void> noTransitionPage({required Widget child}) {
  return CustomTransitionPage<void>(
    child: child,
    transitionDuration: Duration.zero,
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      return child; // 直接返回 child，没有任何动画
    },
  );
}
