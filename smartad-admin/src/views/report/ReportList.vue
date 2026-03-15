<template>
  <div>
    <el-card shadow="never" style="margin-bottom: 16px; border-radius: 8px">
      <el-form :model="query" inline>
        <el-form-item label="策略ID">
          <el-input v-model="query.strategyId" placeholder="输入策略ID" clearable style="width: 180px" />
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
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchList">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="never" style="border-radius: 8px">
      <el-table v-loading="loading" :data="tableData" stripe style="width: 100%">
        <el-table-column prop="strategyId" label="策略ID" width="180" />
        <el-table-column prop="crowdTag" label="人群" width="130">
          <template #default="{ row }"><el-tag type="info">{{ row.crowdTag }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="channel" label="渠道" width="100">
          <template #default="{ row }"><el-tag>{{ channelMap[row.channel] || row.channel }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="reportDate" label="日期" width="120" />
        <el-table-column prop="impressions" label="曝光量" width="110" align="right" />
        <el-table-column prop="clicks" label="点击量" width="100" align="right" />
        <el-table-column label="CTR" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.ctr < 0.005 ? '#f56c6c' : '#67c23a' }">
              {{ (row.ctr * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="cost" label="消耗(元)" width="110" align="right">
          <template #default="{ row }">{{ row.cost?.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="conversions" label="转化量" width="100" align="right" />
        <el-table-column label="ROI" width="90" align="right">
          <template #default="{ row }">
            <span :style="{ color: row.roi < 1 ? '#f56c6c' : '#67c23a' }">
              {{ row.roi?.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" width="170" />
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
import { getReportList } from '@/api/report'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const dateRange = ref([])
const query = reactive({ strategyId: '', channel: '', startDate: '', endDate: '', page: 1, pageSize: 10 })

const channelMap = { douyin: '抖音', kuaishou: '快手', weibo: '微博', toutiao: '头条', baidu: '百度' }

async function fetchList() {
  if (dateRange.value?.length === 2) {
    query.startDate = dateRange.value[0]
    query.endDate = dateRange.value[1]
  } else {
    query.startDate = ''
    query.endDate = ''
  }
  loading.value = true
  try {
    const res = await getReportList(query)
    tableData.value = res.data.records || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { strategyId: '', channel: '', startDate: '', endDate: '', page: 1 })
  dateRange.value = []
  fetchList()
}

onMounted(() => fetchList())
</script>
