package org.xiaoshuyui.automl.module.home.service;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.xiaoshuyui.automl.module.annotation.service.AnnotationService;
import org.xiaoshuyui.automl.module.dataset.service.DatasetService;
import org.xiaoshuyui.automl.module.home.entity.HomeIndex;
import org.xiaoshuyui.automl.module.task.service.TaskService;

@Service
public class HomeService {

    private static HomeIndex homeIndex = new HomeIndex();

    private final DatasetService datasetService;
    private final TaskService taskService;
    private final AnnotationService annotationService;

    public HomeService(
            DatasetService datasetService, TaskService taskService, AnnotationService annotationService) {
        this.datasetService = datasetService;
        this.taskService = taskService;
        this.annotationService = annotationService;
    }

    public HomeIndex getHomeIndex() {
        return homeIndex;
    }

    @Scheduled(fixedRate = 3_600_000)
    private void updateHomeIndex() {
        homeIndex = new HomeIndex(
                datasetService.getDatasetCount(),
                annotationService.getAnnotationCount(),
                taskService.getTaskCount(),
                taskService.getTaskErrorCount(),
                taskService.getTaskPerDay(30));
    }
}
