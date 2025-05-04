///
/// Generated file. Do not edit.
///
// coverage:ignore-file
// ignore_for_file: type=lint, unused_import

import 'package:flutter/widgets.dart';
import 'package:intl/intl.dart';
import 'package:slang/generated.dart';
import 'strings.g.dart';

// Path: <root>
class TranslationsZhCn implements Translations {
	/// You can call this constructor and build your own translation instance of this locale.
	/// Constructing via the enum [AppLocale.build] is preferred.
	TranslationsZhCn({Map<String, Node>? overrides, PluralResolver? cardinalResolver, PluralResolver? ordinalResolver, TranslationMetadata<AppLocale, Translations>? meta})
		: assert(overrides == null, 'Set "translation_overrides: true" in order to enable this feature.'),
		  $meta = meta ?? TranslationMetadata(
		    locale: AppLocale.zhCn,
		    overrides: overrides ?? {},
		    cardinalResolver: cardinalResolver,
		    ordinalResolver: ordinalResolver,
		  ) {
		$meta.setFlatMapFunction(_flatMapFunction);
	}

	/// Metadata for the translations of <zh-CN>.
	@override final TranslationMetadata<AppLocale, Translations> $meta;

	/// Access flat map
	@override dynamic operator[](String key) => $meta.getTranslation(key);

	late final TranslationsZhCn _root = this; // ignore: unused_field

	@override 
	TranslationsZhCn $copyWith({TranslationMetadata<AppLocale, Translations>? meta}) => TranslationsZhCn(meta: meta ?? this.$meta);

	// Translations
	@override late final _TranslationsLabelScreenZhCn label_screen = _TranslationsLabelScreenZhCn._(_root);
	@override late final _TranslationsDatasetScreenZhCn dataset_screen = _TranslationsDatasetScreenZhCn._(_root);
	@override late final _TranslationsRouteZhCn route = _TranslationsRouteZhCn._(_root);
	@override late final _TranslationsSidebarZhCn sidebar = _TranslationsSidebarZhCn._(_root);
	@override late final _TranslationsAnnotationScreenZhCn annotation_screen = _TranslationsAnnotationScreenZhCn._(_root);
	@override late final _TranslationsDialogsZhCn dialogs = _TranslationsDialogsZhCn._(_root);
	@override late final _TranslationsPredictScreenZhCn predict_screen = _TranslationsPredictScreenZhCn._(_root);
}

// Path: label_screen
class _TranslationsLabelScreenZhCn implements TranslationsLabelScreenEn {
	_TranslationsLabelScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get not_selected => '数据集或标注未选择';
	@override String get select => '选择...';
}

// Path: dataset_screen
class _TranslationsDatasetScreenZhCn implements TranslationsDatasetScreenEn {
	_TranslationsDatasetScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get confirm => '确认';
	@override late final _TranslationsDatasetScreenFilesZhCn files = _TranslationsDatasetScreenFilesZhCn._(_root);
}

// Path: route
class _TranslationsRouteZhCn implements TranslationsRouteEn {
	_TranslationsRouteZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get back_to_main => '返回首页';
	@override String get nothing => '这里空无一物';
}

// Path: sidebar
class _TranslationsSidebarZhCn implements TranslationsSidebarEn {
	_TranslationsSidebarZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get dataset => '数据集';
	@override String get label => '标注';
	@override String get annotation => '标注';
	@override String get tool_model => '工具';
	@override String get predict => '测试';
}

// Path: annotation_screen
class _TranslationsAnnotationScreenZhCn implements TranslationsAnnotationScreenEn {
	_TranslationsAnnotationScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override late final _TranslationsAnnotationScreenListWidgetZhCn list_widget = _TranslationsAnnotationScreenListWidgetZhCn._(_root);
	@override late final _TranslationsAnnotationScreenListZhCn list = _TranslationsAnnotationScreenListZhCn._(_root);
	@override late final _TranslationsAnnotationScreenImageBoardZhCn image_board = _TranslationsAnnotationScreenImageBoardZhCn._(_root);
}

// Path: dialogs
class _TranslationsDialogsZhCn implements TranslationsDialogsEn {
	_TranslationsDialogsZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override late final _TranslationsDialogsModifyDatasetZhCn modify_dataset = _TranslationsDialogsModifyDatasetZhCn._(_root);
	@override late final _TranslationsDialogsNewDatasetZhCn new_dataset = _TranslationsDialogsNewDatasetZhCn._(_root);
	@override late final _TranslationsDialogsNewModelZhCn new_model = _TranslationsDialogsNewModelZhCn._(_root);
}

// Path: predict_screen
class _TranslationsPredictScreenZhCn implements TranslationsPredictScreenEn {
	_TranslationsPredictScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get upload => '上传';
}

// Path: dataset_screen.files
class _TranslationsDatasetScreenFilesZhCn implements TranslationsDatasetScreenFilesEn {
	_TranslationsDatasetScreenFilesZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override late final _TranslationsDatasetScreenFilesFileDetailsZhCn file_details = _TranslationsDatasetScreenFilesFileDetailsZhCn._(_root);
}

