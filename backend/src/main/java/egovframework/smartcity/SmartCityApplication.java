package egovframework.smartcity;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 스마트시티 공공시설 & 민원 관리 시스템 (eGovFrame 4.x / Spring Boot 3)
 */
@SpringBootApplication
public class SmartCityApplication {

    public static void main(String[] args) {
        SpringApplication.run(SmartCityApplication.class, args);
        System.out.println("==========================================================");
        System.out.println(" [SMARTCITY] eGovFrame Backend Server Started successfully!");
        System.out.println(" REST & Nexacro API Base URL: http://localhost:8080/api");
        System.out.println("==========================================================");
    }
}
