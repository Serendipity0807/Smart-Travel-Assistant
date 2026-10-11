<script setup lang="ts">
// 行程结果页: 展示完整的每日行程(景点/餐饮/酒店/预算)
// 数据来自 localStorage(首页提交成功后写入), 直接打开本页会跳回首页
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { ITINERARY_STORAGE_KEY, searchSpots } from '@/api'
import AmapMap from '@/components/AmapMap.vue'
import type { CandidateSpot, DayPlan, Itinerary } from '@/types/trip'
import { recalculateBudget } from '@/utils/budget'

const router = useRouter()
const itinerary = ref<Itinerary | null>(null)

// 地图当前显示第几天(与下方每日卡片对应)
const activeDay = ref(1)

const PERIOD_LABEL: Record<string, string> = {
  morning: '上午',
  afternoon: '下午',
  evening: '晚上',
}

onMounted(() => {
  const raw = localStorage.getItem(ITINERARY_STORAGE_KEY)
  if (!raw) {
    router.replace({ name: 'home' })
    return
  }
  try {
    itinerary.value = JSON.parse(raw) as Itinerary
  } catch {
    router.replace({ name: 'home' })
  }
})

function goHome() {
  router.push({ name: 'home' })
}

function formatPrice(n: number): string {
  return `¥${n.toLocaleString('zh-CN')}`
}

function dayDate(d: DayPlan): string {
  const [, month, day] = d.date.split('-')
  return `${month}月${day}日`
}

/** 预算四项的占比数据(进度条用) */
const budgetItems = computed(() => {
  if (!itinerary.value) return []
  const b = itinerary.value.budget
  const total = b.total || 1 // 防除零
  return [
    { label: '门票', value: b.tickets, percent: Math.round((b.tickets / total) * 100), color: '#409eff' },
    { label: '酒店', value: b.hotels, percent: Math.round((b.hotels / total) * 100), color: '#67c23a' },
    { label: '餐饮', value: b.dining, percent: Math.round((b.dining / total) * 100), color: '#e6a23c' },
    { label: '交通', value: b.transport, percent: Math.round((b.transport / total) * 100), color: '#f56c6c' },
  ]
})

// ===== 行程编辑(阶段7): 增删调序景点, 每次编辑重算预算并写回 localStorage =====

function saveToStorage() {
  if (itinerary.value) {
    localStorage.setItem(ITINERARY_STORAGE_KEY, JSON.stringify(itinerary.value))
  }
}

/** 编辑后的统一收尾: 预算重算(复用阶段6公式) + 持久化(刷新不丢) */
function afterEdit() {
  if (!itinerary.value) return
  itinerary.value.budget = recalculateBudget(itinerary.value)
  saveToStorage()
}

