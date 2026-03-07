import { createRouter, createWebHistory } from 'vue-router';
import Login from '../components/Login.vue';
import Neo4jGraph from '../components/Neo4jGraph.vue';
import AdminGraph from '../components/AdminGraph.vue';

// 路由守卫：检查登录状态和角色
const requireAuth = (to, from, next) => {
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
  if (!userInfo.username) {
    next('/login');
  } else {
    // 检查角色是否匹配
    if (to.meta.requiredRole && to.meta.requiredRole !== userInfo.role) {
      next('/login');
    } else {
      next();
    }
  }
};

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/user-graph',
    name: 'UserGraph',
    component: Neo4jGraph,
    beforeEnter: requireAuth,
    meta: { requiredRole: 'user' }
  },
  {
    path: '/admin-graph',
    name: 'AdminGraph',
    component: AdminGraph,
    beforeEnter: requireAuth,
    meta: { requiredRole: 'admin' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login'
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;