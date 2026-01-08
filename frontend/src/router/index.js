import { createRouter, createWebHistory } from 'vue-router';
import Home from '../views/Home.vue';
import EyeTracking from '../views/EyeTracking.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/eye-tracking',
    name: 'EyeTracking',
    component: EyeTracking,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