async function removeSpot(day: DayPlan, index: number) {
  try {
    await ElMessageBox.confirm(`确定删除景点「${day.spots[index].name}」吗?`, '删除景点', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return // 用户取消
  }
  day.spots.splice(index, 1)
  afterEdit()
}

function moveSpot(day: DayPlan, index: number, delta: -1 | 1) {
  const target = index + delta
  if (target < 0 || target >= day.spots.length) return
  const [spot] = day.spots.splice(index, 1)
  day.spots.splice(target, 0, spot)
  afterEdit()
}

// ===== 添加景点(阶段7): 搜索高德 POI → 选候选 → 补门票/停留 → 追加到当天 =====

const addDialogVisible = ref(false)
const addTargetDay = ref<DayPlan | null>(null)
const searchKeyword = ref('')
const searching = ref(false)
const candidates = ref<CandidateSpot[]>([])
const selected = ref<CandidateSpot | null>(null)
const newTicketPrice = ref(0)
const newStayMinutes = ref(120)

function openAddDialog(day: DayPlan) {
  addTargetDay.value = day
  addDialogVisible.value = true
  searchKeyword.value = ''
  candidates.value = []
  selected.value = null
  newTicketPrice.value = 0
  newStayMinutes.value = 120
}

async function doSearch() {
  if (!searchKeyword.value.trim() || !itinerary.value) return
  searching.value = true
  try {
    candidates.value = await searchSpots(searchKeyword.value.trim(), itinerary.value.destination)
    selected.value = null
  } finally {
    searching.value = false
  }
}

function pickCandidate(spot: CandidateSpot) {
  selected.value = spot
}

function confirmAdd() {
  if (!addTargetDay.value || !selected.value) return
  addTargetDay.value.spots.push({
    name: selected.value.name,
    lng: selected.value.lng,
    lat: selected.value.lat,
    period: 'afternoon',
    address: selected.value.address,
    ticket_price: newTicketPrice.value,
    stay_minutes: newStayMinutes.value,
    description: selected.value.description,
    image_url: '', // 手添景点无配图, 前端已做无图兜底
  })
  addDialogVisible.value = false
  afterEdit()
}

// ===== 导出(阶段8): 图片/PDF =====
// 地图卡片在截图克隆里被移除(见 utils/export.ts 的 onclone):
// 高德地图用 canvas 渲染, html2canvas 复制不了, 强行截图会空白或报错;
// 地图信息(景点编号/路线)在每日卡片里都有, 导出不损失内容
const exporting = ref<'image' | 'pdf' | null>(null)

async function doExport(kind: 'image' | 'pdf') {
  if (!itinerary.value) return
  exporting.value = kind
  try {
    // 动态加载导出库(html2canvas+jspdf 约 400KB): 点击导出时才下载, 不拖慢首屏
    const { exportImage, exportPdf } = await import('@/utils/export')
    const name = itinerary.value.destination
    if (kind === 'image') await exportImage(name)
    else await exportPdf(name)
    ElMessage.success(kind === 'image' ? '行程图片已下载' : '行程 PDF 已下载')
  } catch (err) {
    console.error('导出失败', err)
    ElMessage.error('导出失败, 请重试')
  } finally {
    exporting.value = null
  }
}
</script>

<template>
  <div v-if="itinerary" id="export-area">
    <el-page-header class="back-header" @back="goHome">
      <template #content>
        <span class="dest-title">{{ itinerary.destination }} · 行程规划</span>
      </template>
    </el-page-header>

    <!-- 导出区域(阶段8): 根容器整体截图, 地图卡片与底部按钮在截图克隆里被移除 -->
    <!-- 行程总览 -->
    <el-card class="overview-card">
        <template #header>
          <div class="overview-header">
            <span>行程总览</span>
            <div class="export-actions">
              <el-button size="small" :loading="exporting === 'image'" @click="doExport('image')">
                导出图片
              </el-button>
              <el-button
                size="small"
                type="primary"
                :loading="exporting === 'pdf'"
                @click="doExport('pdf')"
              >
                导出 PDF
              </el-button>
            </div>
          </div>
        </template>
      <!-- 超支警告(阶段6: 后端核算出的真实预算 vs 用户设定预算) -->
      <el-alert
        v-if="itinerary.budget_limit > 0 && itinerary.budget.total > itinerary.budget_limit"
        type="error"
        :closable="false"
        show-icon
        class="over-budget-alert"
        :title="`核算总额 ${formatPrice(itinerary.budget.total)} 超出你的预算 ${formatPrice(itinerary.budget_limit)}, 可回到首页调整预算重新规划`"
      />
      <el-descriptions :column="3" border>
        <el-descriptions-item label="目的地">{{ itinerary.destination }}</el-descriptions-item>
        <el-descriptions-item label="日期">
          {{ itinerary.start_date }} ~ {{ itinerary.end_date }}
        </el-descriptions-item>
        <el-descriptions-item label="天数">{{ itinerary.days.length }} 天</el-descriptions-item>
        <el-descriptions-item label="门票">
          {{ formatPrice(itinerary.budget.tickets) }}
        </el-descriptions-item>
        <el-descriptions-item label="酒店">
          {{ formatPrice(itinerary.budget.hotels) }}
        </el-descriptions-item>
        <el-descriptions-item label="餐饮">
          {{ formatPrice(itinerary.budget.dining) }}
        </el-descriptions-item>
        <el-descriptions-item label="交通">
          {{ formatPrice(itinerary.budget.transport) }}
        </el-descriptions-item>
        <el-descriptions-item label="总预算" :span="2">
          <b class="total-price">{{ formatPrice(itinerary.budget.total) }}</b>
          <span v-if="itinerary.travelers > 0" class="per-person">
            · 人均 {{ formatPrice(itinerary.budget.total / itinerary.travelers) }}
          </span>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 四项占比(阶段6) -->
      <div class="budget-bars">
        <div v-for="item in budgetItems" :key="item.label" class="budget-bar-item">
          <span class="budget-bar-label">{{ item.label }}</span>
          <el-progress
            :percentage="item.percent"
            :color="item.color"
            :stroke-width="10"
            class="budget-bar"
          />
          <span class="budget-bar-value">{{ formatPrice(item.value) }}</span>
        </div>
      </div>
    </el-card>

    <!-- 行程地图: 按天切换显示景点标记与路线 -->
    <el-card id="map-card" class="map-card">
      <template #header>
        <div class="map-header">
          <span>🗺️ 行程地图</span>
          <el-radio-group v-model="activeDay" size="small">
            <el-radio-button v-for="d in itinerary.days" :key="d.day" :value="d.day">
              第 {{ d.day }} 天
            </el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <AmapMap :days="itinerary.days" :active-day="activeDay" />
    </el-card>

    <!-- 每日行程 -->
    <el-card v-for="d in itinerary.days" :key="d.day" class="day-card">
      <template #header>
        <div class="day-header">
          <span class="day-title">第 {{ d.day }} 天 · {{ dayDate(d) }}</span>
          <div class="day-header-actions">
            <el-tag v-if="d.weather" size="small" type="info" effect="plain">
              {{ d.weather }}
            </el-tag>
            <el-button size="small" type="primary" plain @click="openAddDialog(d)">
              + 添加景点
            </el-button>
          </div>
        </div>
      </template>

      <!-- 景点 -->
      <div v-for="(spot, i) in d.spots" :key="i" class="spot-item">
        <el-image
          v-if="spot.image_url"
          :src="spot.image_url"
          fit="cover"
          class="spot-image"
          lazy
        />
        <div class="spot-info">
          <div class="spot-name-row">
            <el-tag size="small" :type="i === 0 ? 'primary' : 'info'" effect="plain">
              {{ PERIOD_LABEL[spot.period] || spot.period }}
            </el-tag>
            <span class="spot-name">{{ spot.name }}</span>
            <span class="spot-price">{{ spot.ticket_price > 0 ? `门票 ${formatPrice(spot.ticket_price)}` : '免费' }}</span>
          </div>
          <div class="spot-meta">
            建议停留 {{ spot.stay_minutes }} 分钟
            <span v-if="spot.address"> · {{ spot.address }}</span>
          </div>
          <div v-if="spot.description" class="spot-desc">{{ spot.description }}</div>
          <div class="spot-actions">
            <el-button size="small" text @click="moveSpot(d, i, -1)" :disabled="i === 0">
              ↑ 上移
            </el-button>
            <el-button
              size="small"
              text
              @click="moveSpot(d, i, 1)"
              :disabled="i === d.spots.length - 1"
            >
              ↓ 下移
            </el-button>
            <el-button size="small" text type="danger" @click="removeSpot(d, i)"> 删除 </el-button>
          </div>
        </div>
      </div>

      <!-- 餐饮 -->
      <div v-if="d.meals.length" class="meal-row">
        <span v-for="m in d.meals" :key="m.name" class="meal-chip">
          🍽️ {{ m.period }}: {{ m.name }}
          <span class="meal-price">{{ formatPrice(m.price_estimate) }}/人</span>
        </span>
      </div>

      <!-- 酒店 -->
      <div v-if="d.hotel" class="hotel-row">
        🏨 {{ d.hotel.name }}
        <el-rate :model-value="d.hotel.rating" disabled size="small" class="hotel-rate" />
        <span class="hotel-price">{{ formatPrice(d.hotel.price_per_night) }}/晚</span>
        <span v-if="d.hotel.address" class="hotel-addr"> · {{ d.hotel.address }}</span>
      </div>
    </el-card>

    <div class="footer-actions">
      <el-button type="primary" @click="goHome">再规划一个</el-button>
    </div>

    <!-- 添加景点对话框(阶段7): 搜索 → 选候选 → 补门票/停留 → 追加 -->
    <el-dialog v-model="addDialogVisible" title="添加景点" width="560px">
      <div class="search-row">
        <el-input
          v-model="searchKeyword"
          placeholder="输入景点关键词, 如: 西湖"
          clearable
          @keyup.enter="doSearch"
        />
        <el-button type="primary" :loading="searching" @click="doSearch">搜索</el-button>
      </div>

      <div v-if="candidates.length" class="candidate-list">
        <div
          v-for="c in candidates"
          :key="`${c.name}-${c.lng}-${c.lat}`"
          class="candidate-item"
          :class="{ selected: selected === c }"
          @click="pickCandidate(c)"
        >
          <div class="candidate-name">{{ c.name }}</div>
          <div v-if="c.address" class="candidate-addr">{{ c.address }}</div>
        </div>
      </div>
      <el-empty
        v-else-if="!searching"
        description="搜索景点后从候选列表中选择"
        :image-size="60"
      />

      <template v-if="selected">
        <el-divider />
        <div class="add-form">
          <div class="add-form-title">已选: {{ selected.name }}, 补充信息:</div>
          <el-form label-width="110px">
            <el-form-item label="门票(元/人)">
              <el-input-number v-model="newTicketPrice" :min="0" :step="5" />
            </el-form-item>
            <el-form-item label="停留(分钟)">
              <el-input-number v-model="newStayMinutes" :min="30" :step="30" />
            </el-form-item>
          </el-form>
        </div>
      </template>

      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!selected" @click="confirmAdd">添加到行程</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.back-header {
  margin-bottom: 16px;
}

