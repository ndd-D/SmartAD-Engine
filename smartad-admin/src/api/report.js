import request from '@/utils/request'

/** 获取策略报表（分页） */
export const getReportList = (params) => request.get('/report/list', { params })

/** 获取指定策略报表详情 */
export const getReportDetail = (strategyId) => request.get(`/report/detail/${strategyId}`)
