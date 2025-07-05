package org.xiaoshuyui.automl.module.augmentAndQuality;

import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.config.S3ConfigProperties;
import org.xiaoshuyui.automl.util.S3FileDelegate;

import jakarta.annotation.Resource;
import lombok.Data;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

@RestController
@RequestMapping("/augmentAndQuality")
public class AugmentAndQualityController {

    @Data
    public static class GetImageRequest {
        String path;
    }

    @Resource
    private S3ConfigProperties s3ConfigProperties;

    @Resource
    private S3FileDelegate s3FileDelegate;

    @PostMapping("/get/image")
    public Result getImage(@RequestBody GetImageRequest request) throws Exception {
        return Result.OK_data(s3FileDelegate.getFile(request.path, s3ConfigProperties.getAugmentBucketName()));
    }

}