// Path: annotation_screen.list_widget
class _TranslationsAnnotationScreenListWidgetZhCn implements TranslationsAnnotationScreenListWidgetEn {
	_TranslationsAnnotationScreenListWidgetZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get empty => '标注信息为空';
	@override String get no_data => '无数据';
}

// Path: annotation_screen.list
class _TranslationsAnnotationScreenListZhCn implements TranslationsAnnotationScreenListEn {
	_TranslationsAnnotationScreenListZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get file_list => '文件列表';
	@override String get empty => '数据集为空';
	@override String get prev => '前一个';
	@override String get next => '后一个';
}

// Path: annotation_screen.image_board
class _TranslationsAnnotationScreenImageBoardZhCn implements TranslationsAnnotationScreenImageBoardEn {
	_TranslationsAnnotationScreenImageBoardZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get empty => '无数据';
}

// Path: dialogs.modify_dataset
class _TranslationsDialogsModifyDatasetZhCn implements TranslationsDialogsModifyDatasetEn {
	_TranslationsDialogsModifyDatasetZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get basic => '基础信息';
	@override String get dataset_name => '数据集名称*';
	@override String get dataset_type => '数据集类型';
	@override String get dataset_location => '原始数据存储地址*';
	@override String get path => '路径*';
	@override String get additional => '额外信息';
	@override String get rank => '评级';
	@override String get description => '简介';
	@override String get description_hint => '数据集简介';
}

// Path: dialogs.new_dataset
class _TranslationsDialogsNewDatasetZhCn implements TranslationsDialogsNewDatasetEn {
	_TranslationsDialogsNewDatasetZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get basic => '基础信息';
	@override String get dataset_name => '数据集名称*';
	@override String get dataset_type => '数据集类型';
	@override String get dataset_location => '原始数据存储地址*';
	@override String get path => '路径*';
	@override String get additional => '额外信息';
	@override String get rank => '评级';
	@override String get description => '简介';
	@override String get description_hint => '数据集简介';
}

// Path: dialogs.new_model
class _TranslationsDialogsNewModelZhCn implements TranslationsDialogsNewModelEn {
	_TranslationsDialogsNewModelZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get name => '名称*';
	@override String get model_type => '模型类型';
	@override String get model_name => '模型名称';
	@override String get description => '简介';
}

// Path: dataset_screen.files.file_details
class _TranslationsDatasetScreenFilesFileDetailsZhCn implements TranslationsDatasetScreenFilesFileDetailsEn {
	_TranslationsDatasetScreenFilesFileDetailsZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get empty => '未选择数据集';
}

/// Flat map(s) containing all translations.
/// Only for edge cases! For simple maps, use the map function of this library.
extension on TranslationsZhCn {
	dynamic _flatMapFunction(String path) {
		switch (path) {
			case 'label_screen.not_selected': return '数据集或标注未选择';
			case 'label_screen.select': return '选择...';
			case 'dataset_screen.confirm': return '确认';
			case 'dataset_screen.files.file_details.empty': return '未选择数据集';
			case 'route.back_to_main': return '返回首页';
			case 'route.nothing': return '这里空无一物';
			case 'sidebar.dataset': return '数据集';
			case 'sidebar.label': return '标注';
			case 'sidebar.annotation': return '标注';
			case 'sidebar.tool_model': return '工具';
			case 'sidebar.predict': return '测试';
			case 'annotation_screen.list_widget.empty': return '标注信息为空';
			case 'annotation_screen.list_widget.no_data': return '无数据';
			case 'annotation_screen.list.file_list': return '文件列表';
			case 'annotation_screen.list.empty': return '数据集为空';
			case 'annotation_screen.list.prev': return '前一个';
			case 'annotation_screen.list.next': return '后一个';
			case 'annotation_screen.image_board.empty': return '无数据';
			case 'dialogs.modify_dataset.basic': return '基础信息';
			case 'dialogs.modify_dataset.dataset_name': return '数据集名称*';
			case 'dialogs.modify_dataset.dataset_type': return '数据集类型';
			case 'dialogs.modify_dataset.dataset_location': return '原始数据存储地址*';
			case 'dialogs.modify_dataset.path': return '路径*';
			case 'dialogs.modify_dataset.additional': return '额外信息';
			case 'dialogs.modify_dataset.rank': return '评级';
			case 'dialogs.modify_dataset.description': return '简介';
			case 'dialogs.modify_dataset.description_hint': return '数据集简介';
			case 'dialogs.new_dataset.basic': return '基础信息';
			case 'dialogs.new_dataset.dataset_name': return '数据集名称*';
			case 'dialogs.new_dataset.dataset_type': return '数据集类型';
			case 'dialogs.new_dataset.dataset_location': return '原始数据存储地址*';
			case 'dialogs.new_dataset.path': return '路径*';
			case 'dialogs.new_dataset.additional': return '额外信息';
			case 'dialogs.new_dataset.rank': return '评级';
			case 'dialogs.new_dataset.description': return '简介';
			case 'dialogs.new_dataset.description_hint': return '数据集简介';
			case 'dialogs.new_model.name': return '名称*';
			case 'dialogs.new_model.model_type': return '模型类型';
			case 'dialogs.new_model.model_name': return '模型名称';
			case 'dialogs.new_model.description': return '简介';
			case 'predict_screen.upload': return '上传';
			default: return null;
		}
	}
}

