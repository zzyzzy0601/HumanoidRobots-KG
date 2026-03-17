<template>
  <div class="login-container">
    <div class="login-card">
      <h2 class="login-title">人型机器人知识图谱构建与管理系统</h2>
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-item">
          <label class="form-label">用户名</label>
          <input
            type="text"
            v-model="loginForm.username"
            placeholder="请输入用户名"
            class="form-input"
            required
          />
        </div>
        <div class="form-item">
          <label class="form-label">密码</label>
          <input
            type="password"
            v-model="loginForm.password"
            placeholder="请输入密码"
            class="form-input"
            required
          />
        </div>
        <button type="submit" class="login-btn" :disabled="loading">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <div class="error-tip" v-if="errorMsg">{{ errorMsg }}</div>
      </form>
      <div class="user-tip">
        还没有账号？<router-link to="/register">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const loading = ref(false);
const errorMsg = ref('');
const loginForm = ref({
  username: '',
  password: ''
});

// 登录请求
const handleLogin = async () => {
  loading.value = true;
  errorMsg.value = '';
  try {
    const response = await fetch('http://localhost:3000/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(loginForm.value)
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.message || '登录失败');
    }

    // 存储用户信息到本地
    localStorage.setItem('userInfo', JSON.stringify(result.data));
    
    // 根据角色跳转
    if (result.data.role === 'admin') {
      router.push('/admin-graph');
    } else {
      router.push('/user-graph');
    }
  } catch (error) {
    errorMsg.value = error.message;
    console.error('登录失败:', error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
}

.login-card {
  width: 400px;
  padding: 30px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.1);
}

.login-title {
  text-align: center;
  color: #2c3e50;
  margin: 0 0 20px 0;
  font-size: 20px;
}

.login-form {
  margin-bottom: 20px;
}

.form-item {
  margin-bottom: 15px;
}

.form-label {
  display: block;
  margin-bottom: 5px;
  color: #34495e;
  font-size: 14px;
}

.form-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.form-input:focus {
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.login-btn {
  width: 100%;
  padding: 10px;
  background-color: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  margin-top: 10px;
}

.login-btn:disabled {
  background-color: #90caf9;
  cursor: not-allowed;
}

.error-tip {
  color: #f44336;
  font-size: 13px;
  text-align: center;
  margin-top: 10px;
}

.user-tip {
  font-size: 12px;
  color: #7f8c8d;
  text-align: center;
  line-height: 1.5;
}
</style>