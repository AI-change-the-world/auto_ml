package org.xiaoshuyui.automl;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
@MapperScan("org.xiaoshuyui.automl.module")
public class AutomlApplication {

    public static void main(String[] args) {
        SpringApplication.run(AutomlApplication.class, args);
    }

}
