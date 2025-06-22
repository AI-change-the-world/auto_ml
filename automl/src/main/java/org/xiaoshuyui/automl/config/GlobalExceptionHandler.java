package org.xiaoshuyui.automl.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.xiaoshuyui.automl.common.Result;

@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    // 捕获所有未处理的异常
    @ExceptionHandler(Exception.class)
    public Result handleException(Exception e) {
        log.error("服务器内部错误: " + e);
        e.printStackTrace();
        return Result.error(500, "服务器内部错误");
    }

    @ExceptionHandler(RuntimeException.class)
    public Result handleUserDefinedException(RuntimeException e) {
        log.error("runtime exception: " + e.getMessage());
        return Result.error(500, e.getMessage());
    }
}
