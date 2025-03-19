import 'package:auto_ml/modules/dataset/components/dataset_card_wrap.dart';
import 'package:auto_ml/modules/dataset/notifier/dataset_notifier.dart';
import 'package:auto_ml/modules/isar/dataset.dart';
import 'package:dropdown_button2/dropdown_button2.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DatasetScreen extends ConsumerStatefulWidget {
  const DatasetScreen({super.key});

  @override
  ConsumerState<DatasetScreen> createState() => _DatasetScreenState();
}

class _DatasetScreenState extends ConsumerState<DatasetScreen> {
  late List<DatasetType> selectedTypes = List.of(DatasetType.values);

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(datasetNotifierProvider);

    return state.when(
      data: (data) {
        var datasets = data.datasets;
        datasets = fakeDataset();

        if (datasets.isEmpty) {
          return Center(child: Text('No datasets found.'));
        }

        Map<DatasetType, List<Dataset>> map = {
          if (data.selectedTypes.contains(DatasetType.image))
            DatasetType.image: [],
          if (data.selectedTypes.contains(DatasetType.text))
            DatasetType.text: [],
          if (data.selectedTypes.contains(DatasetType.other))
            DatasetType.other: [],
          if (data.selectedTypes.contains(DatasetType.audio))
            DatasetType.audio: [],
          if (data.selectedTypes.contains(DatasetType.video))
            DatasetType.video: [],
        };

        for (var dataset in datasets) {
          map[dataset.type]?.add(dataset);
        }

        return Padding(
          padding: EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              SizedBox(
                height: 30,
                child: Row(
                  children: [
                    Spacer(),
                    DropdownButtonHideUnderline(
                      child: DropdownButton2<DatasetType>(
                        dropdownStyleData: DropdownStyleData(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(4),
                            color: Colors.white,
                          ),
                        ),
                        isExpanded: true,
                        hint: Text(
                          'Select Items',
                          style: TextStyle(
                            fontSize: 14,
                            color: Theme.of(context).hintColor,
                          ),
                        ),
                        items:
                            DatasetType.values.map((item) {
                              return DropdownMenuItem(
                                value: item,
                                //disable default onTap to avoid closing menu when selecting an item
                                enabled: false,
                                child: StatefulBuilder(
                                  builder: (context, menuSetState) {
                                    final isSelected = selectedTypes.contains(
                                      item,
                                    );

                                    return InkWell(
                                      onTap: () {
                                        isSelected
                                            ? selectedTypes.remove(item)
                                            : selectedTypes.add(item);
                                        setState(() {});
                                        //This rebuilds the dropdownMenu Widget to update the check mark
                                        menuSetState(() {});

                                        ref
                                            .read(
                                              datasetNotifierProvider.notifier,
                                            )
                                            .updateSelectTypes(selectedTypes);
                                      },
                                      child: Container(
                                        height: double.infinity,
                                        padding: const EdgeInsets.symmetric(
                                          horizontal: 16.0,
                                        ),
                                        child: Row(
                                          children: [
                                            if (isSelected)
                                              const Icon(
                                                Icons.check_box_outlined,
                                              )
                                            else
                                              const Icon(
                                                Icons.check_box_outline_blank,
                                              ),
                                            const SizedBox(width: 16),
                                            Expanded(
                                              child: Text(
                                                item.name,
                                                style: const TextStyle(
                                                  fontSize: 14,
                                                ),
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    );
                                  },
                                ),
                              );
                            }).toList(),
                        //Use last selected item as the current value so if we've limited menu height, it scroll to last item.
                        value:
                            data.selectedTypes.isEmpty
                                ? null
                                : data.selectedTypes.last,
                        onChanged: (value) {},
                        selectedItemBuilder: (context) {
                          return DatasetType.values.map((item) {
                            return Container(
                              alignment: AlignmentDirectional.center,
                              child: Row(
                                spacing: 4,
                                children:
                                    selectedTypes
                                        .map(
                                          (e) => e.icon(
                                            color: Colors.black,
                                            size: 14,
                                          ),
                                        )
                                        .toList(),
                              ),
                            );
                          }).toList();
                        },
                        buttonStyleData: const ButtonStyleData(
                          padding: EdgeInsets.only(left: 16, right: 8),
                          height: 40,
                          width: 140,
                        ),
                        menuItemStyleData: const MenuItemStyleData(
                          height: 40,
                          padding: EdgeInsets.zero,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    spacing: 20,
                    children:
                        map.entries.map((entry) {
                          return DatasetCardWrap(
                            type: entry.key,
                            datasets: entry.value,
                          );
                        }).toList(),
                  ),
                ),
              ),
            ],
          ),
        );
      },
      error: (error, stackTrace) {
        return Center(child: Text('Error: $error'));
      },
      loading: () {
        return Center(child: CircularProgressIndicator());
      },
    );
  }
}
