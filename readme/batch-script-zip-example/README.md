# 上传脚本包验证样例

运行同目录的打包脚本，它会生成可直接上传的 `readme/batch-script-zip-example.zip`。脚本会将
`batch_script.json`、`README.md` 和代码文件直接写入 ZIP 根目录，不会带上目录层级或 macOS 的
`__MACOSX` 元数据。

```sh
python3 readme/batch-script-zip-example/build_package.py
```

它为每张图片生成一个 YOLO 中心框，并通过 `Pillow` 读取图片尺寸。首次运行会创建虚拟环境并安装依赖；同一版本和依赖内容再次运行会复用该虚拟环境。

建议创建检测标注项目，至少配置一个类别。执行时使用默认参数即可；`class_index` 应对应标注项目中的类别顺序。
