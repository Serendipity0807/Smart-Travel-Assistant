/// <reference types="vite/client" />

// import.meta.env 的类型声明: 所有 VITE_ 开头的环境变量在这里登记
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_AMAP_JS_KEY: string
  readonly VITE_AMAP_SECURITY_CODE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
