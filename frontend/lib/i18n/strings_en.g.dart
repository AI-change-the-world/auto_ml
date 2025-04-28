///
/// Generated file. Do not edit.
///
// coverage:ignore-file
// ignore_for_file: type=lint, unused_import

part of 'strings.g.dart';

// Path: <root>
typedef TranslationsEn = Translations; // ignore: unused_element
class Translations implements BaseTranslations<AppLocale, Translations> {
	/// Returns the current translations of the given [context].
	///
	/// Usage:
	/// final t = Translations.of(context);
	static Translations of(BuildContext context) => InheritedLocaleData.of<AppLocale, Translations>(context).translations;

	/// You can call this constructor and build your own translation instance of this locale.
	/// Constructing via the enum [AppLocale.build] is preferred.
	Translations({Map<String, Node>? overrides, PluralResolver? cardinalResolver, PluralResolver? ordinalResolver, TranslationMetadata<AppLocale, Translations>? meta})
		: assert(overrides == null, 'Set "translation_overrides: true" in order to enable this feature.'),
		  $meta = meta ?? TranslationMetadata(
		    locale: AppLocale.en,
		    overrides: overrides ?? {},
		    cardinalResolver: cardinalResolver,
		    ordinalResolver: ordinalResolver,
		  ) {
		$meta.setFlatMapFunction(_flatMapFunction);
	}

	/// Metadata for the translations of <en>.
	@override final TranslationMetadata<AppLocale, Translations> $meta;

	/// Access flat map
	dynamic operator[](String key) => $meta.getTranslation(key);

	late final Translations _root = this; // ignore: unused_field

	Translations $copyWith({TranslationMetadata<AppLocale, Translations>? meta}) => Translations(meta: meta ?? this.$meta);

	// Translations
	late final TranslationsLabelScreenEn label_screen = TranslationsLabelScreenEn._(_root);
	late final TranslationsDatasetScreenEn dataset_screen = TranslationsDatasetScreenEn._(_root);
	late final TranslationsSidebarEn sidebar = TranslationsSidebarEn._(_root);
	late final TranslationsRouteEn route = TranslationsRouteEn._(_root);
	late final TranslationsAnnotationScreenEn annotation_screen = TranslationsAnnotationScreenEn._(_root);
	late final TranslationsDialogsEn dialogs = TranslationsDialogsEn._(_root);
	late final TranslationsPredictScreenEn predict_screen = TranslationsPredictScreenEn._(_root);
}

// Path: label_screen
class TranslationsLabelScreenEn {
	TranslationsLabelScreenEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get not_selected => 'Dataset or label is not selected';
	String get select => 'Select';
}

// Path: dataset_screen
class TranslationsDatasetScreenEn {
	TranslationsDatasetScreenEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get confirm => 'Confirm';
	late final TranslationsDatasetScreenFilesEn files = TranslationsDatasetScreenFilesEn._(_root);
}

// Path: sidebar
class TranslationsSidebarEn {
	TranslationsSidebarEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get dataset => 'Dataset';
	String get label => 'Label';
	String get annotation => 'Annotation';
	String get tool_model => 'Tool Model';
	String get predict => 'Predict';
}

// Path: route
class TranslationsRouteEn {
	TranslationsRouteEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get back_to_main => 'Back to Main';
	String get nothing => 'Woops! There is nothing here.';
}

// Path: annotation_screen
class TranslationsAnnotationScreenEn {
	TranslationsAnnotationScreenEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	late final TranslationsAnnotationScreenListWidgetEn list_widget = TranslationsAnnotationScreenListWidgetEn._(_root);
	late final TranslationsAnnotationScreenListEn list = TranslationsAnnotationScreenListEn._(_root);
	late final TranslationsAnnotationScreenImageBoardEn image_board = TranslationsAnnotationScreenImageBoardEn._(_root);
}

// Path: dialogs
class TranslationsDialogsEn {
	TranslationsDialogsEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	late final TranslationsDialogsModifyDatasetEn modify_dataset = TranslationsDialogsModifyDatasetEn._(_root);
	late final TranslationsDialogsNewDatasetEn new_dataset = TranslationsDialogsNewDatasetEn._(_root);
	late final TranslationsDialogsNewModelEn new_model = TranslationsDialogsNewModelEn._(_root);
}

// Path: predict_screen
class TranslationsPredictScreenEn {
	TranslationsPredictScreenEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get upload => 'Upload';
}

// Path: dataset_screen.files
class TranslationsDatasetScreenFilesEn {
	TranslationsDatasetScreenFilesEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	late final TranslationsDatasetScreenFilesFileDetailsEn file_details = TranslationsDatasetScreenFilesFileDetailsEn._(_root);
}

// Path: annotation_screen.list_widget
class TranslationsAnnotationScreenListWidgetEn {
	TranslationsAnnotationScreenListWidgetEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get empty => 'annotations is empty';
	String get no_data => 'No Data';
}

