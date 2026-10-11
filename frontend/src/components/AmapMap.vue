<script setup lang="ts">
// 高德地图组件: 显示指定天的景点标记(按游览顺序编号) + 路线连线
// 用法: <AmapMap :days="itinerary.days" :active-day="activeDay" />
// 注意: 高德官方 loader 不提供 TS 类型, 相关变量用 any 并注释说明
import AMapLoader from '@amap/amap-jsapi-loader'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { DayPlan, Spot } from '@/types/trip'

const props = defineProps<{
  days: DayPlan[]
  activeDay: number // 第几天(从 1 开始)
}>()

const containerRef = ref<HTMLDivElement | null>(null)

// 高德 SDK 与地图实例(类型为 any: 官方 loader 没有类型声明)
let AMap: any = null
let map: any = null
let infoWindow: any = null
const markers: any[] = []
let polyline: any = null

onMounted(async () => {
  // 安全密钥: 必须在创建地图之前挂到 window 上(高德官方要求)
  ;(window as any)._AMapSecurityConfig = {
    securityJsCode: import.meta.env.VITE_AMAP_SECURITY_CODE,
  }
  AMap = await AMapLoader.load({
    key: import.meta.env.VITE_AMAP_JS_KEY,
    version: '2.0',
  })
  if (!containerRef.value) return
  map = new AMap.Map(containerRef.value, { zoom: 12, viewMode: '2D' })
  infoWindow = new AMap.InfoWindow({ anchor: 'bottom-center', offset: new AMap.Pixel(0, -32) })
  drawDay(props.activeDay)
})

onBeforeUnmount(() => {
  // 组件销毁时释放地图资源(SPA 反复进出页面不泄漏)
  map?.destroy()
  map = null
})

// 切换天数时重画: 清掉旧标记和路线, 画新的一天
watch(
  () => props.activeDay,
  (day) => drawDay(day),
)

// 行程被编辑(增删景点/调序)时重画当前天: 阶段7 行程编辑联动
watch(
  () => props.days,
  () => drawDay(props.activeDay),
  { deep: true },
)

function drawDay(day: number) {
  if (!map || !AMap) return
  clearOverlays()
  const plan = props.days.find((d) => d.day === day)
  if (!plan || plan.spots.length === 0) return

  const positions = plan.spots.map((s) => [s.lng, s.lat] as [number, number])

  plan.spots.forEach((spot, i) => {
    const marker = new AMap.Marker({
      position: positions[i],
      title: spot.name,
      // 数字编号标记, 样式在全局 style.css(动态 HTML 不受 scoped 约束)
      content: `<div class="amap-spot-marker">${i + 1}</div>`,
      zIndex: 100 + i,
    })
    marker.on('click', () => openInfo(spot))
    marker.addTo(map)
    markers.push(marker)
  })

  // 游览路线: 按数组顺序连线, 带方向箭头
  polyline = new AMap.Polyline({
    path: positions,
    strokeColor: '#409eff',
    strokeWeight: 5,
    strokeOpacity: 0.85,
    lineJoin: 'round',
    showDir: true,
  })
  polyline.addTo(map)

  // 视图自动缩放到覆盖全部标记(四周留 80px 边距)
  map.setFitView([...markers, polyline], false, [80, 80, 80, 80])
}

function clearOverlays() {
  for (const m of markers) m.remove()
  markers.length = 0
  polyline?.remove()
  polyline = null
  infoWindow?.close()
}

function openInfo(spot: Spot) {
  const price = spot.ticket_price > 0 ? `门票 ¥${spot.ticket_price}` : '免费'
  const content = `
    <div class="amap-info">
      <img src="${spot.image_url}" class="amap-info-img" onerror="this.style.display='none'" />
      <div class="amap-info-body">
        <div class="amap-info-name">${spot.name}</div>
        <div class="amap-info-meta">${price} · 建议停留 ${spot.stay_minutes} 分钟</div>
        <div class="amap-info-desc">${spot.description}</div>
      </div>
    </div>`
  infoWindow.setContent(content)
  infoWindow.open(map, [spot.lng, spot.lat])
}
</script>

<template>
  <div ref="containerRef" class="amap-container" />
</template>

<style scoped>
.amap-container {
  width: 100%;
  height: 480px;
  border-radius: 8px;
}
</style>
