package org.xiaoshuyui.automl.module.predict;

import java.util.HashMap;
import java.util.concurrent.Executors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.common.SseResponse;
import org.xiaoshuyui.automl.module.dataset.entity.response.GetFileContentResponse;
import org.xiaoshuyui.automl.module.predict.entity.DescribeImageListRequest;
import org.xiaoshuyui.automl.module.predict.entity.PredictDataWithDuration;
import org.xiaoshuyui.automl.module.predict.entity.ProcessRequest;
import org.xiaoshuyui.automl.module.predict.service.HttpService;
import org.xiaoshuyui.automl.module.predict.service.PredictDataService;
import org.xiaoshuyui.automl.module.predict.service.PredictTaskService;
import org.xiaoshuyui.automl.util.SseUtil;

@RestController
@Slf4j
@RequestMapping("/predict")
public class PredictController {
  private final HttpService httpService;
  private final PredictTaskService predictTaskService;
  private final PredictDataService predictDataService;

  static HashMap<Long, PredictDataWithDuration> globalHashMap = new HashMap<>();

  static HashMap<String, PredictDataWithDuration> globalS3 = new HashMap<>();

  public PredictController(
      HttpService httpService,
      PredictTaskService predictTaskService,
      PredictDataService predictDataService) {
    this.httpService = httpService;
    this.predictTaskService = predictTaskService;
    this.predictDataService = predictDataService;
  }

  @PostMapping("/videoProcess")
  public SseEmitter videoProcess(@RequestBody ProcessRequest req) {
    SseEmitter sseEmitter = new SseEmitter();

    Executors.newSingleThreadExecutor()
        .execute(
            () -> {
              var predictData = predictDataService.getById(req.getFileId());
              var sessionId = predictTaskService.create(req.getFileId());
              SseResponse<String> sseResponse = new SseResponse();
              sseResponse.setStatus("on data ...");
              sseResponse.setData(sessionId);
              sseResponse.setDone(false);
              SseUtil.sseSend(sseEmitter, sseResponse);
              httpService
                  .getVideoProcess(predictData.getFileName(), sessionId)
                  .subscribe(
                      line -> {
                        sseResponse.setData(line);
                        if (!line.contains("video_path")) {
                          sseResponse.setMessage(line);
                        } else {
                          sseResponse.setStatus("done");
                        }
                        SseUtil.sseSend(sseEmitter, sseResponse);
                      },
                      throwable -> {
                        sseResponse.setStatus("error");
                        sseResponse.setDone(true);
                        sseResponse.setMessage("[DONE] " + throwable.getMessage());
                        log.error(throwable.toString());
                        SseUtil.sseSend(sseEmitter, sseResponse);
                        sseEmitter.complete();
                      },
                      () -> {
                        sseResponse.setStatus("done");
                        sseResponse.setDone(true);
                        sseResponse.setData("[DONE]");
                        sseResponse.setMessage("[DONE]");
                        SseUtil.sseSend(sseEmitter, sseResponse);
                        sseEmitter.complete();
                      });
            });

    return sseEmitter;
  }

  @GetMapping("/file/list")
  public Result list() {
    return Result.OK_data(predictDataService.getDatas());
  }

  @GetMapping("/file/preview/{id}")
  public Result preview(@PathVariable Long id) {
    try {
      GetFileContentResponse response = new GetFileContentResponse();
      if (globalHashMap.containsKey(id)) {
        if (!globalHashMap.get(id).isExpired()) {
          response.setContent(globalHashMap.get(id).getPresignUrl());
          return Result.OK_data(response);
        }
      }
      var s = predictDataService.getFile(id);

      response.setContent(s);
      PredictDataWithDuration predictDataWithDuration = new PredictDataWithDuration();
      predictDataWithDuration.refresh(s);
      globalHashMap.put(id, predictDataWithDuration);
      return Result.OK_data(response);
    } catch (Exception e) {
      log.error(e.toString());
      return Result.error(e.getMessage());
    }
  }

