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
	@override String get refresh => '刷新';
	@override late final _TranslationsTableZhCn table = _TranslationsTableZhCn._(_root);
	@override late final _TranslationsDatasetScreenZhCn dataset_screen = _TranslationsDatasetScreenZhCn._(_root);
	@override late final _TranslationsRouteZhCn route = _TranslationsRouteZhCn._(_root);
	@override late final _TranslationsSidebarZhCn sidebar = _TranslationsSidebarZhCn._(_root);
	@override late final _TranslationsAnnotationScreenZhCn annotation_screen = _TranslationsAnnotationScreenZhCn._(_root);
	@override late final _TranslationsDialogsZhCn dialogs = _TranslationsDialogsZhCn._(_root);
	@override late final _TranslationsPredictScreenZhCn predict_screen = _TranslationsPredictScreenZhCn._(_root);
	@override late final _TranslationsAgentScreenZhCn agent_screen = _TranslationsAgentScreenZhCn._(_root);
	@override late final _TranslationsTaskScreenZhCn task_screen = _TranslationsTaskScreenZhCn._(_root);
	@override late final _TranslationsDeployScreenZhCn deploy_screen = _TranslationsDeployScreenZhCn._(_root);
	@override late final _TranslationsGlobalZhCn global = _TranslationsGlobalZhCn._(_root);
}

// Path: label_screen
class _TranslationsLabelScreenZhCn implements TranslationsLabelScreenEn {
	_TranslationsLabelScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get not_selected => '数据集或标注未选择';
	@override String get select => '选择...';
}

// Path: table
class _TranslationsTableZhCn implements TranslationsTableEn {
	_TranslationsTableZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get createat => '创建时间';
	@override String get updateat => '更新时间';
	@override String get operation => '操作';
}

// Path: dataset_screen
class _TranslationsDatasetScreenZhCn implements TranslationsDatasetScreenEn {
	_TranslationsDatasetScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get dataset_no_selected => '请先选择数据集';
	@override String get confirm => '确认';
	@override late final _TranslationsDatasetScreenFilesZhCn files = _TranslationsDatasetScreenFilesZhCn._(_root);
	@override late final _TranslationsDatasetScreenTableZhCn table = _TranslationsDatasetScreenTableZhCn._(_root);
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
	@override String get agent => 'Aether智能体';
	@override String get task => '任务';
	@override String get deploy => '部署';
}

// Path: annotation_screen
class _TranslationsAnnotationScreenZhCn implements TranslationsAnnotationScreenEn {
	_TranslationsAnnotationScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override late final _TranslationsAnnotationScreenListWidgetZhCn list_widget = _TranslationsAnnotationScreenListWidgetZhCn._(_root);
	@override late final _TranslationsAnnotationScreenListZhCn list = _TranslationsAnnotationScreenListZhCn._(_root);
	@override late final _TranslationsAnnotationScreenImageBoardZhCn image_board = _TranslationsAnnotationScreenImageBoardZhCn._(_root);
	@override String get select_dataset => '选择数据集';
	@override String get select_annotation => '选择标注集';
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
	@override String get id => '编号';
	@override String get name => '文件名';
	@override String get type => '文件类型';
	@override String get uploaded => '上传于';
}

// Path: agent_screen
class _TranslationsAgentScreenZhCn implements TranslationsAgentScreenEn {
	_TranslationsAgentScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get id => '编号';
	@override String get name => '名称';
	@override String get description => '描述';
	@override String get module => '关联模块';
	@override String get recommend => '是否推荐';
}

// Path: task_screen
class _TranslationsTaskScreenZhCn implements TranslationsTaskScreenEn {
	_TranslationsTaskScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get id => '编号';
	@override String get type => '任务类型';
	@override String get dataset_id => '数据集编号';
	@override String get annotation_id => '标注集编号';
	@override String get status => '状态';
}

