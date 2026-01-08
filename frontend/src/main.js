import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import i18n from './i18n';
import './style.css';

// Initialize theme before app mounts
// Force light mode as default, ignore system preference
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
  document.documentElement.classList.add('dark');
} else {
  // Explicitly set to light mode (default)
  document.documentElement.classList.remove('dark');
  if (!savedTheme) {
    localStorage.setItem('theme', 'light');
  }
}

createApp(App).use(router).use(i18n).mount('#app');

