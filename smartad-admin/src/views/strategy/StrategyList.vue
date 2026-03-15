<template>
  <div>
    <!-- 搜索栏 -->
    <el-card shadow="never" style="margin-bottom: 16px; border-radius: 8px">
      <el-form :model="query" inline>
        <el-form-item label="策略状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 160px">
            <el-option label="待人工确认" value="pending" />
            <el-option label="高风险待确认" value="risk_pending" />
            <el-option label="投放中" value="running" />
            <el-option label="已暂停" value="paused" />
            <el-option label="已下线" value="offline" />
          </el-select>
        </el-form-item>
        <el-form-item label="渠道">
          <el-select v-model="query.channel" placeholder="全部" clearable style="width: 130px">
            <el-option label="抖音" value="douyin" />
            <el-option label="快手" value="kuaishou" />
            <el-option label="微博" value="weibo" />
            <el-option label="头条" value="toutiao" />
            <el-option label="百度" value="baidu" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 策略表格 -->
    <el-card shadow="never" style="border-radius: 8px">
      <el-table
        v-loading="loading"
        :data="tableData"
        row-key="strategyId"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="strategyId" label="策略ID" width="180" />
        <el-table-column prop="commandId" label="指令ID" width="180" />
        <el-table-column prop="crowdTag" label="人群标签" width="140">
          <template #default="{ row }">
            <el-tag type="info">{{ row.crowdTag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="channel" label="渠道" width="100">
          <template #default="{ row }">
            <el-tag>{{ channelMap[row.channel] || row.channel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="budgetDay" label="日预算(元)" width="120" align="right">
          <template #default="{ row }">{{ row.budgetDay?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="bidPrice" label="出价(分)" width="100" align="right" />
        <el-table-column prop="status" label="状态" width="130">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="aiScore" label="AI评分" width="90" align="center">
          <template #default="{ row }">
            <span v-if="row.aiScore != null" :style="{ color: row.aiScore >= 70 ? '#67c23a' : '#e6a23c' }">
              {{ row.aiScore }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="170" />
        <el-table-column label="操作" fixed="right" width="220">
          <template #default="{ row }">
            <!-- 待确认 -->
            <template v-if="row.status === 'pending'">
              <el-button size="small" type="primary" @click="openConfirmDialog(row, 'approve')">上线</el-button>
              <el-button size="small" @click="openConfirmDialog(row, 'edit')">编辑上线</el-button>
              <el-button size="small" type="danger" @click="openConfirmDialog(row, 'reject')">拒绝</el-button>
            </template>
            <!-- 高风险待确认 -->
            <template v-else-if="row.status === 'risk_pending'">
              <el-button size="small" type="warning" @click="openRiskConfirmDialog(row, 'approve')">
                确认上线
              </el-button>
              <el-button size="small" type="danger" @click="openRiskConfirmDialog(row, 'reject')">拒绝</el-button>
            </template>
            <!-- 投放中 -->
            <template v-else-if="row.status === 'running'">
              <el-button size="small" @click="openStopDialog(row, 'pause')">暂停</el-button>
              <el-button size="small" type="danger" @click="openStopDialog(row, 'offline')">下线</el-button>
            </template>
            <!-- 已暂停 -->
            <template v-else-if="row.status === 'paused'">
              <el-button size="small" type="danger" @click="openStopDialog(row, 'offline')">下线</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 16px; justify-content: flex-end"
        @change="fetchList"
      />
    </el-card>

    <!-- 确认/编辑 对话框 -->
    <el-dialog v-model="confirmVisible" :title="confirmTitle" width="480px">
      <el-form v-if="confirmType === 'edit'" :model="editForm" label-width="90px">
        <el-form-item label="日预算(元)">
          <el-input-number v-model="editForm.budgetDay" :min="100" :max="100000" :precision="2" />
        </el-form-item>
        <el-form-item label="出价(分)">
          <el-input-number v-model="editForm.bidPrice" :min="10" :max="10000" :step="1" />
        </el-form-item>
      </el-form>
      <p v-else style="color: #666">{{ confirmType === 'approve' ? '确认上线该策略？' : '确认拒绝该策略？该策略将被下线。' }}</p>
      <template #footer>
        <el-button @click="confirmVisible = false">取消</el-button>
        <el-button :type="confirmType === 'reject' ? 'danger' : 'primary'" :loading="actionLoading" @click="doConfirm">
          确认
        </el-button>
      </template>
    </el-dialog>

    <!-- 高风险确认对话框 -->
    <el-dialog v-model="riskVisible" title="高风险策略确认" width="480px">
      <el-alert type="warning" :closable="false" style="margin-bottom: 16px">
        <template #title>该策略日预算或出价超过风险阈值，需人工审核</template>
      </el-alert>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="策略ID">{{ currentRow?.strategyId }}</el-descriptions-item>
        <el-descriptions-item label="日预算">{{ currentRow?.budgetDay }} 元</el-descriptions-item>
        <el-descriptions-item label="出价">{{ currentRow?.bidPrice }} 分</el-descriptions-item>
        <el-descriptions-item label="AI 理由">{{ currentRow?.aiReason || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="riskVisible = false">取消</el-button>
        <el-button type="danger" :loading="actionLoading" @click="doRiskConfirm('reject')">拒绝</el-button>
        <el-button type="primary" :loading="actionLoading" @click="doRiskConfirm('approve')">确认上线</el-button>
      </template>
    </el-dialog>

    <!-- 暂停/下线对话框 -->
    <el-dialog v-model="stopVisible" :title="stopType === 'pause' ? '暂停策略' : '下线策略'" width="400px">
      <p>{{ stopType === 'pause' ? '确认暂停该策略投放？' : '确认下线该策略？下线后无法恢复投放。' }}</p>
      <template #footer>
        <el-button @click="stopVisible = false">取消</el-button>
        <el-button :type="stopType === 'pause' ? 'warning' : 'danger'" :loading="actionLoading" @click="doStop">
          确认
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getStrategyList, confirmStrategy, stopStrategy, confirmRiskStrategy } from '@/api/strategy'

const userStore = useUserStore()

const loading = ref(false)
const actionLoading = ref(false)
const tableData = ref([])
const total = ref(0)

const query = reactive({ status: '', channel: '', page: 1, pageSize: 10 })

const channelMap = { douyin: '抖音', kuaishou: '快手', weibo: '微博', toutiao: '头条', baidu: '百度' }

function statusLabel(status) {
  const map = {
    pending: '待人工确认',
    risk_pending: '高风险待确认',
    running: '投放中',
    paused: '已暂停',
    offline: '已下线',
    rejected: '已拒绝',
    processing: 'AI处理中',
  }
  return map[status] || status
}

function statusTagType(status) {
  const map = {
    pending: 'warning',
    risk_pending: 'danger',
    running: 'success',
    paused: 'info',
    offline: '',
    rejected: 'danger',
    processing: 'info',
  }
  return map[status] || ''
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getStrategyList(query)
    tableData.value = res.data.records || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  query.status = ''
  query.channel = ''
  query.page = 1
  fetchList()
}

// 确认/编辑逻辑
const confirmVisible = ref(false)
const confirmType = ref('approve')
const confirmTitle = ref('')
const currentRow = ref(null)
const editForm = reactive({ budgetDay: 0, bidPrice: 0 })

function openConfirmDialog(row, type) {
  currentRow.value = row
  confirmType.value = type
  confirmTitle.value = type === 'approve' ? '确认上线策略' : type === 'edit' ? '编辑并上线策略' : '拒绝策略'
  if (type === 'edit') {
    editForm.budgetDay = row.budgetDay
    editForm.bidPrice = row.bidPrice
  }
  confirmVisible.value = true
}

async function doConfirm() {
  actionLoading.value = true
  try {
    if (confirmType.value === 'reject') {
      // 拒绝策略：调用下线接口
      await stopStrategy({
        strategyId: currentRow.value.strategyId,
        operateType: '下线',
      })
    } else {
      await confirmStrategy({
        strategyId: currentRow.value.strategyId,
        operateType: confirmType.value === 'edit' ? '编辑' : '上线',
        editData: confirmType.value === 'edit' ? { budgetDay: editForm.budgetDay, bidPrice: editForm.bidPrice } : undefined,
      })
    }
    ElMessage.success('操作成功')
    confirmVisible.value = false
    fetchList()
  } finally {
    actionLoading.value = false
  }
}

// 高风险确认
const riskVisible = ref(false)

function openRiskConfirmDialog(row, _type) {
  currentRow.value = row
  riskVisible.value = true
}

async function doRiskConfirm(action) {
  actionLoading.value = true
  try {
    // 前端 approve/reject → 后端 同意/拒绝
    const confirmResult = action === 'approve' ? '同意' : '拒绝'
    await confirmRiskStrategy({
      strategyId: currentRow.value.strategyId,
      userId: userStore.userInfo?.userId || 1,
      confirmResult,
    })
    ElMessage.success('操作成功')
    riskVisible.value = false
    fetchList()
  } finally {
    actionLoading.value = false
  }
}

// 暂停/下线
const stopVisible = ref(false)
const stopType = ref('pause')

function openStopDialog(row, type) {
  currentRow.value = row
  stopType.value = type
  stopVisible.value = true
}

async function doStop() {
  actionLoading.value = true
  try {
    // 前端 pause/offline → 后端 暂停/下线
    const operateType = stopType.value === 'pause' ? '暂停' : '下线'
    await stopStrategy({
      strategyId: currentRow.value.strategyId,
      operateType,
    })
    ElMessage.success('操作成功')
    stopVisible.value = false
    fetchList()
  } finally {
    actionLoading.value = false
  }
}

onMounted(() => fetchList())

// 暴露给父组件刷新
defineExpose({ fetchList })
</script>
