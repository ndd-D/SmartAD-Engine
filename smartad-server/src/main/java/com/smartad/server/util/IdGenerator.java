package com.smartad.server.util;

import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

/**
 * 业务ID生成器（格式：前缀+yyyyMMdd+4位序号）
 * 第一阶段用数据库自增ID + 日期前缀实现，无并发竞争风险（单机）
 */
@Component
public class IdGenerator {

    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd");

    /**
     * 根据当天自增序号生成ID
     * @param prefix 前缀：CMD / STR / ALT / CASE
     * @param sequence 当天序号（从1开始）
     */
    public static String generate(String prefix, long sequence) {
        String dateStr = LocalDate.now().format(DATE_FORMAT);
        return prefix + dateStr + String.format("%04d", sequence);
    }
}
