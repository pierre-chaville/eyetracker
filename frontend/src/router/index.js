import { createRouter, createWebHistory } from 'vue-router';
import Home from '../views/Home.vue';
import EyeTracking from '../views/EyeTracking.vue';
import Communicate from '../views/Communicate.vue';
import Calibration from '../views/Calibration.vue';
import Users from '../views/Users.vue';
import UserDetail from '../views/UserDetail.vue';
import Setup from '../views/Setup.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/communicate',
    name: 'Communicate',
    component: Communicate,
  },
  {
    path: '/calibration',
    name: 'Calibration',
    component: Calibration,
  },
  {
    path: '/eye-tracking',
    name: 'EyeTracking',
    component: EyeTracking,
  },
  {
    path: '/users',
    name: 'Users',
    component: Users,
  },
  {
    path: '/users/:id',
    name: 'UserDetail',
    component: UserDetail,
  },
  {
    path: '/setup',
    name: 'Setup',
    component: Setup,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

