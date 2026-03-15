import request from '@/utils/request'

/** 下发指令 */
export const submitCommand = (data) => request.post('/strategy/command', data)

/** 获取指令执行状态 */
export const getCommandDetail = (commandId) => request.get('/strategy/command/status', { params: { commandId } })

/** 回复 AI 追问 */
export const replyCommand = (data) => request.post('/strategy/command/reply', data)

/** 指令列表（分页） */
export const getCommandList = (params) => request.get('/strategy/list', { params })
