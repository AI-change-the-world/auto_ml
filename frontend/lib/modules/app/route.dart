import 'package:auto_ml/i18n/strings.g.dart';
import 'package:auto_ml/modules/aether_agent/aether_agent_screen.dart';
import 'package:auto_ml/modules/app/_simple_layout.dart';
import 'package:auto_ml/modules/dataset/dataset_screen.dart';
import 'package:auto_ml/modules/annotation/label_screen.dart';
import 'package:auto_ml/modules/deploy/deploy_screen.dart';
import 'package:auto_ml/modules/task/task_screen.dart';
import 'package:auto_ml/modules/tool_models/model_screen.dart';
import 'package:auto_ml/modules/predict/predict_screen.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

final GoRouter router = GoRouter(
  errorPageBuilder: (context, state) {
    return MaterialPage<void>(
      key: state.pageKey,
      child: Scaffold(
        body: Center(
          child: Column(
            spacing: 20,
            crossAxisAlignment: CrossAxisAlignment.center,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(t.route.nothing, style: const TextStyle(fontSize: 24)),
              ElevatedButton(
                style: Styles.getDefaultButtonStyle(width: 200),
                onPressed: () {
                  context.go("/");
                },
                child: Text(
                  t.route.back_to_main,
                  style: Styles.defaultButtonTextStyle,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  },
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
        // GoRoute(
        //   path: '/annotation',
        //   name: 'annotation',
        //   pageBuilder:
        //       (context, state) => noTransitionPage(child: AnnotationScreen()),
        // ),
        GoRoute(
          path: '/tool-models',
          name: 'tool-models',
          // builder: (context, state) => const ModelScreen(),
          pageBuilder:
              (context, state) => noTransitionPage(child: ModelScreen()),
        ),
        GoRoute(
          path: '/annotation',
          name: 'annotation',
          pageBuilder:
              (context, state) => noTransitionPage(child: LabelScreen()),
          // pageBuilder:
          //     (context, state) => noTransitionPage(
          //       child: TestLabelScreen(
          //         assetImg: "assets/test.png",
          //         assetLabel: "assets/test.txt",
          //       ),
          //     ),
        ),
        GoRoute(
          path: '/predict',
          name: 'predict',
          // builder: (context, state) => Container(),
          pageBuilder:
              (context, state) => noTransitionPage(child: PredictScreen()),
        ),
        GoRoute(
          path: '/task',
          name: 'task',
          // builder: (context, state) => Container(),
          pageBuilder:
              (context, state) => noTransitionPage(child: TaskScreen()),
        ),
        GoRoute(
          path: '/deploy',
          name: 'deploy',
          // builder: (context, state) => Container(),
          pageBuilder:
              (context, state) => noTransitionPage(child: DeployScreen()),
        ),
        GoRoute(
          path: '/aether/agent',
          name: 'aether agent',
          // builder: (context, state) => Container(),
          pageBuilder:
              (context, state) => noTransitionPage(child: AetherAgentScreen()),
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
