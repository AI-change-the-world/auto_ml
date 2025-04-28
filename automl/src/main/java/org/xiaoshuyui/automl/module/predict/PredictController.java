package org.xiaoshuyui.automl.module.predict;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.common.SseResponse;
import org.xiaoshuyui.automl.module.predict.entity.ProcessRequest;
import org.xiaoshuyui.automl.module.predict.service.HttpService;
import org.xiaoshuyui.automl.module.predict.service.PredictDataService;
import org.xiaoshuyui.automl.module.predict.service.PredictTaskService;
import org.xiaoshuyui.automl.util.SseUtil;

import java.util.concurrent.Executors;

@RestController
@Slf4j
@RequestMapping("/predict")
public class PredictController {
    private final HttpService httpService;
    private final PredictTaskService predictTaskService;
    private final PredictDataService predictDataService;

    public PredictController(HttpService httpService, PredictTaskService predictTaskService, PredictDataService predictDataService) {
        this.httpService = httpService;
        this.predictTaskService = predictTaskService;
        this.predictDataService = predictDataService;
    }

    @PostMapping("/videoProcess")
    public SseEmitter videoProcess(@RequestBody ProcessRequest req) {
        SseEmitter sseEmitter = new SseEmitter();

        Executors.newSingleThreadExecutor().execute(() -> {
            var predictData = predictDataService.getById(req.getFileId());
            var sessionId = predictTaskService.create(req.getFileId());
            SseResponse<String> sseResponse = new SseResponse();
            sseResponse.setStatus("on data ...");
            sseResponse.setDone(false);

            httpService.getVideoProcess(predictData.getFileName(), sessionId).subscribe(line -> {
                sseResponse.setData(line);
                if (!line.contains("video_path")) {
                    sseResponse.setMessage(line);
                } else {
                    sseResponse.setStatus("done");
                }
                SseUtil.sseSend(sseEmitter, sseResponse);
            }, throwable -> {
                sseResponse.setStatus("error");
                sseResponse.setMessage(throwable.getMessage());
                log.error(throwable.toString());
                SseUtil.sseSend(sseEmitter, sseResponse);
                sseEmitter.complete();
            }, () -> {
                sseResponse.setStatus("done");
                sseResponse.setDone(true);
                sseResponse.setData("");
                sseResponse.setMessage("done");
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
}
