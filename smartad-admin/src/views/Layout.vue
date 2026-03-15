<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="aside">
      <div class="logo">
        <span class="logo-text">SmartAD Engine</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#1a237e"
        text-color="rgba(255,255,255,0.75)"
        active-text-color="#fff"
        router
      >
        <el-menu-item index="/strategy">
          <el-icon><DataLine /></el-icon>
          <span>策略管理</span>
        </el-menu-item>
        <el-menu-item index="/report">
          <el-icon><TrendCharts /></el-icon>
          <span>投放报表</span>
        </el-menu-item>
        <el-menu-item index="/alert">
          <el-icon><Bell /></el-icon>
          <span>
            告警管理
            <el-badge v-if="alertCount > 0" :value="alertCount" class="alert-badge" />
          </span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶栏 -->
      <el-header class="header">
        <div class="header-right">
          <span class="username">{{ userStore.userInfo?.username }}</span>
          <el-button text type="danger" @click="handleLogout">退出</el-button>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="main-content">
        <!-- 指令输入框（全局固定显示） -->
        <CommandInput @submitted="onCommandSubmitted" />
        <router-view :key="refreshKey" />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { getAlertList } from '@/api/alert'
import CommandInput from '@/components/CommandInput.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const alertCount = ref(0)
const refreshKey = ref(0)

const activeMenu = computed(() => route.path)

async function fetchAlertCount() {
  try {
    const res = await getAlertList({ status: 'active', pageSize: 1 })
    alertCount.value = res.data?.total || 0
  } catch {}
}

function handleLogout() {
  userStore.logout()
  router.push('/login')
}

function onCommandSubmitted() {
  // 指令提交后刷新策略列表
  refreshKey.value++
}

onMounted(() => {
  fetchAlertCount()
  // 每60秒刷新告警数量
  setInterval(fetchAlertCount, 60000)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.aside {
  background-color: #1a237e;
  display: flex;
  flex-direction: column;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo-text {
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 1px;
}
.el-menu {
  border-right: none;
  flex: 1;
}
.header {
  background: #fff;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 24px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.username {
  font-size: 14px;
  color: #333;
}
.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
.alert-badge {
  margin-left: 6px;
  vertical-align: middle;
}
</style>
