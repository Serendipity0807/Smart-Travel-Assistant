// 应用入口: 挂载 App(=后端 main.py 的角色)
// Element Plus 全量引入(部署前可优化为按需导入, 阶段9处理)
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import './style.css'

createApp(App).use(ElementPlus, { locale: zhCn }).use(router).mount('#app')
