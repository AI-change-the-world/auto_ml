package org.xiaoshuyui.automl.module.predict;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.xiaoshuyui.automl.common.SseResponse;
import org.xiaoshuyui.automl.module.predict.service.HttpService;
import org.xiaoshuyui.automl.module.predict.service.PredictDataService;
import org.xiaoshuyui.automl.module.predict.service.PredictTaskService;
import org.xiaoshuyui.automl.util.SseUtil;
import reactor.core.publisher.Flux;

@RestController
@Slf4j
@RequestMapping("/predict")
public class PredictController {
    private final HttpService httpService;
    private final PredictTaskService predictTaskService;
    private final PredictDataService predictDataService;

    public PredictController(HttpService httpService, PredictTaskService predictTaskService, PredictDataService predictDataService)
    {
        this.httpService = httpService;
        this.predictTaskService = predictTaskService;
        this.predictDataService = predictDataService;
    }

    @GetMapping("/videoProcess/{id}")
    public SseEmitter videoProcess(@PathVariable long id)
    {
        SseEmitter sseEmitter = new SseEmitter();
        var predictData = predictDataService.getById(id);
        var sessionId = predictTaskService.create(id);
        SseResponse<String> sseResponse = new SseResponse();
        sseResponse.setStatus("on data ...");
        sseResponse.setDone(false);

        httpService.getVideoProcess(predictData.getFileName(), sessionId).subscribe(line -> {
            sseResponse.setData(line);
            SseUtil.sseSend(sseEmitter, sseResponse);
        },  throwable -> {
            sseResponse.setStatus("error");
            sseResponse.setMessage(throwable.getMessage());
            log.error(throwable.toString());
            SseUtil.sseSend(sseEmitter, sseResponse);
            sseEmitter.complete();
        }, () -> {
            sseResponse.setStatus("done");
            sseResponse.setDone(true);
            SseUtil.sseSend(sseEmitter, sseResponse);
            sseEmitter.complete();
        });

        return sseEmitter;
    }
}
