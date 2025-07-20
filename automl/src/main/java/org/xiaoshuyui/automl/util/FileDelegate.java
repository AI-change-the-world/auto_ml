package org.xiaoshuyui.automl.util;

import org.jetbrains.annotations.Nullable;

import java.io.InputStream;
import java.util.List;
import java.util.Map;

public interface FileDelegate {

    default String getFile(String path, @Nullable String bucket) throws Exception {
        return null;
    }

    default String getFile(String path) throws Exception {
        return null;
    }

    default InputStream getFileStream(String path) throws Exception {
        return null;
    }

    ;

    default InputStream getFileStream(String path, @Nullable String bucket) throws Exception {
        return null;
    }

    default void writeFileStream(String path, InputStream inputStream, @Nullable String bucket) throws Exception {

    }

    ;

    default void putFile(String path, InputStream inputStream) throws Exception {
    }

    /*
     * 批量上传文件
     * files: 文件列表
     * bucket: 存储桶
     * basePath: 文件夹路径
     * return: 文件列表
     */
    default List<String> putFileList(List<String> files, String bucket, String basePath)
            throws Exception {
        return null;
    }

    /**
     * 将文件从源路径复制到目标路径
     * 此方法提供了一种简单的方式来复制文件，隐藏了复制操作的内部复杂性
     * 它通常用于文件管理或数据迁移场景
     *
     * @param srcPath  文件的源路径，不应为null或空，以避免文件找不到异常
     * @param destPath 文件的目标路径，不应为null或空，以避免文件找不到异常
     * @throws Exception 如果复制过程中发生任何错误，例如文件不存在、磁盘空间不足等，抛出此异常
     */
    default void copyFile(String srcPath, String destPath) throws Exception {
        // 此处省略了复制文件的具体实现代码
    }

    /**
     * 复制文件从源路径到目标路径
     * 此方法允许通过指定源文件路径和目标文件路径来复制文件此外，可以通过传递一个配置映射来定制文件复制过程
     * 该配置映射是可选的，如果不需要特殊配置，可以将其设置为null
     * 注意：此方法可能抛出异常，调用者需要处理这些异常
     *
     * @param srcPath  源文件的路径，不能为空
     * @param destPath 目标文件的路径，不能为空
     * @param conf     可选的配置映射，包含可能影响复制过程的配置信息如果不需要特殊配置，此参数可以为null
     * @throws Exception 如果复制过程中发生任何错误，将抛出异常具体的异常类型取决于错误的性质
     */
    default void copyFile(String srcPath, String destPath, @Nullable Map<String, Object> conf) throws Exception {
        // 方法实现留空，由调用者根据具体需求填充
    }

    /**
 * 复制指定路径下的所有文件到目标路径
 * 如果提供了配置信息，可能会根据配置信息影响复制行为
 * 例如，配置信息可以指示是否覆盖现有文件，或者是否包括子目录中的文件
 *
 * @param srcPath  源文件夹路径，表示需要复制的文件所在目录
 * @param destPath  目标文件夹路径，表示文件将被复制到的目录
 * @param conf  可选的配置信息，包含可能影响文件复制行为的键值对
 *              例如：是否覆盖同名文件，是否递归复制子目录等
 *              如果不需要任何特殊配置，可以传入null
 * @throws Exception  如果复制过程中发生任何错误，比如读取或写入文件时的问题，或者权限不足等，都将抛出此异常
 */
default void copyFiles(List<String> srcPaths, String destPrefix, @Nullable Map<String, Object> conf) throws Exception {
    // 方法实现将包括处理源路径和目标路径，以及根据配置信息进行文件复制的逻辑
}

}
