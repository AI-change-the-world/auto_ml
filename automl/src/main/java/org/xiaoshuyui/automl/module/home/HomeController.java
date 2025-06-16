package org.xiaoshuyui.automl.module.home;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.xiaoshuyui.automl.common.Result;
import org.xiaoshuyui.automl.module.home.service.HomeService;

@RestController
@RequestMapping("/home")
public class HomeController {

  private final HomeService homeService;

  public HomeController(HomeService homeService) {
    this.homeService = homeService;
  }

  @GetMapping("/index")
  public Result index() {
    return Result.OK_data(homeService.getHomeIndex());
  }
}
