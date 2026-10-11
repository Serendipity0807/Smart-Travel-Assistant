<script setup lang="ts">
// 首页: 行程规划表单
// 提交 → 后端 POST /api/trip/plan → 结果存 localStorage → 跳转 /plan
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getHealth, ITINERARY_STORAGE_KEY, planTrip, type HealthStatus } from '@/api'
import type { Preference } from '@/types/trip'

const router = useRouter()
const loading = ref(false)

// 后端健康状态(页面顶部小标签显示)
const health = ref<HealthStatus | null>(null)

const form = reactive({
  destination: '',
  preferences: [] as Preference[],
  budget: 3000,
  travelers: 2,
})
const dateRange = ref<[string, string] | null>(null)

const PREFERENCE_OPTIONS: { label: string; value: Preference }[] = [
  { label: '历史文化', value: '历史文化' },
  { label: '自然风光', value: '自然风光' },
  { label: '美食', value: '美食' },
  { label: '亲子', value: '亲子' },
  { label: '购物', value: '购物' },
  { label: '文艺', value: '文艺' },
]

onMounted(async () => {
  try {
    health.value = await getHealth()
  } catch {
    // 后端没启动, 静默处理(提交时会有错误提示)
  }
})

/** 后端三项配置齐全才算就绪 */
function allConfigured(): boolean {
  return !!(
    health.value &&
    health.value.llm_configured &&
    health.value.amap_configured &&
    health.value.unsplash_configured
  )
}

/** 字符串日期 → 天数(含首尾) */
function daysBetween(start: string, end: string): number {
  return (new Date(end).getTime() - new Date(start).getTime()) / 86400000 + 1
}

async function onSubmit() {
  if (!form.destination.trim()) {
    return
  }
  if (!dateRange.value) {
    return
  }
  const [start_date, end_date] = dateRange.value
  if (daysBetween(start_date, end_date) > 15) {
    return
  }
  loading.value = true
  try {
    const itinerary = await planTrip({
      destination: form.destination.trim(),
      start_date,
      end_date,
      preferences: form.preferences,
      budget: form.budget,
      travelers: form.travelers,
    })
    localStorage.setItem(ITINERARY_STORAGE_KEY, JSON.stringify(itinerary))
    await router.push({ name: 'plan' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <div class="status-bar">
      <el-tag v-if="health && allConfigured()" type="success" effect="light">
        后端已连接 · 服务就绪
      </el-tag>
      <el-tag v-else-if="health" type="warning" effect="light"> 后端已连接 · 配置不全 </el-tag>
      <el-tag v-else type="info" effect="light"> 后端未连接 </el-tag>
    </div>

    <el-card class="form-card">
      <template #header>
        <span class="card-title">规划你的旅程</span>
      </template>

      <el-form label-width="90px" @submit.prevent="onSubmit">
        <el-form-item label="目的地" required>
          <el-input
            v-model="form.destination"
            placeholder="如: 北京"
            maxlength="50"
            clearable
          />
        </el-form-item>

        <el-form-item label="出行日期" required>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="出发日期"
            end-placeholder="返程日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="旅行偏好">
          <el-checkbox-group v-model="form.preferences">
            <el-checkbox v-for="opt in PREFERENCE_OPTIONS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>

        <el-form-item label="总预算(元)">
          <el-input-number v-model="form.budget" :min="100" :step="100" />
        </el-form-item>

        <el-form-item label="出行人数">
          <el-input-number v-model="form.travelers" :min="1" :max="20" />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            native-type="submit"
            :loading="loading"
            :disabled="!form.destination.trim() || !dateRange"
          >
            {{ loading ? '规划中, 约需 1-2 分钟…' : '生成行程' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.status-bar {
  margin-bottom: 16px;
}

.form-card {
  max-width: 640px;
}

.card-title {
  font-weight: 600;
}
</style>
