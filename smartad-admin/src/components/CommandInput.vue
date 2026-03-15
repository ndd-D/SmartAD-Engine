<template>
  <el-card class="command-input-card" shadow="never">
    <div class="command-row">
      <el-input
        v-model="commandText"
        placeholder="输入广告投放指令，例如：针对年轻女性在抖音投放日预算500元的广告"
        size="large"
        :disabled="submitting || waiting"
        clearable
        @keyup.enter="handleSubmit"
      >
        <template #prepend>
          <el-icon style="font-size: 16px"><ChatDotRound /></el-icon>
        </template>
      </el-input>
      <el-button
        type="primary"
        size="large"
        :loading="submitting"
        :disabled="!commandText.trim() || waiting"
        @click="handleSubmit"
      >
        下发指令
      </el-button>
    </div>

    <!-- AI 追问 -->
    <el-alert
      v-if="waiting && aiQuestion"
      type="warning"
      :closable="false"
      style="margin-top: 12px"
    >
      <template #title>
        <span>AI 需要确认：{{ aiQuestion }}</span>
      </template>
      <div style="margin-top: 8px; display: flex; gap: 8px">
        <el-input
          v-model="replyText"
          placeholder="请回复 AI 的问题..."
          size="default"
          @keyup.enter="handleReply"
        />
        <el-button type="primary" :loading="replying" @click="handleReply">回复</el-button>
      </div>
    </el-alert>

    <!-- 处理中提示 -->
    <el-alert
      v-if="waiting && !aiQuestion"
      type="info"
      :closable="false"
      style="margin-top: 12px"
    >
      <template #title>
        <el-icon class="is-loading"><Loading /></el-icon>
        AI 正在处理指令，请稍候...
      </template>
    </el-alert>
  </el-card>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { submitCommand, getCommandDetail, replyCommand } from '@/api/command'

const emit = defineEmits(['submitted'])

const commandText = ref('')
const submitting = ref(false)
const replying = ref(false)
const waiting = ref(false)
const aiQuestion = ref('')
const replyText = ref('')
const currentCommandId = ref('')

let pollTimer = null

async function handleSubmit() {
  if (!commandText.value.trim()) return
  submitting.value = true
  try {
    const res = await submitCommand({ commandText: commandText.value.trim() })
    currentCommandId.value = res.data.commandId
    ElMessage.success('指令已下发，AI 处理中...')
    waiting.value = true
    startPolling()
    emit('submitted')
  } catch {
  } finally {
    submitting.value = false
  }
}

async function handleReply() {
  if (!replyText.value.trim()) return
  replying.value = true
  try {
    await replyCommand({
      commandId: currentCommandId.value,
      replyText: replyText.value.trim(),
    })
    replyText.value = ''
    aiQuestion.value = ''
    ElMessage.success('回复已提交，AI 继续处理中...')
  } catch {
  } finally {
    replying.value = false
  }
}

function startPolling() {
  clearPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await getCommandDetail(currentCommandId.value)
      const cmd = res.data
      const status = cmd.status

      if (status === 'waiting_reply') {
        aiQuestion.value = cmd.aiQuestion || 'AI 有问题需要确认'
      } else if (status === 'completed') {
        clearPolling()
        waiting.value = false
        aiQuestion.value = ''
        commandText.value = ''
        ElMessage.success('策略已生成，请在策略管理中查看')
        emit('submitted')
      } else if (status === 'failed') {
        clearPolling()
        waiting.value = false
        aiQuestion.value = ''
        ElMessage.error('指令处理失败：' + (cmd.aiQuestion || '未知错误'))
      }
    } catch {}
  }, 3000)
}

function clearPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onUnmounted(() => clearPolling())
</script>

<style scoped>
.command-input-card {
  margin-bottom: 20px;
  border-radius: 8px;
}
.command-row {
  display: flex;
  gap: 12px;
  align-items: center;
}
.command-row .el-input {
  flex: 1;
}
</style>