// Path: deploy_screen
class _TranslationsDeployScreenZhCn implements TranslationsDeployScreenEn {
	_TranslationsDeployScreenZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get id => '编号';
	@override String get model_path => '模型存储路径';
	@override String get base_model => '基础模型';
	@override String get dataset_id => '数据集编号';
	@override String get annotation_id => '标注集编号';
	@override String get Epoch => '训练轮数';
	@override String get Loss => '损失';
	@override String get status => '状态';
}

// Path: global
class _TranslationsGlobalZhCn implements TranslationsGlobalEn {
	_TranslationsGlobalZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override late final _TranslationsGlobalErrorsZhCn errors = _TranslationsGlobalErrorsZhCn._(_root);
	@override late final _TranslationsGlobalSuccessZhCn success = _TranslationsGlobalSuccessZhCn._(_root);
}

// Path: dataset_screen.files
class _TranslationsDatasetScreenFilesZhCn implements TranslationsDatasetScreenFilesEn {
	_TranslationsDatasetScreenFilesZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override late final _TranslationsDatasetScreenFilesFileDetailsZhCn file_details = _TranslationsDatasetScreenFilesFileDetailsZhCn._(_root);
}

// Path: dataset_screen.table
class _TranslationsDatasetScreenTableZhCn implements TranslationsDatasetScreenTableEn {
	_TranslationsDatasetScreenTableZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get id => '数据集编号';
	@override String get name => '数据集名称';
	@override String get details => '数据集详情';
	@override String get annotations => '标注集';
	@override String get count => '数据集数量';
	@override String get status => '状态';
	@override String get preview => '预览';
	@override late final _TranslationsDatasetScreenTableAnnotationZhCn annotation = _TranslationsDatasetScreenTableAnnotationZhCn._(_root);
	@override String get no_preview => '无预览文件';
	@override String get upload_annotation => '上传标注文件';
	@override String get support_error => '暂时支持分类和目标检测';
	@override String get train_support_error => '暂时支持分类和目标检测的自动标注';
	@override String get auto_annotate => '自动标注';
	@override String get train => '训练';
	@override String get prompt_unset => '**Prompt未设置**';
	@override String get prompt => '查看Prompt';
	@override String get classes => '查看类别';
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
	@override String get annotation_list => '标注列表';
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

// Path: global.errors
class _TranslationsGlobalErrorsZhCn implements TranslationsGlobalErrorsEn {
	_TranslationsGlobalErrorsZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get name_cannot_be_empty => '名称不可为空';
	@override String get basic_error => '异常';
	@override String get create_error => '创建失败';
	@override String get modify_error => '修改失败';
}

// Path: global.success
class _TranslationsGlobalSuccessZhCn implements TranslationsGlobalSuccessEn {
	_TranslationsGlobalSuccessZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get create_success => '创建成功';
	@override String get modify_success => '修改成功';
}

// Path: dataset_screen.files.file_details
class _TranslationsDatasetScreenFilesFileDetailsZhCn implements TranslationsDatasetScreenFilesFileDetailsEn {
	_TranslationsDatasetScreenFilesFileDetailsZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get empty => '未选择数据集';
}

// Path: dataset_screen.table.annotation
class _TranslationsDatasetScreenTableAnnotationZhCn implements TranslationsDatasetScreenTableAnnotationEn {
	_TranslationsDatasetScreenTableAnnotationZhCn._(this._root);

	final TranslationsZhCn _root; // ignore: unused_field