.dest-title {
  font-size: 18px;
  font-weight: 600;
}

.overview-card {
  margin-bottom: 16px;
}

.overview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.export-actions {
  display: flex;
  gap: 8px;
}

.map-card {
  margin-bottom: 16px;
}

.map-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.total-price {
  color: var(--el-color-danger);
  font-size: 16px;
}

.per-person {
  color: #909399;
  font-size: 13px;
  margin-left: 6px;
}

.over-budget-alert {
  margin-bottom: 12px;
}

.budget-bars {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 24px;
}

.budget-bar-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.budget-bar-label {
  width: 32px;
  color: #606266;
  font-size: 13px;
  flex-shrink: 0;
}

.budget-bar {
  flex: 1;
}

.budget-bar-value {
  width: 90px;
  text-align: right;
  color: #909399;
  font-size: 13px;
  flex-shrink: 0;
}

.day-card {
  margin-bottom: 16px;
}

.day-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.day-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.day-title {
  font-weight: 600;
}

.spot-item {
  display: flex;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed var(--el-border-color-lighter);
}

.spot-item:last-of-type {
  border-bottom: none;
}

.spot-image {
  width: 120px;
  height: 80px;
  border-radius: 6px;
  flex-shrink: 0;
}

.spot-info {
  flex: 1;
}