// Path: annotation_screen.list
class TranslationsAnnotationScreenListEn {
	TranslationsAnnotationScreenListEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get file_list => 'File List';
	String get empty => 'Dateset is empty';
	String get prev => 'Prev';
	String get next => 'Next';
}

// Path: annotation_screen.image_board
class TranslationsAnnotationScreenImageBoardEn {
	TranslationsAnnotationScreenImageBoardEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get empty => 'No image';
}

// Path: dialogs.modify_dataset
class TranslationsDialogsModifyDatasetEn {
	TranslationsDialogsModifyDatasetEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get basic => 'Basic Info';
	String get dataset_name => 'Dataset Name*';
	String get dataset_type => 'Dataset Type';
	String get dataset_location => 'Dataset Location*';
	String get path => 'Dataset Path*';
	String get additional => 'Additional Information';
	String get rank => 'Ranking';
	String get description => 'Description';
	String get description_hint => 'Dataset Description';
}

// Path: dialogs.new_dataset
class TranslationsDialogsNewDatasetEn {
	TranslationsDialogsNewDatasetEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get basic => 'Basic Info';
	String get dataset_name => 'Dataset Name*';
	String get dataset_type => 'Dataset Type';
	String get dataset_location => 'Dataset Location*';
	String get path => 'Dataset Path*';
	String get additional => 'Additional Information';
	String get rank => 'Ranking';
	String get description => 'Description';
	String get description_hint => 'Dataset Description';
}

// Path: dialogs.new_model
class TranslationsDialogsNewModelEn {
	TranslationsDialogsNewModelEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get name => 'Name*';
	String get model_type => 'Model Type';
	String get model_name => 'Model Name';
	String get description => 'Description';
}

// Path: dataset_screen.files.file_details
class TranslationsDatasetScreenFilesFileDetailsEn {
	TranslationsDatasetScreenFilesFileDetailsEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get empty => 'No dataset selected';
}

/// Flat map(s) containing all translations.
/// Only for edge cases! For simple maps, use the map function of this library.
extension on Translations {
	dynamic _flatMapFunction(String path) {
		switch (path) {
			case 'label_screen.not_selected': return 'Dataset or label is not selected';
			case 'label_screen.select': return 'Select';
			case 'dataset_screen.confirm': return 'Confirm';
			case 'dataset_screen.files.file_details.empty': return 'No dataset selected';
			case 'sidebar.dataset': return 'Dataset';
			case 'sidebar.label': return 'Label';
			case 'sidebar.annotation': return 'Annotation';
			case 'sidebar.tool_model': return 'Tool Model';
			case 'sidebar.predict': return 'Predict';
			case 'route.back_to_main': return 'Back to Main';
			case 'route.nothing': return 'Woops! There is nothing here.';
			case 'annotation_screen.list_widget.empty': return 'annotations is empty';
			case 'annotation_screen.list_widget.no_data': return 'No Data';
			case 'annotation_screen.list.file_list': return 'File List';
			case 'annotation_screen.list.empty': return 'Dateset is empty';
			case 'annotation_screen.list.prev': return 'Prev';
			case 'annotation_screen.list.next': return 'Next';
			case 'annotation_screen.image_board.empty': return 'No image';
			case 'dialogs.modify_dataset.basic': return 'Basic Info';
			case 'dialogs.modify_dataset.dataset_name': return 'Dataset Name*';
			case 'dialogs.modify_dataset.dataset_type': return 'Dataset Type';
			case 'dialogs.modify_dataset.dataset_location': return 'Dataset Location*';
			case 'dialogs.modify_dataset.path': return 'Dataset Path*';
			case 'dialogs.modify_dataset.additional': return 'Additional Information';
			case 'dialogs.modify_dataset.rank': return 'Ranking';
			case 'dialogs.modify_dataset.description': return 'Description';
			case 'dialogs.modify_dataset.description_hint': return 'Dataset Description';
			case 'dialogs.new_dataset.basic': return 'Basic Info';
			case 'dialogs.new_dataset.dataset_name': return 'Dataset Name*';
			case 'dialogs.new_dataset.dataset_type': return 'Dataset Type';
			case 'dialogs.new_dataset.dataset_location': return 'Dataset Location*';
			case 'dialogs.new_dataset.path': return 'Dataset Path*';
			case 'dialogs.new_dataset.additional': return 'Additional Information';
			case 'dialogs.new_dataset.rank': return 'Ranking';
			case 'dialogs.new_dataset.description': return 'Description';
			case 'dialogs.new_dataset.description_hint': return 'Dataset Description';
			case 'dialogs.new_model.name': return 'Name*';
			case 'dialogs.new_model.model_type': return 'Model Type';
			case 'dialogs.new_model.model_name': return 'Model Name';
			case 'dialogs.new_model.description': return 'Description';
			case 'predict_screen.upload': return 'Upload';
			default: return null;
		}
	}
}

