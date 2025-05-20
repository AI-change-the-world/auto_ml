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
	String get refresh => 'Refresh';
	late final TranslationsTableEn table = TranslationsTableEn._(_root);
	late final TranslationsDatasetScreenEn dataset_screen = TranslationsDatasetScreenEn._(_root);
	late final TranslationsSidebarEn sidebar = TranslationsSidebarEn._(_root);
	late final TranslationsRouteEn route = TranslationsRouteEn._(_root);
	late final TranslationsAnnotationScreenEn annotation_screen = TranslationsAnnotationScreenEn._(_root);
	late final TranslationsDialogsEn dialogs = TranslationsDialogsEn._(_root);
	late final TranslationsPredictScreenEn predict_screen = TranslationsPredictScreenEn._(_root);
	late final TranslationsAgentScreenEn agent_screen = TranslationsAgentScreenEn._(_root);
	late final TranslationsTaskScreenEn task_screen = TranslationsTaskScreenEn._(_root);
	late final TranslationsDeployScreenEn deploy_screen = TranslationsDeployScreenEn._(_root);
	late final TranslationsGlobalEn global = TranslationsGlobalEn._(_root);
}

// Path: label_screen
class TranslationsLabelScreenEn {
	TranslationsLabelScreenEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get not_selected => 'Dataset or label is not selected';
	String get select => 'Select';
}

// Path: table
class TranslationsTableEn {
	TranslationsTableEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get createat => 'Created At';
	String get updateat => 'Updated At';
	String get operation => 'Operation';
}

// Path: dataset_screen
class TranslationsDatasetScreenEn {
	TranslationsDatasetScreenEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get dataset_no_selected => 'No dataset selected';
	String get confirm => 'Confirm';
	late final TranslationsDatasetScreenFilesEn files = TranslationsDatasetScreenFilesEn._(_root);
	late final TranslationsDatasetScreenTableEn table = TranslationsDatasetScreenTableEn._(_root);
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
	String get agent => 'Aether Agent';
	String get task => 'task';
	String get deploy => 'Deploy';
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
	String get select_dataset => 'Select Dataset';
	String get select_annotation => 'Select Annotation';
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
	String get id => 'Id';
	String get name => 'File Name';
	String get type => 'File Type';
	String get uploaded => 'Uploaded';
}

// Path: agent_screen
class TranslationsAgentScreenEn {
	TranslationsAgentScreenEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get id => 'Id';
	String get name => 'Name';
	String get description => 'Description';
	String get module => 'Module';
	String get recommend => 'Recommend';
}

// Path: task_screen
class TranslationsTaskScreenEn {
	TranslationsTaskScreenEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get id => 'Id';
	String get type => 'Type';
	String get dataset_id => 'Dataset Id';
	String get annotation_id => 'Annotation Id';
	String get status => 'Status';
}

// Path: deploy_screen
class TranslationsDeployScreenEn {
	TranslationsDeployScreenEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get id => 'Id';
	String get model_path => 'Model Path';
	String get base_model => 'Base Model';
	String get dataset_id => 'Dataset Id';
	String get annotation_id => 'Annotation Id';
	String get Epoch => 'Epoch';
	String get Loss => 'Loss';
	String get status => 'Status';
}

// Path: global
class TranslationsGlobalEn {
	TranslationsGlobalEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	late final TranslationsGlobalErrorsEn errors = TranslationsGlobalErrorsEn._(_root);
	late final TranslationsGlobalSuccessEn success = TranslationsGlobalSuccessEn._(_root);
}

// Path: dataset_screen.files
class TranslationsDatasetScreenFilesEn {
	TranslationsDatasetScreenFilesEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	late final TranslationsDatasetScreenFilesFileDetailsEn file_details = TranslationsDatasetScreenFilesFileDetailsEn._(_root);
}

