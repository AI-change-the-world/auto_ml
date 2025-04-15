package org.xiaoshuyui.automl.module.dataset.service;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import org.apache.opendal.AsyncOperator;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.dataset.entity.DatasetFile;
import org.xiaoshuyui.automl.module.dataset.entity.DatasetStorage;
import org.xiaoshuyui.automl.module.dataset.mapper.DatasetFileMapper;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class DatasetFileServiceImpl extends ServiceImpl<DatasetFileMapper, DatasetFile> implements DatasetFileService {
    final DatasetFileMapper mapper;

    public DatasetFileServiceImpl(DatasetFileMapper datasetFileMapper) {
        this.mapper = datasetFileMapper;
    }

    ///  only one level folder
    ///
    /// todo: exception handling
    public void scanFolderSync(DatasetStorage storage) {
        final Map<String, String> conf = new HashMap<>();
        conf.put("root", "/");
        if (storage.getStorageType() == 0) {
            List<DatasetFile> files = new ArrayList<>();
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
                    if (item.metadata.isDir()) {
                        continue;
                    }
                    if (item.metadata.isFile()) {
                        DatasetFile datasetFile = new DatasetFile();
                        datasetFile.setDatasetId(storage.getId());
                        datasetFile.setFilePath(item.path);
                        files.add(datasetFile);
                        // save batch every 100 files
                        if (files.size() >= 100) {
                            this.saveBatch(files, 100);
                            files.clear();
                        }
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