  @GetMapping("/s3/preview")
  public Result s3preview(@RequestParam String name) {
    try {
      GetFileContentResponse response = new GetFileContentResponse();
      if (globalS3.containsKey(name)) {
        if (!globalS3.get(name).isExpired()) {
          response.setContent(globalS3.get(name).getPresignUrl());
          return Result.OK_data(response);
        }
      }
      var s = predictDataService.getFile(name);

      response.setContent(s);
      PredictDataWithDuration predictDataWithDuration = new PredictDataWithDuration();
      predictDataWithDuration.refresh(s);
      globalS3.put(name, predictDataWithDuration);
      return Result.OK_data(response);
    } catch (Exception e) {
      log.error(e.toString());
      return Result.error(e.getMessage());
    }
  }

  @GetMapping("/describe")
  public SseEmitter describeImage(@RequestParam String name) {
    SseEmitter sseEmitter = new SseEmitter();
    SseResponse<String> sseResponse = new SseResponse<>();
    Executors.newSingleThreadExecutor()
        .execute(
            () -> {
              httpService
                  .getDescribeImage(name)
                  .subscribe(
                      line -> {
                        sseResponse.setData(line);
                        SseUtil.sseSend(sseEmitter, sseResponse);
                      },
                      throwable -> {
                        sseResponse.setStatus("error");
                        sseResponse.setMessage(throwable.getMessage());
                        sseResponse.setDone(true);
                        SseUtil.sseSend(sseEmitter, sseResponse);
                        sseEmitter.complete();
                      },
                      () -> {
                        sseResponse.setDone(true);
                        sseResponse.setStatus("done");
                        sseResponse.setMessage("[DONE]");
                        SseUtil.sseSend(sseEmitter, sseResponse);
                        sseEmitter.complete();
                      });
            });

    return sseEmitter;
  }

  @PostMapping("/describe")
  public SseEmitter describeImageWithPrompt(@RequestBody DescribeImageListRequest request) {
    SseEmitter sseEmitter = new SseEmitter();
    SseResponse<String> sseResponse = new SseResponse<>();
    Executors.newSingleThreadExecutor()
        .execute(
            () -> {
              httpService
                  .getDescribeImage(request.getFrames().get(0), request.getPrompt())
                  .subscribe(
                      line -> {
                        sseResponse.setData(line);
                        SseUtil.sseSend(sseEmitter, sseResponse);
                      },
                      throwable -> {
                        sseResponse.setStatus("error");
                        sseResponse.setMessage(throwable.getMessage());
                        sseResponse.setDone(true);
                        SseUtil.sseSend(sseEmitter, sseResponse);
                        sseEmitter.complete();
                      },
                      () -> {
                        sseResponse.setDone(true);
                        sseResponse.setStatus("done");
                        sseResponse.setMessage("[DONE]");
                        SseUtil.sseSend(sseEmitter, sseResponse);
                        sseEmitter.complete();
                      });
            });

    return sseEmitter;
  }

  @PostMapping("/describe/list")
  public SseEmitter describeImageList(@RequestBody DescribeImageListRequest request) {
    SseEmitter sseEmitter = new SseEmitter();
    SseResponse<String> sseResponse = new SseResponse<>();
    Executors.newSingleThreadExecutor()
        .execute(
            () -> {
              if (request.getFrames().size() == 0) {
                sseResponse.setStatus("error");
                sseResponse.setMessage("frames is empty");
                sseResponse.setDone(true);
                SseUtil.sseSend(sseEmitter, sseResponse);
                sseEmitter.complete();
                return;
              }

              if (request.getFrames().size() > 20) {
                request.setFrames(request.getFrames().subList(0, 20));
              }

              httpService
                  .getDescribeImageList(request.getFrames())
                  .subscribe(
                      line -> {
                        sseResponse.setData(line);
                        SseUtil.sseSend(sseEmitter, sseResponse);
                      },
                      throwable -> {
                        sseResponse.setStatus("error");
                        sseResponse.setMessage(throwable.getMessage());
                        sseResponse.setDone(true);
                        SseUtil.sseSend(sseEmitter, sseResponse);
                        sseEmitter.complete();
                      },
                      () -> {
                        sseResponse.setDone(true);
                        sseResponse.setStatus("done");
                        sseResponse.setMessage("");
                        SseUtil.sseSend(sseEmitter, sseResponse);
                        sseEmitter.complete();
                      });
            });

    return sseEmitter;
  }
}
