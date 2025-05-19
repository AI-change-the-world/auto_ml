package org.xiaoshuyui.automl.util;

import java.util.ArrayList;
import java.util.List;
import java.util.AbstractMap.SimpleEntry;

import org.springframework.stereotype.Component;
import org.xiaoshuyui.automl.config.S3ConfigProperties;

import com.alibaba.nacos.shaded.com.google.gson.Gson;

import lombok.Data;

@Component
public class QwenVLDatasetGenerator {

    final S3FileDelegate s3FileDelegate;
    final S3ConfigProperties s3ConfigProperties;

    public QwenVLDatasetGenerator(S3FileDelegate s3FileDelegate, S3ConfigProperties s3ConfigProperties) {
        this.s3FileDelegate = s3FileDelegate;
        this.s3ConfigProperties = s3ConfigProperties;
    }

    static Gson gson = new Gson();

    @Data
    static class QwenVLAnnotation {
        List<String> images;
        List<Messages> messages;
    }

    @Data
    static class Messages {
        String role;
        String content;

        static Messages of(String role, String content) {
            Messages messages = new Messages();
            messages.role = role;
            messages.content = content;
            return messages;
        }
    }

    public String generateDataset(String annotationSavePath, String datasetSavePath) throws Exception {
        List results = new ArrayList<>();
        List<String> annotationFiles = s3FileDelegate.listFiles(annotationSavePath,
                s3ConfigProperties.getDatasetsBucketName());
        List<String> imageFiles = s3FileDelegate.listFiles(datasetSavePath,
                s3ConfigProperties.getDatasetsBucketName());

        List<SimpleEntry<String, String>> simpleEntries = FileAnnotationMerger.mergeFilesAndAnnotations(imageFiles,
                annotationFiles);
        final Messages userMessages = Messages.of("user", "<image>详细描述图中内容");
        for (SimpleEntry<String, String> simpleEntry : simpleEntries) {
            if (simpleEntry.getValue().isEmpty()) {
                continue;
            }

            QwenVLAnnotation qwenVLAnnotation = new QwenVLAnnotation();
            String filename = simpleEntry.getKey().substring(simpleEntry.getKey().lastIndexOf('/') + 1);
            qwenVLAnnotation.setImages(List.of("data/mllm_demo_data/" + filename));

            String annotationContent = s3FileDelegate.getFile(simpleEntry.getValue(),
                    s3ConfigProperties.getDatasetsBucketName());
            Messages messages = Messages.of("assistant", annotationContent);
            qwenVLAnnotation.setMessages(List.of(userMessages, messages));
            results.add(qwenVLAnnotation);
        }

        return gson.toJson(results);
    }
}