.spot-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spot-name {
  font-weight: 600;
}

.spot-price {
  color: var(--el-color-warning);
  font-size: 13px;
}

.spot-meta {
  color: #909399;
  font-size: 13px;
  margin-top: 4px;
}

.spot-desc {
  color: #606266;
  font-size: 13px;
  margin-top: 4px;
  line-height: 1.5;
}

.spot-actions {
  display: flex;
  gap: 4px;
  margin-top: 6px;
}

/* 添加景点对话框 */
.search-row {
  display: flex;
  gap: 8px;
}

.candidate-list {
  margin-top: 12px;
  max-height: 260px;
  overflow-y: auto;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
}

.candidate-item {
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.candidate-item:last-child {
  border-bottom: none;
}

.candidate-item:hover {
  background: var(--el-fill-color-light);
}

.candidate-item.selected {
  background: var(--el-color-primary-light-9);
}

.candidate-name {
  font-weight: 600;
  font-size: 14px;
}

.candidate-addr {
  color: #909399;
  font-size: 12px;
  margin-top: 2px;
}

.add-form-title {
  font-weight: 600;
  margin-bottom: 12px;
}

.meal-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 0;
}

.meal-chip {
  background: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 13px;
}

.meal-price {
  color: #909399;
}

.hotel-row {
  padding: 10px 0;
  font-size: 14px;
}

.hotel-rate {
  display: inline-flex;
  margin: 0 8px;
  vertical-align: middle;
}

.hotel-price {
  color: var(--el-color-warning);
}

.hotel-addr {
  color: #909399;
  font-size: 13px;
}

.footer-actions {
  text-align: center;
  padding: 8px 0 24px;
}
</style>
