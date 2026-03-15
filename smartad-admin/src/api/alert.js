import request from '@/utils/request'

/** 告警列表（分页） */
export const getAlertList = (params) => request.get('/alert/list', { params })

/** 确认告警 */
export const confirmAlert = (alertId) => request.post(`/alert/confirm/${alertId}`)
