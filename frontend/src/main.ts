import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import i18n from './i18n'
import './style.css'

const savedTheme = localStorage.getItem('theme')
if (savedTheme === 'dark') {
  document.documentElement.classList.add('dark')
} else {
  document.documentElement.classList.remove('dark')
  if (!savedTheme) {
    localStorage.setItem('theme', 'light')
  }
}

createApp(App).use(router).use(i18n).mount('#app')
