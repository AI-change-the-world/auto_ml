package org.xiaoshuyui.automl.module;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import reactor.core.publisher.Flux;

@Service
public class LLMService {
    private final ChatClient defaultClient;

    public LLMService(@Qualifier("defaultChat") ChatClient defaultClient) {
        this.defaultClient = defaultClient;
    }

    // 发送聊天消息并返回结果
    public String chat(String prompt) {
        return defaultClient.prompt().user(prompt).call().content();
    }

    // 发送聊天消息并流式返回结果
    public Flux<String> streamChat(String prompt) {
        return defaultClient.prompt().user(prompt).stream().content();
    }
}
