// API 封装: axios 实例 + 统一错误处理
// 与后端约定: 业务接口返回 {code, message, data}, code=0 成功
import axios from 'axios'
import { ElMessage } from 'element-plus'

import type { CandidateSpot, Itinerary, TripRequest } from '@/types/trip'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  // 行程规划全流程(多轮 LLM 调用)约 1-4 分钟: LLM 响应波动大, 7 天行程实测最坏 3.5 分钟,
  // 给足余量(与 nginx 的 proxy_read_timeout 保持一致, 改这里时两边同步)
  timeout: 600000,
})

// 响应拦截器: 统一拆包 + 统一错误提示
client.interceptors.response.use(
  (resp) => {
    const body = resp.data
    // 带 {code, message, data} 包装的业务接口
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) return body.data
      ElMessage.error(body.message || '请求失败')
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    // 无包装的接口(如 /api/health)原样返回
    return body
  },
  (err) => {
    const msg: string = err.response?.data?.message || err.message || '网络错误'
    ElMessage.error(msg)
    return Promise.reject(err)
  },
)

/** 后端健康状态(三个密钥是否已配置) */
export interface HealthStatus {
  status: string
  llm_configured: boolean
  amap_configured: boolean
  unsplash_configured: boolean
}

/** 行程结果在 localStorage 里的键(首页写入, 结果页读取) */
export const ITINERARY_STORAGE_KEY = 'last-itinerary'

/** GET /api/health */
export function getHealth(): Promise<HealthStatus> {
  return client.get('/api/health')
}

/** POST /api/trip/plan 生成行程 */
export function planTrip(request: TripRequest): Promise<Itinerary> {
  return client.post('/api/trip/plan', request)
}

/** GET /api/trip/spots/search 搜索候选景点(阶段7"添加景点") */
export function searchSpots(keyword: string, city: string): Promise<CandidateSpot[]> {
  return client.get('/api/trip/spots/search', { params: { keyword, city } })
}
