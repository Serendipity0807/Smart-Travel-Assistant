// 应用入口: 挂载 App(=后端 main.py 的角色)
// Element Plus 按需引入(阶段9): 模板里的组件由 vite 插件自动导入, 不再全量注册
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import { createApp } from 'vue'

// 基础样式(reset + CSS 变量 --el-color-*)
import 'element-plus/theme-chalk/base.css'
// ElMessage/ElMessageBox 在 script 里手动 import, 插件管不到, 样式需手动引入
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'

import App from './App.vue'
import router from './router'
import './style.css'

createApp(App).use(router).mount('#app')
