package org.xiaoshuyui.automl.module.task.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import java.io.IOException;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.common.PageResult;
import org.xiaoshuyui.automl.module.task.entity.NewTrainingTaskRequest;
import org.xiaoshuyui.automl.module.task.entity.Task;
import org.xiaoshuyui.automl.module.task.mapper.TaskLogMapper;
import org.xiaoshuyui.automl.module.task.mapper.TaskMapper;

@Service
@Slf4j
public class TaskService {

  private final TaskMapper taskMapper;
  private final TaskLogMapper taskLogMapper;

  @Value("${ai-platform.url}")
  String aiPlatformUrl;

  @Value("${ai-platform.train-yolo}")
  String trainYolo;

  public TaskService(TaskMapper taskMapper, TaskLogMapper taskLogMapper) {
    this.taskMapper = taskMapper;
    this.taskLogMapper = taskLogMapper;
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

  private static Gson gson =
      new GsonBuilder()
          .serializeNulls() // 👈 关键：保留 null 字段
          .create();

  static OkHttpClient client = new OkHttpClient();

  public void newTrainTask(NewTrainingTaskRequest entity) {
    Task task = new Task();
    task.setTaskType(0);
    task.setDatasetId(entity.getDatasetId());
    task.setAnnotationId(entity.getAnnotationId());
    task.setTaskConfig(gson.toJson(entity));

    taskMapper.insert(task);

    var t =
        new Thread() {
          @Override
          public void run() {
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
