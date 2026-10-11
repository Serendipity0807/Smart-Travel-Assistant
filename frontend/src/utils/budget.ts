// 前端预算核算(行程编辑后实时重算)
// 公式与后端 app/services/budget_service.py 完全一致, 改公式时要两边同步
import type { Budget, Itinerary } from '@/types/trip'

/** 每人每天交通基准(元): 与后端 config.py 的 transport_daily_budget_per_person 一致 */
export const TRANSPORT_PER_PERSON_PER_DAY = 50

const round2 = (n: number): number => Math.round(n * 100) / 100

/** 按当前行程数据重算预算: 门票×人数 + 酒店×房间数 + 餐饮×人数 + 交通估算 */
export function recalculateBudget(it: Itinerary): Budget {
  const travelers = it.travelers
  const tickets =
    it.days.reduce((sum, d) => sum + d.spots.reduce((s, sp) => s + sp.ticket_price, 0), 0) *
    travelers
  const rooms = Math.ceil(travelers / 2)
  const hotels =
    it.days.reduce((sum, d) => sum + (d.hotel ? d.hotel.price_per_night : 0), 0) * rooms
  const dining =
    it.days.reduce((sum, d) => sum + d.meals.reduce((s, m) => s + m.price_estimate, 0), 0) *
    travelers
  const transport = TRANSPORT_PER_PERSON_PER_DAY * travelers * it.days.length

  return {
    tickets: round2(tickets),
    hotels: round2(hotels),
    dining: round2(dining),
    transport: round2(transport),
    total: round2(tickets + hotels + dining + transport),
  }
}
