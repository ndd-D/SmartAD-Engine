<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px; border-radius: 8px">
      <el-form :model="query" inline>
        <el-form-item label="告警状态">
          <el-select v-model="query.status" placeholder="全部" clearable style="width: 130px">
            <el-option label="未处理" value="active" />
            <el-option label="已确认" value="confirmed" />
          </el-select>
        </el-form-item>
        <el-form-item label="告警级别">
          <el-select v-model="query.alertLevel" placeholder="全部" clearable style="width: 120px">
            <el-option label="信息" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" style="border-radius: 8px">
      <el-table v-loading="loading" :data="tableData" stripe style="width: 100%">
        <el-table-column prop="alertId" label="告警ID" width="180" />
        <el-table-column prop="strategyId" label="策略ID" width="180" />
        <el-table-column prop="alertType" label="告警类型" width="130">
          <template #default="{ row }">{{ alertTypeLabel(row.alertType) }}</template>
        </el-table-column>
        <el-table-column prop="alertLevel" label="级别" width="100">
          <template #default="{ row }">
            <el-tag :type="levelTagType(row.alertLevel)">{{ levelLabel(row.alertLevel) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="alertMessage" label="告警信息" min-width="200" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'danger' : 'info'">
              {{ row.status === 'active' ? '未处理' : '已确认' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="触发时间" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'active'"
              size="small"
              type="primary"
              @click="handleConfirm(row)"
            >
              确认
            </el-button>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getAlertList, confirmAlert } from '@/api/alert'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const query = reactive({ status: '', alertLevel: '', page: 1, pageSize: 10 })

function alertTypeLabel(type) {
  const map = {
    low_ctr: 'CTR过低',
    low_roi: 'ROI过低',
    budget_overrun: '预算超支',
    no_conversion: '无转化',
    abnormal_cost: '消耗异常',
    normal: '正常',
  }
  return map[type] || type
}

function levelLabel(level) {
  return { info: '信息', warning: '警告', critical: '严重' }[level] || level
}

function levelTagType(level) {
  return { info: 'info', warning: 'warning', critical: 'danger' }[level] || ''
}

async function fetchList() {
  loading.value = true
  try {
    const res = await getAlertList(query)
    tableData.value = res.data.records || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

async function handleConfirm(row) {
  try {
    await confirmAlert(row.alertId)
    ElMessage.success('告警已确认')
    fetchList()
  } catch {}
}

function resetQuery() {
  Object.assign(query, { status: '', alertLevel: '', page: 1 })
  fetchList()
}

onMounted(() => fetchList())
</script>
