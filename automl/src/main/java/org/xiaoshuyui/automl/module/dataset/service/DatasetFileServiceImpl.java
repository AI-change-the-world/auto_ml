package org.xiaoshuyui.automl.module.dataset.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.extern.slf4j.Slf4j;
import org.apache.opendal.AsyncOperator;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.dataset.entity.Dataset;
import org.xiaoshuyui.automl.module.dataset.entity.DatasetFile;
import org.xiaoshuyui.automl.module.dataset.mapper.DatasetFileMapper;
import org.xiaoshuyui.automl.module.dataset.mapper.DatasetMapper;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Deprecated(since = "no longer used")
@Service
@Slf4j
public class DatasetFileServiceImpl extends ServiceImpl<DatasetFileMapper, DatasetFile> implements DatasetFileService {
    final DatasetFileMapper mapper;

    final DatasetMapper datasetMapper;

    public DatasetFileServiceImpl(DatasetFileMapper datasetFileMapper, DatasetMapper datasetMapper) {
        this.mapper = datasetFileMapper;
        this.datasetMapper = datasetMapper;
    }

    ///  only one level folder
    ///
    /// todo: exception handling
    public void scanFolderSync(Dataset storage) {
        if (storage.getUrl() == null) {
            return;
        }
        final Map<String, String> conf = new HashMap<>();
        String path = storage.getUrl();
        if (!path.endsWith("/")) {
            path = path + "/";
        }
        log.info("scan folder: {}", path);
        conf.put("root", path);
        if (storage.getStorageType() == 0) {
            List<DatasetFile> files = new ArrayList<>();
            try (AsyncOperator op = AsyncOperator.of("fs", conf)) {
                var res = op.list("").join();
                log.info("res: {}", res.isEmpty());
                for (var item : res) {
                    log.info("file: {}", item.path);
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
                this.saveBatch(files);
                storage.setScanStatus(1);
                datasetMapper.updateById(storage);
            } catch (Exception e) {
                storage.setScanStatus(2);
                datasetMapper.updateById(storage);
                log.error("scan folder error: {}", e.getMessage());
            }

        }

    }

    public void scanFolderParallel(Dataset dataset) {
        Thread thread = new Thread(() -> {
            scanFolderSync(dataset);
        });
        thread.start();
    }

    public List<DatasetFile> getSample() {
        QueryWrapper<DatasetFile> queryWrapper = new QueryWrapper<>();
        queryWrapper.last("LIMIT 5");
        return mapper.selectList(null);
    }

    public long getCount(long id) {
        QueryWrapper<DatasetFile> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("dataset_id", id);
        return mapper.selectCount(queryWrapper);
    }
}
