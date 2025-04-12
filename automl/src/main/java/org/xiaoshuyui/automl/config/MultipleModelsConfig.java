package org.xiaoshuyui.automl.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.document.MetadataMode;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.model.SimpleApiKey;
import org.springframework.ai.openai.OpenAiChatModel;
import org.springframework.ai.openai.OpenAiChatOptions;
import org.springframework.ai.openai.OpenAiEmbeddingModel;
import org.springframework.ai.openai.OpenAiEmbeddingOptions;
import org.springframework.ai.openai.api.OpenAiApi;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

@Slf4j
@Configuration
public class MultipleModelsConfig {

    @Value("${spring.ai.openai.chat.options.model}")
    String modelName;

    @Value("${spring.ai.openai.base-url}")
    String url;

    @Value("${spring.ai.openai.api-key}")
    String sk;

    @Value("${spring.ai.openai.embedding.options.model}")
    String embeddingModelName;

    @Bean(name = "defaultChat")
    public ChatClient defaultChatClient() {
        log.info("Using model: {}", modelName);
        log.info("Using base url: {}", url);
        SimpleApiKey simpleApiKey = new SimpleApiKey(sk);
        OpenAiApi aiApi = new OpenAiApi.Builder().apiKey(simpleApiKey).baseUrl(url).build();
        ChatModel chatModel = OpenAiChatModel.builder().openAiApi(aiApi).defaultOptions(OpenAiChatOptions.builder().model(modelName).build()).build();
        return ChatClient.builder(chatModel).build();
    }

    @Primary
    @Bean(name = "defaultEmbedding")
    public EmbeddingModel embeddingChatClient() {
        SimpleApiKey simpleApiKey = new SimpleApiKey(sk);
        OpenAiApi aiApi = new OpenAiApi.Builder().apiKey(simpleApiKey).baseUrl(url).build();
        return new OpenAiEmbeddingModel(aiApi, MetadataMode.EMBED, OpenAiEmbeddingOptions.builder().model(embeddingModelName).build());
    }
}

