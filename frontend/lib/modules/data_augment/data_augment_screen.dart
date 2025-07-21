import 'package:auto_ml/modules/data_augment/components/card.dart';
import 'package:auto_ml/modules/data_augment/components/cv_dialog.dart';
import 'package:auto_ml/modules/data_augment/components/gan_dialog.dart';
import 'package:auto_ml/modules/data_augment/components/sd_dialog.dart';
import 'package:auto_ml/modules/dataset/components/left_right_background_container.dart'
    show BgImageType;
import 'package:flutter/material.dart';

class DataAugmentScreen extends StatefulWidget {
  const DataAugmentScreen({super.key});

  @override
  State<DataAugmentScreen> createState() => _DataAugmentScreenState();
}

class _DataAugmentScreenState extends State<DataAugmentScreen> {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(10),
      child: SingleChildScrollView(
        child: Wrap(
          spacing: 20,
          runSpacing: 20,
          children: [
            Hover3DCard(
              title: "CV Augmentation",
              description:
                  "Use CV augmentation to improve the performance of your model.",
              imageUrl: "assets/cv.jpeg",
              onTap: () {
                showGeneralDialog(
                  context: context,
                  barrierDismissible: true,
                  barrierLabel: "CvAugmentationDialog",
                  pageBuilder: (c, _, _) {
                    return Center(child: CvDialog());
                  },
                );
              },
              bgImageType: BgImageType.asset,
            ),
            Hover3DCard(
              title: "GAN Augmentation",
              description: "Train a GAN to generate new data.",
              imageUrl: "assets/gan.jpeg",
              onTap: () {
                showGeneralDialog(
                  context: context,
                  barrierDismissible: true,
                  barrierLabel: "GANAugmentationDialog",
                  pageBuilder: (c, _, _) {
                    return Center(child: GanDialog());
                  },
                );
              },
              bgImageType: BgImageType.asset,
            ),
            Hover3DCard(
              title: "Time Series Augmentation",
              description: "Data augmentation for time series.",
              imageUrl: "assets/ts.png",
              bgImageType: BgImageType.asset,
              onTap: () {},
            ),
            Hover3DCard(
              title: "Video to image extraction",
              description: "Extract high-quality frames from videos.",
              imageUrl: "assets/v2i.png",
              bgImageType: BgImageType.asset,
              onTap: () {},
            ),
            Hover3DCard(
              onTap: () {
                showGeneralDialog(
                  context: context,
                  barrierDismissible: true,
                  barrierLabel: "AugmentationDialog",
                  pageBuilder: (c, _, _) {
                    return Center(child: SdDialog());
                  },
                );
              },
              bgImageType: BgImageType.asset,
              title: "Augmentation Pipeline",
              description: "Customize your augmentation pipeline.",
              imageUrl: "assets/sd.jpeg",
            ),
          ],
        ),
      ),
    );
  }
}
