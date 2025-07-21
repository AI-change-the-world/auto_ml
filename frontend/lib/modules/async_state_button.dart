import 'package:auto_ml/utils/logger.dart';
import 'package:auto_ml/utils/styles.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

typedef HandleError = void Function(Object error);

class AsyncStateButton<T> extends ConsumerWidget {
  final ProviderBase<AsyncValue<T>> provider;
  final void Function(T value) onDone;
  final String label;
  final HandleError? handleError;

  const AsyncStateButton({
    super.key,
    required this.provider,
    required this.onDone,
    required this.label,
    this.handleError,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncValue = ref.watch(provider);

    return asyncValue.when(
      loading:
          () => Container(
            width: 24,
            height: 24,
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: Colors.grey.shade200,
              shape: BoxShape.circle, // 关键：使整个容器为圆形
            ),
            child: const CircularProgressIndicator(strokeWidth: 2),
          ),

      error: (error, _) {
        if (handleError != null) {
          handleError!(error);
        }
        logger.e(error);
        return Text(
          "Error",
          style: Styles.defaultButtonTextStyle.copyWith(color: Colors.red),
        );
      },
      data:
          (value) => ElevatedButton(
            onPressed: () => onDone(value),
            child: Text(label),
          ),
    );
  }
}

enum FutureButtonState { initial, loading, success, error }

class FutureStatusButton<T> extends StatefulWidget {
  final Future<T> Function() onPressedAsync;
  final void Function(T data) onDone;
  final Widget initialChild;
  final Widget? loadingChild;
  final Widget? successChild;
  final Widget? errorChild;
  final void Function(Object error)? onError;
  final FutureButtonState initialState;

  final Duration animationDuration;
  final double? width;
  final double height;

  const FutureStatusButton({
    super.key,
    required this.onPressedAsync,
    required this.onDone,
    required this.initialChild,
    this.loadingChild,
    this.successChild,
    this.errorChild,
    this.onError,
    this.animationDuration = const Duration(milliseconds: 300),
    this.width = 80,
    this.height = 30,
    this.initialState = FutureButtonState.initial,
  });

  @override
  State<FutureStatusButton<T>> createState() => _FutureStatusButtonState<T>();
}

class _FutureStatusButtonState<T> extends State<FutureStatusButton<T>> {
  late FutureButtonState _state = widget.initialState;

  void _handlePress() async {
    if (_state == FutureButtonState.loading) return;

    setState(() {
      _state = FutureButtonState.loading;
    });

    try {
      final result = await widget.onPressedAsync();
      widget.onDone(result);
      if (mounted) {
        setState(() => _state = FutureButtonState.success);
      }
    } catch (e) {
      widget.onError?.call(e);
      if (mounted) {
        setState(() {
          _state = FutureButtonState.error;
        });
      }
    }
  }

  void changeCurrentState(FutureButtonState state) {
    if (_state != state) {
      setState(() {
        _state = state;
      });
    }
  }

  Widget _buildChild() {
    logger.i("state $_state");
    switch (_state) {
      case FutureButtonState.loading:
        return Container(
          key: const ValueKey('loading'),
          width: 20,
          height: 20,
          decoration: const BoxDecoration(
            color: Colors.blue,
            shape: BoxShape.circle,
          ),
          padding: const EdgeInsets.all(5),
          child: const CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
          ),
        );

      case FutureButtonState.success:
        return ElevatedButton(
          key: const ValueKey('success'),
          onPressed: _handlePress,
          style: ElevatedButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(4), // 设置圆角半径
            ),
            padding: EdgeInsets.symmetric(horizontal: 6, vertical: 3), // 调整按钮大小
          ),
          child: widget.successChild ?? widget.initialChild,
        );

      case FutureButtonState.error:
        return ElevatedButton(
          key: const ValueKey('error'),
          onPressed: _handlePress,
          style: ElevatedButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(4), // 设置圆角半径
            ),
            padding: EdgeInsets.symmetric(horizontal: 6, vertical: 3), // 调整按钮大小
          ),
          child: widget.errorChild ?? const Text("重试"),
        );

      case FutureButtonState.initial:
        return ElevatedButton(
          key: const ValueKey('initial'),
          onPressed: _handlePress,
          style: ElevatedButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(4), // 设置圆角半径
            ),
            padding: EdgeInsets.symmetric(horizontal: 6, vertical: 3), // 调整按钮大小
          ),
          child: widget.initialChild,
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: widget.animationDuration,
      width: _state == FutureButtonState.loading ? 20 : widget.width,
      height: _state == FutureButtonState.loading ? 20 : widget.height,
      curve: Curves.easeInOut,
      child: Align(
        alignment:
            _state == FutureButtonState.loading
                ? Alignment.center
                : Alignment.centerRight,
        child: _buildChild(),
      ),
    );
  }
}

class FutureStatusButtonSimple extends StatefulWidget {
  final Widget initialChild;

  final Duration animationDuration;
  final double? width;
  final double height;
  final VoidCallback onPressed;

  const FutureStatusButtonSimple({
    super.key,
    required this.initialChild,
    this.animationDuration = const Duration(milliseconds: 300),
    this.width = 80,
    this.height = 30,
    required this.onPressed,
  });

  @override
  State<FutureStatusButtonSimple> createState() =>
      FutureStatusButtonSimpleState();
}

class FutureStatusButtonSimpleState extends State<FutureStatusButtonSimple> {
  late FutureButtonState _state = FutureButtonState.initial;

  void _handlePress() async {
    widget.onPressed();
  }

  void changeCurrentState(FutureButtonState state) {
    if (_state != state) {
      setState(() {
        _state = state;
      });
    }
  }

  Widget _buildChild() {
    logger.i("state $_state");
    switch (_state) {
      case FutureButtonState.loading:
        return Container(
          key: const ValueKey('loading'),
          width: 20,
          height: 20,
          decoration: const BoxDecoration(
            color: Colors.blue,
            shape: BoxShape.circle,
          ),
          padding: const EdgeInsets.all(5),
          child: const CircularProgressIndicator(
            strokeWidth: 2,
            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
          ),
        );

      case FutureButtonState.initial:
        return ElevatedButton(
          key: const ValueKey('initial'),
          onPressed: _handlePress,
          style: ElevatedButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(4), // 设置圆角半径
            ),
            padding: EdgeInsets.symmetric(horizontal: 6, vertical: 3), // 调整按钮大小
          ),
          child: widget.initialChild,
        );
      default:
        return ElevatedButton(
          key: const ValueKey('initial'),
          onPressed: _handlePress,
          style: ElevatedButton.styleFrom(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(4), // 设置圆角半径
            ),
            padding: EdgeInsets.symmetric(horizontal: 6, vertical: 3), // 调整按钮大小
          ),
          child: widget.initialChild,
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: widget.animationDuration,
      width: _state == FutureButtonState.loading ? 20 : widget.width,
      height: _state == FutureButtonState.loading ? 20 : widget.height,
      curve: Curves.easeInOut,
      child: Align(
        alignment:
            _state == FutureButtonState.loading
                ? Alignment.center
                : Alignment.centerRight,
        child: _buildChild(),
      ),
    );
  }
}
