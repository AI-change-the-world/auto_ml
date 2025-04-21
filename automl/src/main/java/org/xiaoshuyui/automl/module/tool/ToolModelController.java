package org.xiaoshuyui.automl.module.tool;

import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.common.SseResponse;
import org.xiaoshuyui.automl.module.tool.entity.TryModel;
import org.xiaoshuyui.automl.module.tool.service.ToolModelService;
import org.xiaoshuyui.automl.util.SseUtil;

import java.util.concurrent.Executors;

@RestController
@RequestMapping("/tool-model")
public class ToolModelController {

    final ToolModelService toolModelService;
    final OpenAiClientFactory openAiClientFactory;

    public ToolModelController(ToolModelService toolModelService, OpenAiClientFactory openAiClientFactory) {
        this.toolModelService = toolModelService;
        this.openAiClientFactory = openAiClientFactory;
    }

    @GetMapping("/list")
    public Result getAll() {
        return Result.OK_data(toolModelService.getAll());
    }

    @GetMapping("/{id}")
    public Result getById(@PathVariable Long id) {
        return Result.OK_data(toolModelService.getById(id));
    }

    @PostMapping("/test")
    public SseEmitter test(@RequestBody TryModel request) {
        SseEmitter emitter = new SseEmitter();
        SseResponse<String> sseResponse = new SseResponse<>();
        if (request.getContent() == null || request.getContent().isEmpty()) {
            sseResponse.setData("error: No data");
            SseUtil.sseSend(emitter, sseResponse);
            emitter.complete();
        }

        var client = openAiClientFactory.createClient(request.getBaseUrl(), request.getApiKey(), request.getModelName());

        Executors.newSingleThreadExecutor().execute(() -> {
            if (request.getContent().startsWith("data")) {
                // TODO image
                // base64
            } else {
                // message
                client.prompt(request.getContent()).stream().content().subscribe(s -> {
                            sseResponse.setData(s);
                            SseUtil.sseSend(emitter, sseResponse);
                        },
                        error -> {
                            sseResponse.setData("error: " + error.getMessage());
                            SseUtil.sseSend(emitter, sseResponse);
                            emitter.complete();
                        },
                        () -> {
                            sseResponse.setDone(true);
                            SseUtil.sseSend(emitter, sseResponse);
                            emitter.complete();
                        });
            }
        });


        return emitter;
    }
}
