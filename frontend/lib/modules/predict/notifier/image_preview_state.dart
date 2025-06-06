import 'package:auto_ml/modules/predict/models/image_preview_model.dart';
import 'package:flutter/material.dart';

class ImagePreviewState {
  final List<ImagePreviewModel> images;
  final int current;
  final int fileId;
  final double imageWidth;
  final double imageHeight;
  final double duration;
  final bool loading;
  final bool isSidebarOpen;
  final Rect? selected;

  ImagePreviewState({
    this.images = const [],
    this.current = -1,
    this.fileId = -1,
    this.imageWidth = 0,
    this.imageHeight = 0,
    this.duration = 0,
    this.loading = false,
    this.isSidebarOpen = false,
    this.selected,
  });

  ImagePreviewState copyWith({
    List<ImagePreviewModel>? images,
    int? current,
    int? fileId,
    double? imageWidth,
    double? imageHeight,
    double? duration,
    bool? loading,
    bool? isSidebarOpen,
    Rect? selected,
  }) {
    return ImagePreviewState(
      images: images ?? this.images,
      current: current ?? this.current,
      fileId: fileId ?? this.fileId,
      imageWidth: imageWidth ?? this.imageWidth,
      imageHeight: imageHeight ?? this.imageHeight,
      duration: duration ?? this.duration,
      loading: loading ?? this.loading,
      isSidebarOpen: isSidebarOpen ?? this.isSidebarOpen,
      selected: selected,
    );
  }
}