	// Translations
	@override String get id => '编号';
	@override String get path => '标注集路径';
	@override String get type => '标注类型';
}

/// Flat map(s) containing all translations.
/// Only for edge cases! For simple maps, use the map function of this library.
extension on TranslationsZhCn {
	dynamic _flatMapFunction(String path) {
		switch (path) {
			case 'label_screen.not_selected': return '数据集或标注未选择';
			case 'label_screen.select': return '选择...';
			case 'refresh': return '刷新';
			case 'table.createat': return '创建时间';
			case 'table.updateat': return '更新时间';
			case 'table.operation': return '操作';
			case 'dataset_screen.dataset_no_selected': return '请先选择数据集';
			case 'dataset_screen.confirm': return '确认';
			case 'dataset_screen.files.file_details.empty': return '未选择数据集';
			case 'dataset_screen.table.id': return '数据集编号';
			case 'dataset_screen.table.name': return '数据集名称';
			case 'dataset_screen.table.details': return '数据集详情';
			case 'dataset_screen.table.annotations': return '标注集';
			case 'dataset_screen.table.count': return '数据集数量';
			case 'dataset_screen.table.status': return '状态';
			case 'dataset_screen.table.preview': return '预览';
			case 'dataset_screen.table.annotation.id': return '编号';
			case 'dataset_screen.table.annotation.path': return '标注集路径';
			case 'dataset_screen.table.annotation.type': return '标注类型';
			case 'dataset_screen.table.no_preview': return '无预览文件';
			case 'dataset_screen.table.upload_annotation': return '上传标注文件';
			case 'dataset_screen.table.support_error': return '暂时支持分类和目标检测';
			case 'dataset_screen.table.train_support_error': return '暂时支持分类和目标检测的自动标注';
			case 'dataset_screen.table.auto_annotate': return '自动标注';
			case 'dataset_screen.table.train': return '训练';
			case 'dataset_screen.table.prompt_unset': return '**Prompt未设置**';
			case 'dataset_screen.table.prompt': return '查看Prompt';
			case 'dataset_screen.table.classes': return '查看类别';
			case 'route.back_to_main': return '返回首页';
			case 'route.nothing': return '这里空无一物';
			case 'sidebar.dataset': return '数据集';
			case 'sidebar.label': return '标注';
			case 'sidebar.annotation': return '标注';
			case 'sidebar.tool_model': return '工具';
			case 'sidebar.predict': return '测试';
			case 'sidebar.agent': return 'Aether智能体';
			case 'sidebar.task': return '任务';
			case 'sidebar.deploy': return '部署';
			case 'annotation_screen.list_widget.empty': return '标注信息为空';
			case 'annotation_screen.list_widget.no_data': return '无数据';
			case 'annotation_screen.list.file_list': return '文件列表';
			case 'annotation_screen.list.empty': return '数据集为空';
			case 'annotation_screen.list.prev': return '前一个';
			case 'annotation_screen.list.next': return '后一个';
			case 'annotation_screen.list.annotation_list': return '标注列表';
			case 'annotation_screen.image_board.empty': return '无数据';
			case 'annotation_screen.select_dataset': return '选择数据集';
			case 'annotation_screen.select_annotation': return '选择标注集';
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
			case 'predict_screen.id': return '编号';
			case 'predict_screen.name': return '文件名';
			case 'predict_screen.type': return '文件类型';
			case 'predict_screen.uploaded': return '上传于';
			case 'agent_screen.id': return '编号';
			case 'agent_screen.name': return '名称';
			case 'agent_screen.description': return '描述';
			case 'agent_screen.module': return '关联模块';
			case 'agent_screen.recommend': return '是否推荐';
			case 'task_screen.id': return '编号';
			case 'task_screen.type': return '任务类型';
			case 'task_screen.dataset_id': return '数据集编号';
			case 'task_screen.annotation_id': return '标注集编号';
			case 'task_screen.status': return '状态';
			case 'deploy_screen.id': return '编号';
			case 'deploy_screen.model_path': return '模型存储路径';
			case 'deploy_screen.base_model': return '基础模型';
			case 'deploy_screen.dataset_id': return '数据集编号';
			case 'deploy_screen.annotation_id': return '标注集编号';
			case 'deploy_screen.Epoch': return '训练轮数';
			case 'deploy_screen.Loss': return '损失';
			case 'deploy_screen.status': return '状态';
			case 'global.errors.name_cannot_be_empty': return '名称不可为空';
			case 'global.errors.basic_error': return '异常';
			case 'global.errors.create_error': return '创建失败';
			case 'global.errors.modify_error': return '修改失败';
			case 'global.success.create_success': return '创建成功';
			case 'global.success.modify_success': return '修改成功';
			default: return null;
		}
	}
}

