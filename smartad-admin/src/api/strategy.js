import request from '@/utils/request'

/** 策略列表（分页+筛选） */
export const getStrategyList = (params) => request.get('/strategy/list', { params })

/** 策略确认/编辑 */
export const confirmStrategy = (data) => request.post('/strategy/confirm', data)

/** 策略暂停/下线 */
export const stopStrategy = (data) => request.post('/strategy/stop', data)

/** 高风险策略人工确认 */
export const confirmRiskStrategy = (data) => request.post('/strategy/risk/confirm', data)