// Path: dataset_screen.table
class TranslationsDatasetScreenTableEn {
	TranslationsDatasetScreenTableEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get id => 'Dataset Id';
	String get name => 'Dataset Name';
	String get details => 'Details';
	String get annotations => 'Annotations';
	String get count => 'Count';
	String get status => 'Status';
	String get preview => 'Preview';
	late final TranslationsDatasetScreenTableAnnotationEn annotation = TranslationsDatasetScreenTableAnnotationEn._(_root);
	String get no_preview => 'No preview image found';
	String get upload_annotation => 'Upload annotation files';
	String get support_error => 'Only support detection and annotation right now';
	String get train_support_error => 'Only classification and detection trainning supported right now';
	String get auto_annotate => 'Auto Annotate';
	String get train => 'Train';
	String get prompt_unset => '**Prompt unset**';
	String get prompt => 'Prompt';
	String get classes => 'Classes';
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
	String get annotation_list => 'Annotation List';
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
	String get dataset_location => 'Original Dataset Location*';
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
	String get dataset_location => 'Original Dataset Location*';
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

// Path: global.errors
class TranslationsGlobalErrorsEn {
	TranslationsGlobalErrorsEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get name_cannot_be_empty => 'Name cannot be empty';
	String get basic_error => 'Error';
	String get create_error => 'Create Error';
	String get modify_error => 'Modify Error';
}

// Path: global.success
class TranslationsGlobalSuccessEn {
	TranslationsGlobalSuccessEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get create_success => 'Create Success';
	String get modify_success => 'Modify Success';
}

// Path: dataset_screen.files.file_details
class TranslationsDatasetScreenFilesFileDetailsEn {
	TranslationsDatasetScreenFilesFileDetailsEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get empty => 'No dataset selected';
}

// Path: dataset_screen.table.annotation
class TranslationsDatasetScreenTableAnnotationEn {
	TranslationsDatasetScreenTableAnnotationEn._(this._root);

	final Translations _root; // ignore: unused_field

