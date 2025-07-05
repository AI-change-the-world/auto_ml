import 'package:auto_ml/modules/data_augment/components/card.dart';
import 'package:auto_ml/modules/data_augment/components/gan_dialog.dart';
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
      child: Wrap(
        spacing: 20,
        runSpacing: 20,
        children: [
          Hover3DCard(
            title: "CV Augmentation",
            description:
                "Use CV augmentation to improve the performance of your model.",
            imageUrl: "assets/cv.jpeg",
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
          ),
          Hover3DCard(
            title: "Augmentation Pipeline",
            description: "Customize your augmentation pipeline.",
            imageUrl: "assets/sd.jpeg",
          ),
        ],
      ),
    );
  }
}
