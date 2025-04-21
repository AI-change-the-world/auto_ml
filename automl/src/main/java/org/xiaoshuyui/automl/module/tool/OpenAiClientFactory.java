package org.xiaoshuyui.automl.module.tool;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.model.SimpleApiKey;
import org.springframework.ai.openai.OpenAiChatModel;
import org.springframework.ai.openai.OpenAiChatOptions;
import org.springframework.ai.openai.api.OpenAiApi;
import org.springframework.stereotype.Component;

@Component
public class OpenAiClientFactory {

    public ChatClient createClient(String baseUrl, String apiKey, String modelName) {
        SimpleApiKey simpleApiKey = new SimpleApiKey(apiKey);
        OpenAiApi aiApi = new OpenAiApi.Builder().apiKey(simpleApiKey).baseUrl(baseUrl).build();
        ChatModel chatModel = OpenAiChatModel.builder().openAiApi(aiApi).defaultOptions(OpenAiChatOptions.builder().model(modelName).build()).build();
        return ChatClient.builder(chatModel).build();
    }
}
