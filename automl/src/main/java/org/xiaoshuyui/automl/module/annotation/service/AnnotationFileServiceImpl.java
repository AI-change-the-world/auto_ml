package org.xiaoshuyui.automl.module.annotation.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.apache.opendal.AsyncOperator;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.annotation.entity.AnnotationFile;
import org.xiaoshuyui.automl.module.annotation.mapper.AnnotationFileMapper;
import org.xiaoshuyui.automl.module.dataset.entity.DatasetStorage;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AnnotationFileServiceImpl extends ServiceImpl<AnnotationFileMapper, AnnotationFile> implements AnnotationFileService {

    final AnnotationFileMapper annotationFileMapper;

    public AnnotationFileServiceImpl(AnnotationFileMapper annotationFileMapper) {
        this.annotationFileMapper = annotationFileMapper;
    }

    public void saveSingle(AnnotationFile annotationFile) {
        annotationFileMapper.insert(annotationFile);
    }

    ///  only one level folder
    public void scanFolderSync(DatasetStorage storage) {
        final Map<String, String> conf = new HashMap<>();
        conf.put("root", "/");
        if (storage.getStorageType() == 0) {
            List<AnnotationFile> files = new ArrayList<>();
            try (AsyncOperator op = AsyncOperator.of("fs", conf)) {
                if (storage.getUrl() == null) {
                    return;
                }
                String path = storage.getUrl();
                if (!path.endsWith("/")) {
                    path = path + "/";
                }
                var res = op.list(path).join();
                for (var item : res) {
//                    System.out.println(item.path);
                    if (item.metadata.isDir()) {
                        continue;
                    }
                    if (item.metadata.isFile()) {
                        AnnotationFile annotationFile = new AnnotationFile();
                        annotationFile.setDatasetId(storage.getId());
                        annotationFile.setFilePath(item.path);
//                        annotationFile.setAnnotationPath(item.path.replace(".jpg", ".xml"));
                        files.add(annotationFile);
                    }
                }
            }
            this.saveBatch(files);
        }

    }

    public void scanFolderParallel(DatasetStorage storage) {
        Thread thread = new Thread(() -> {
            scanFolderSync(storage);
        });
        thread.start();
    }
}
