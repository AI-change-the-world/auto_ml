import 'package:flutter/material.dart';

enum BgImageType { asset, network }

class LeftRightBackgroundContainer extends StatelessWidget {
  final List<Widget> children;
  final double height;
  final double width;
  final Color leftBackgroundColor;
  final String? rightBackgroundImage;
  final BgImageType bgImageType;

  const LeftRightBackgroundContainer({
    super.key,
    this.children = const [],
    this.height = 200,
    this.width = 100,
    this.leftBackgroundColor = Colors.white,
    this.rightBackgroundImage,
    this.bgImageType = BgImageType.network,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: 4,
      borderRadius: BorderRadius.circular(30),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(30),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.transparent,
            borderRadius: BorderRadius.circular(30),
          ),
          height: height,
          width: width,
          child: Stack(
            children: [
              // 整个背景层
              Row(
                children: [
                  // 左侧白色背景
                  Expanded(flex: 1, child: Container(color: Colors.white)),

                  Expanded(
                    flex: 1,
                    child: Stack(
                      children: [
                        Positioned.fill(
                          child: Align(
                            alignment: Alignment.centerLeft,
                            child: FractionallySizedBox(
                              widthFactor: 2, // 显示左半边
                              alignment: Alignment.centerLeft,
                              child: ClipRect(
                                // child: Image.asset(imagePath, fit: BoxFit.cover),
                                child:
                                    rightBackgroundImage == null
                                        ? Image.asset(
                                          'assets/bg.jpeg',
                                          height: height,
                                          width: 0.5 * width,
                                          fit: BoxFit.fill,
                                        )
                                        : bgImageType == BgImageType.network
                                        ? Image.network(
                                          rightBackgroundImage!,
                                          height: height,
                                          width: 0.5 * width,
                                          fit: BoxFit.fill,
                                        )
                                        : Image.asset(
                                          rightBackgroundImage!,
                                          height: height,
                                          width: 0.5 * width,
                                          fit: BoxFit.fill,
                                        ),
                              ),
                            ),
                          ),
                        ),
                        Positioned.fill(
                          child: Container(
                            decoration: BoxDecoration(
                              gradient: LinearGradient(
                                stops: [.2, 1],
                                begin: Alignment.centerLeft,
                                end: Alignment.centerRight,
                                colors: [
                                  Colors.white.withValues(alpha: 0.5),
                                  Colors.transparent,
                                ],
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              // 可加前景内容
              ...children,
            ],
          ),
        ),
      ),
    );
  }
}
