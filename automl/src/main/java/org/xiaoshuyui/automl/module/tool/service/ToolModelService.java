package org.xiaoshuyui.automl.module.tool.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.common.BaseResponse;
import org.xiaoshuyui.automl.module.annotation.entity.Annotation;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.dataset.service.DatasetService;
import org.xiaoshuyui.automl.module.tool.OpenAiClientFactory;
import org.xiaoshuyui.automl.module.tool.entity.LabelData;
import org.xiaoshuyui.automl.module.tool.entity.ModelUseRequest;
import org.xiaoshuyui.automl.module.tool.entity.PredictRequest;
import org.xiaoshuyui.automl.module.tool.entity.ToolModel;
import org.xiaoshuyui.automl.module.tool.mapper.ToolModelMapper;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

@Service
public class ToolModelService {

    @Value("${ai-platform.url}")
    String baseUrl;

    @Value("${ai-platform.get_label}")
    String getLabelApi;

    private final ToolModelMapper toolModelMapper;
    private final OpenAiClientFactory openAiClientFactory;
    private final DatasetService datasetService;
    private final AnnotationService annotationService;

    public ToolModelService(ToolModelMapper toolModelMapper, OpenAiClientFactory openAiClientFactory, DatasetService datasetService, AnnotationService annotationService) {
        this.toolModelMapper = toolModelMapper;
        this.openAiClientFactory = openAiClientFactory;
        this.datasetService = datasetService;
        this.annotationService = annotationService;
    }

    public List<ToolModel> getAll() {
        QueryWrapper<ToolModel> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("is_deleted", 0);
        return toolModelMapper.selectList(queryWrapper);
    }

    public ToolModel getById(Long id) {
        QueryWrapper<ToolModel> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("is_deleted", 0);
        queryWrapper.eq("tool_model_id", id);
        return toolModelMapper.selectOne(queryWrapper);
    }

    private static final OkHttpClient okClient = new OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(180, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .build();
    private static final ObjectMapper mapper = new ObjectMapper();


    public String chat(ModelUseRequest request) throws Exception {
        ToolModel model = getById(request.getModelId());
        if (model == null) {
            throw new Exception("model not found");
        }
        ChatClient client = openAiClientFactory.createClient(model.getBaseUrl(), model.getApiKey(), model.getModelName());
        if (request.isImage()) {
            var dataset = datasetService.get(request.getDatasetId());
            if (dataset == null) {
                throw new Exception("dataset not found");
            }
            String fileContent = datasetService.getFileContentUnCompress(dataset.getUrl(), request.getContent(), dataset.getStorageType());
            PredictRequest requestBody = new PredictRequest();
            requestBody.setImage_data(fileContent);
            requestBody.setModel_id((int) request.getModelId());
            if (request.getAnnotationId() != 0) {
                Annotation annotation = annotationService.getById(request.getAnnotationId());
                if (annotation != null) {
                    requestBody.setClasses(List.of(annotation.getClassItems().split(";")));
                }
            } else {
                requestBody.setClasses(new ArrayList<>());
            }
            requestBody.setPrompt(request.getPrompt());
            // 将对象序列化为 JSON
            String json = mapper.writeValueAsString(requestBody);

            // 构造 POST 请求
            Request okrequest = new Request.Builder()
                    .url(baseUrl + getLabelApi)
                    .post(RequestBody.create(json, MediaType.parse("application/json")))
                    .build();
            Response response = okClient.newCall(okrequest).execute();
            if (response.isSuccessful()) {
                String responseBody = response.body().string();
                BaseResponse<LabelData> result = mapper.readValue(responseBody, new TypeReference<>() {
                });
                return result.getData().toString();
            }

            throw new Exception("request failed");
        } else {
            // message
            return client.prompt(request.getPrompt()).call().content();
        }
    }
}