	// Translations
	String get id => 'Id';
	String get path => 'Annotation Path';
	String get type => 'Type';
}

/// Flat map(s) containing all translations.
/// Only for edge cases! For simple maps, use the map function of this library.
extension on Translations {
	dynamic _flatMapFunction(String path) {
		switch (path) {
			case 'label_screen.not_selected': return 'Dataset or label is not selected';
			case 'label_screen.select': return 'Select';
			case 'refresh': return 'Refresh';
			case 'table.createat': return 'Created At';
			case 'table.updateat': return 'Updated At';
			case 'table.operation': return 'Operation';
			case 'dataset_screen.dataset_no_selected': return 'No dataset selected';
			case 'dataset_screen.confirm': return 'Confirm';
			case 'dataset_screen.files.file_details.empty': return 'No dataset selected';
			case 'dataset_screen.table.id': return 'Dataset Id';
			case 'dataset_screen.table.name': return 'Dataset Name';
			case 'dataset_screen.table.details': return 'Details';
			case 'dataset_screen.table.annotations': return 'Annotations';
			case 'dataset_screen.table.count': return 'Count';
			case 'dataset_screen.table.status': return 'Status';
			case 'dataset_screen.table.preview': return 'Preview';
			case 'dataset_screen.table.annotation.id': return 'Id';
			case 'dataset_screen.table.annotation.path': return 'Annotation Path';
			case 'dataset_screen.table.annotation.type': return 'Type';
			case 'dataset_screen.table.no_preview': return 'No preview image found';
			case 'dataset_screen.table.upload_annotation': return 'Upload annotation files';
			case 'dataset_screen.table.support_error': return 'Only support detection and annotation right now';
			case 'dataset_screen.table.train_support_error': return 'Only classification and detection trainning supported right now';
			case 'dataset_screen.table.auto_annotate': return 'Auto Annotate';
			case 'dataset_screen.table.train': return 'Train';
			case 'dataset_screen.table.prompt_unset': return '**Prompt unset**';
			case 'dataset_screen.table.prompt': return 'Prompt';
			case 'dataset_screen.table.classes': return 'Classes';
			case 'sidebar.dataset': return 'Dataset';
			case 'sidebar.label': return 'Label';
			case 'sidebar.annotation': return 'Annotation';
			case 'sidebar.tool_model': return 'Tool Model';
			case 'sidebar.predict': return 'Predict';
			case 'sidebar.agent': return 'Aether Agent';
			case 'sidebar.task': return 'task';
			case 'sidebar.deploy': return 'Deploy';
			case 'route.back_to_main': return 'Back to Main';
			case 'route.nothing': return 'Woops! There is nothing here.';
			case 'annotation_screen.list_widget.empty': return 'annotations is empty';
			case 'annotation_screen.list_widget.no_data': return 'No Data';
			case 'annotation_screen.list.file_list': return 'File List';
			case 'annotation_screen.list.empty': return 'Dateset is empty';
			case 'annotation_screen.list.prev': return 'Prev';
			case 'annotation_screen.list.next': return 'Next';
			case 'annotation_screen.list.annotation_list': return 'Annotation List';
			case 'annotation_screen.image_board.empty': return 'No image';
			case 'annotation_screen.select_dataset': return 'Select Dataset';
			case 'annotation_screen.select_annotation': return 'Select Annotation';
			case 'dialogs.modify_dataset.basic': return 'Basic Info';
			case 'dialogs.modify_dataset.dataset_name': return 'Dataset Name*';
			case 'dialogs.modify_dataset.dataset_type': return 'Dataset Type';
			case 'dialogs.modify_dataset.dataset_location': return 'Original Dataset Location*';
			case 'dialogs.modify_dataset.path': return 'Dataset Path*';
			case 'dialogs.modify_dataset.additional': return 'Additional Information';
			case 'dialogs.modify_dataset.rank': return 'Ranking';
			case 'dialogs.modify_dataset.description': return 'Description';
			case 'dialogs.modify_dataset.description_hint': return 'Dataset Description';
			case 'dialogs.new_dataset.basic': return 'Basic Info';
			case 'dialogs.new_dataset.dataset_name': return 'Dataset Name*';
			case 'dialogs.new_dataset.dataset_type': return 'Dataset Type';
			case 'dialogs.new_dataset.dataset_location': return 'Original Dataset Location*';
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
			case 'predict_screen.id': return 'Id';
			case 'predict_screen.name': return 'File Name';
			case 'predict_screen.type': return 'File Type';
			case 'predict_screen.uploaded': return 'Uploaded';
			case 'agent_screen.id': return 'Id';
			case 'agent_screen.name': return 'Name';
			case 'agent_screen.description': return 'Description';
			case 'agent_screen.module': return 'Module';
			case 'agent_screen.recommend': return 'Recommend';
			case 'task_screen.id': return 'Id';
			case 'task_screen.type': return 'Type';
			case 'task_screen.dataset_id': return 'Dataset Id';
			case 'task_screen.annotation_id': return 'Annotation Id';
			case 'task_screen.status': return 'Status';
			case 'deploy_screen.id': return 'Id';
			case 'deploy_screen.model_path': return 'Model Path';
			case 'deploy_screen.base_model': return 'Base Model';
			case 'deploy_screen.dataset_id': return 'Dataset Id';
			case 'deploy_screen.annotation_id': return 'Annotation Id';
			case 'deploy_screen.Epoch': return 'Epoch';
			case 'deploy_screen.Loss': return 'Loss';
			case 'deploy_screen.status': return 'Status';
			case 'global.errors.name_cannot_be_empty': return 'Name cannot be empty';
			case 'global.errors.basic_error': return 'Error';
			case 'global.errors.create_error': return 'Create Error';
			case 'global.errors.modify_error': return 'Modify Error';
			case 'global.success.create_success': return 'Create Success';
			case 'global.success.modify_success': return 'Modify Success';
			default: return null;
		}
	}
}

