package org.xiaoshuyui.automl.module.task.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import lombok.extern.slf4j.Slf4j;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.common.PageResult;
import org.xiaoshuyui.automl.config.S3ConfigProperties;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.task.entity.NewTrainingTaskRequest;
import org.xiaoshuyui.automl.module.task.entity.Task;
import org.xiaoshuyui.automl.module.task.entity.TaskLog;
import org.xiaoshuyui.automl.module.task.mapper.TaskLogMapper;
import org.xiaoshuyui.automl.module.task.mapper.TaskMapper;
import org.xiaoshuyui.automl.module.tool.entity.PythonEvalDatasetRequest;
import org.xiaoshuyui.automl.util.S3FileDelegate;

@Service
@Slf4j
public class TaskService {

  private final TaskMapper taskMapper;
  private final TaskLogMapper taskLogMapper;
  private final AnnotationService annotationService;
  private final S3FileDelegate s3FileDelegate;
  private final S3ConfigProperties s3ConfigProperties;

  @Value("${ai-platform.url}")
  String aiPlatformUrl;

  @Value("${ai-platform.train-yolo}")
  String trainYolo;

  public TaskService(
      TaskMapper taskMapper,
      TaskLogMapper taskLogMapper,
      AnnotationService annotationService,
      S3FileDelegate s3FileDelegate,
      S3ConfigProperties s3ConfigProperties) {
    this.taskMapper = taskMapper;
    this.taskLogMapper = taskLogMapper;
    this.annotationService = annotationService;
    this.s3FileDelegate = s3FileDelegate;
    this.s3ConfigProperties = s3ConfigProperties;
  }

  public PageResult getTaskList(int pageId, int pageSize) {
    IPage<Task> page = new Page<>(pageId, pageSize);
    QueryWrapper<Task> queryWrapper = new QueryWrapper<>();
    queryWrapper.eq("is_deleted", 0);

    IPage<Task> resultPage = taskMapper.selectPage(page, queryWrapper);

    return new PageResult<>(resultPage.getRecords(), resultPage.getTotal());
  }

  public List getTaskLogsById(Long id) {
    QueryWrapper queryWrapper = new QueryWrapper();
    queryWrapper.eq("task_id", id);
    return taskLogMapper.selectList(queryWrapper);
  }

  public Long getTaskCount(Long datasetId) {
    QueryWrapper queryWrapper = new QueryWrapper();
    queryWrapper.eq("dataset_id", datasetId);
    return taskMapper.selectCount(queryWrapper);
  }

  private static Gson gson =
      new GsonBuilder()
          .serializeNulls() // 👈 关键：保留 null 字段
          .create();

  static OkHttpClient client = new OkHttpClient();

  public void newDatasetEvalationTask(Long datasetId, Long annotationId) {
    Task task = new Task();
    task.setTaskType("test");
    task.setDatasetId(datasetId);
    task.setAnnotationId(annotationId);

    taskMapper.insert(task);

    var t =
        new Thread() {
          @Override
          public void run() {
            PythonEvalDatasetRequest request = new PythonEvalDatasetRequest();
            request.setDataset_id(datasetId);
            request.setAnnotation_id(annotationId);
            request.setTask_id(task.getTaskId());

            /// TODO 访问python
          }
        };
    t.start();
  }

  public void newTask(Task task) {
    taskMapper.insert(task);
  }

  public void newTrainTask(NewTrainingTaskRequest entity) {
    Task task = new Task();
    task.setTaskType("train");
    task.setDatasetId(entity.getDatasetId());
    Annotation annotation = annotationService.getById(entity.getAnnotationId());
    if (annotation.getAnnotationType() == 0) {
      task.setTaskType("cls_train");
    }

    task.setAnnotationId(entity.getAnnotationId());
    task.setTaskConfig(gson.toJson(entity));

    taskMapper.insert(task);

    var t =
        new Thread() {
          @Override
          public void run() {

            if (annotation.getAnnotationType() == 0) {
              // collection classification
              TaskLog taskLog = new TaskLog();
              taskLog.setTaskId(task.getTaskId());
              taskLog.setLogContent("[pre-train] collect all files");
              taskLogMapper.insert(taskLog);
              try {
                List<String> files =
                    s3FileDelegate.listFiles(
                        annotation.getAnnotationSavePath(),
                        s3ConfigProperties.getDatasetsBucketName());

                Map<String, String> classMap = new HashMap<>();
                for (String file : files) {
                  String content =
                      s3FileDelegate.getFileContent(
                          file, s3ConfigProperties.getDatasetsBucketName());
                  List<String> lines = content.lines().toList();
                  if (lines.size() != 2) {
                    continue;
                  }
                  String lineFileName = lines.get(0).substring(lines.get(0).lastIndexOf("/") + 1);
                  classMap.put(lineFileName, lines.get(1));
                }
                String json = gson.toJson(classMap);
                s3FileDelegate.putFile(
                    annotation.getAnnotationSavePath() + "/" + "classes.json",
                    json,
                    s3ConfigProperties.getDatasetsBucketName());
                taskLog.setLogContent("[pre-train] collect files success");
                taskLogMapper.insert(taskLog);

              } catch (Exception e) {
                taskLog.setLogContent("[post-train] collect files error");
                taskLogMapper.insert(taskLog);
                task.setStatus(3);
                taskMapper.updateById(task);
                e.printStackTrace();
                return;
              }
            }

            MediaType JSON = MediaType.parse("application/json; charset=utf-8");

            String json = "{\"task_id\": " + task.getTaskId() + "}";
            RequestBody body = RequestBody.create(json, JSON);

            // 构造请求
            Request request =
                new Request.Builder()
                    .url(aiPlatformUrl + trainYolo) // 替换成实际 URL
                    .post(body)
                    .build();

            // 执行请求
            try (Response response = client.newCall(request).execute()) {
              if (response.isSuccessful()) {
                log.info("Response: " + response.body().string());
              } else {
                log.error("Request failed: " + response.code());
              }
            } catch (IOException e) {
              e.printStackTrace();
              log.error("auto label error: {}", e.getMessage());
            }
          }
        };

    t.start();
  }
}
