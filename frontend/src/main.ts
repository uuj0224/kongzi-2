import { createApp } from 'vue'
import { ElButton, ElDialog, ElDrawer, provideGlobalConfig } from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import './style.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
const app = createApp(App)
provideGlobalConfig({ locale: zhCn }, app, true)
app.component('ElButton', ElButton).component('ElDialog', ElDialog).component('ElDrawer', ElDrawer).mount('#app')
