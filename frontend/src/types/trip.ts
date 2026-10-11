// 前后端共用的数据结构: 与后端 app/schemas/request.py 和 itinerary.py 一一对应
export type Preference = '历史文化' | '自然风光' | '美食' | '亲子' | '购物' | '文艺'

/** 行程规划请求(前端表单提交) */
export interface TripRequest {
  destination: string
  start_date: string // "YYYY-MM-DD"
  end_date: string
  preferences: Preference[]
  budget: number
  travelers: number
}

/** 景点 */
export interface Spot {
  name: string
  lng: number
  lat: number
  period: 'morning' | 'afternoon' | 'evening'
  address: string
  ticket_price: number
  stay_minutes: number
  description: string
  image_url: string
}

/** 一餐 */
export interface Meal {
  period: string
  name: string
  price_estimate: number
}

/** 酒店 */
export interface Hotel {
  name: string
  lng: number
  lat: number
  price_per_night: number
  rating: number
  address: string
}

/** 预算明细 */
export interface Budget {
  tickets: number
  hotels: number
  dining: number
  transport: number
  total: number // 后端 @property 计算的, 序列化后带出来
}

/** 单日行程 */
export interface DayPlan {
  day: number
  date: string
  weather: string
  spots: Spot[]
  meals: Meal[]
  hotel: Hotel | null
}

/** 完整行程 */
export interface Itinerary {
  destination: string
  start_date: string
  end_date: string
  preferences: string[]
  days: DayPlan[]
  budget: Budget
  created_at: string
  // 阶段6新增: 后端业务层核算时回填
  travelers: number // 出行人数
  budget_limit: number // 用户设定的总预算(超支提示用)
}

/** 候选景点(阶段7"添加景点"搜索返回) */
export interface CandidateSpot {
  name: string
  lng: number
  lat: number
  address: string
  description: string
}
