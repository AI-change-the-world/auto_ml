package org.xiaoshuyui.automl.config;

import com.zaxxer.hikari.HikariDataSource;
import jakarta.annotation.Resource;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.cloud.context.config.annotation.RefreshScope;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import javax.sql.DataSource;


@Configuration
@ConfigurationProperties(prefix = "datasource")
public class DataSourceConfiguration {

    @Resource
    private DataSourceConfig dataSourceConfig;

    @Bean
    @RefreshScope
    public DataSource dataSource() {
        HikariDataSource dataSource = new HikariDataSource();
        dataSource.setJdbcUrl(dataSourceConfig.getDbUrl());
        dataSource.setUsername(dataSourceConfig.getDbUsername());
        dataSource.setPassword(dataSourceConfig.getDbPassword());
        dataSource.setDriverClassName("com.mysql.cj.jdbc.Driver");
        dataSource.setMaxLifetime(1800000);
        dataSource.setIdleTimeout(600000);
        return dataSource;
    }
}
