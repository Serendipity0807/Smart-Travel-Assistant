// 行程导出工具(阶段8): 图片 = PNG 长图, PDF = A4 分页
// 原理: html2canvas 把行程根容器(#export-area)截成整张 canvas
//   - 图片: canvas 直接下载 PNG
//   - PDF: 按 A4 内容区比例把长图切成多段, 每段一页插入 jsPDF
// 约定: onclone 里移除 #map-card(高德 canvas 无法被复制, 强行截图会空白或报错;
//       地图信息在每日卡片里都有, 不损失内容)和 .footer-actions(操作按钮不进导出)
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'

const EXPORT_ROOT_ID = 'export-area'

// A4 竖版(mm) + 页边距
const A4_WIDTH_MM = 210
const A4_HEIGHT_MM = 297
const MARGIN_MM = 8

const CONTENT_WIDTH_MM = A4_WIDTH_MM - MARGIN_MM * 2
const CONTENT_HEIGHT_MM = A4_HEIGHT_MM - MARGIN_MM * 2

/** 把导出区域截成 canvas(scale=2 保证打印清晰度) */
async function captureRoot(): Promise<HTMLCanvasElement> {
  const el = document.getElementById(EXPORT_ROOT_ID)
  if (!el) throw new Error('未找到导出区域')
  await waitForImages(el)
  return html2canvas(el, {
    scale: 2,
    useCORS: true, // Unsplash 图片跨域加载
    backgroundColor: '#ffffff',
    logging: false,
    // 在克隆文档里删除不参与导出的元素, 不影响真实页面 DOM
    onclone: (_doc, clonedEl) => {
      clonedEl.querySelector('#map-card')?.remove()
      clonedEl.querySelector('.footer-actions')?.remove()
    },
  })
}

/** 尽力等区域内的图片加载完(懒加载未触发/网络慢时减少灰块, 最长 5s 不阻塞导出) */
async function waitForImages(el: HTMLElement): Promise<void> {
  const imgs = Array.from(el.querySelectorAll('img')).filter((i) => i.src)
  await Promise.all(
    imgs.map(
      (img) =>
        new Promise<void>((resolve) => {
          const done = () => resolve()
          const timer = setTimeout(done, 5000)
          if (img.complete) {
            clearTimeout(timer)
            done()
            return
          }
          img.onload = () => {
            clearTimeout(timer)
            done()
          }
          img.onerror = () => {
            clearTimeout(timer)
            done()
          }
        }),
    ),
  )
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/** 导出完整行程长图(PNG) */
export async function exportImage(baseName: string): Promise<void> {
  const canvas = await captureRoot()
  await new Promise<void>((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (!blob) {
        reject(new Error('生成图片失败'))
        return
      }
      downloadBlob(blob, `${baseName}-行程.png`)
      resolve()
    }, 'image/png')
  })
}

/** 导出 PDF: 长图按 A4 内容区切块, 每块一页 */
export async function exportPdf(baseName: string): Promise<void> {
  const canvas = await captureRoot()
  const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })

  // 整图按 A4 内容宽度等比缩放后的高度(mm), 超过一页就分页
  const scaledHeightMm = (canvas.height / canvas.width) * CONTENT_WIDTH_MM
  const pages = Math.max(1, Math.ceil(scaledHeightMm / CONTENT_HEIGHT_MM))
  // 每页在源 canvas 上占用的像素高(平均切分, 余数并入末页)
  const sliceHeightPx = Math.ceil(canvas.height / pages)

  for (let i = 0; i < pages; i++) {
    if (i > 0) pdf.addPage()
    const slice = document.createElement('canvas')
    slice.width = canvas.width
    slice.height = sliceHeightPx
    const ctx = slice.getContext('2d')
    if (!ctx) throw new Error('创建分页画布失败')
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, slice.width, slice.height)
    ctx.drawImage(canvas, 0, i * sliceHeightPx, canvas.width, sliceHeightPx, 0, 0, canvas.width, sliceHeightPx)
    // JPEG 质量 0.92: 体积远小于 PNG, 行程以文字为主观感无损
    const imgData = slice.toDataURL('image/jpeg', 0.92)
    const imgHeightMm = (sliceHeightPx / canvas.width) * CONTENT_WIDTH_MM
    pdf.addImage(imgData, 'JPEG', MARGIN_MM, MARGIN_MM, CONTENT_WIDTH_MM, imgHeightMm)
  }
  pdf.save(`${baseName}-行程.pdf`)
}
