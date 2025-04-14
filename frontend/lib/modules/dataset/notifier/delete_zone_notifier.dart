import 'package:flutter_riverpod/flutter_riverpod.dart';

class DeleteZoneNotifier extends AutoDisposeNotifier<bool> {
  @override
  bool build() {
    return false;
  }

  void show() {
    state = true;
  }

  void hide() {
    state = false;
  }
}

final deleteZoneNotifierProvider =
    AutoDisposeNotifierProvider<DeleteZoneNotifier, bool>(
      DeleteZoneNotifier.new,
    );
