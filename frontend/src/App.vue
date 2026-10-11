<script setup lang="ts">
// 根组件: 顶部导航 + 页面出口(router-view)
// el-config-provider 提供 Element Plus 中文 locale(阶段9按需引入后替代 app.use 全局配置)
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <el-config-provider :locale="zhCn">
    <div class="app">
      <header class="app-header">
        <div class="app-header-inner">
          <span class="app-title">🏔️ 智能旅游助手</span>
          <el-tag v-if="route.path === '/plan'" type="success" effect="plain">行程规划结果</el-tag>
        </div>
      </header>
      <main class="app-main">
        <router-view />
      </main>
    </div>
  </el-config-provider>
</template>

<style scoped>
.app-header {
  background: #fff;
  border-bottom: 1px solid var(--el-border-color-light);
  position: sticky;
  top: 0;
  z-index: 10;
}

.app-header-inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 14px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.app-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--el-color-primary);
}

.app-main {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 20px;
}
</style>
