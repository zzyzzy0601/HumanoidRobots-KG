<template>
  <div class="register-container">
    <div class="register-card">
      <h2 class="register-title">人型机器人知识图谱科普系统 - 注册</h2>
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-item">
          <label class="form-label">用户名</label>
          <input
            type="text"
            v-model="registerForm.username"
            placeholder="请输入用户名"
            class="form-input"
            required
          />
        </div>
        <div class="form-item">
          <label class="form-label">密码</label>
          <input
            type="password"
            v-model="registerForm.password"
            placeholder="请输入密码"
            class="form-input"
            required
          />
        </div>
        <!-- 普通用户注册默认user，管理员角色建议仅后端配置，前端可隐藏 -->
        <div class="form-item" v-if="isAdminShow">
          <label class="form-label">角色</label>
          <select v-model="registerForm.role" class="form-input">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
        </div>
        <button type="submit" class="register-btn" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
        <div class="error-tip" v-if="errorMsg">{{ errorMsg }}</div>
        <div class="success-tip" v-if="successMsg">{{ successMsg }}</div>
      </form>
      <div class="login-link">
        已有账号？<router-link to="/login">立即登录</router-link>
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
const successMsg = ref('');
const isAdminShow = ref(false); // 生产环境保持false，仅测试时改为true
const registerForm = ref({
  username: '',
  password: '',
  role: 'user' // 默认普通用户，管理员仅后端配置/测试时开启
});

const handleRegister = async () => {
  loading.value = true;
  errorMsg.value = '';
  successMsg.value = '';
  try {
    const response = await fetch('http://localhost:3000/api/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(registerForm.value)
    });

    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.message || '注册失败');
    }

    successMsg.value = '注册成功，即将跳转到登录页';
    setTimeout(() => {
      router.push('/login');
    }, 1500);
  } catch (error) {
    errorMsg.value = error.message;
    console.error('注册失败:', error);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
/* 样式复用登录页，仅调整少量命名 */
.register-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
}

.register-card {
  width: 400px;
  padding: 30px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.1);
}

.register-title {
  text-align: center;
  color: #2c3e50;
  margin: 0 0 20px 0;
  font-size: 20px;
}

.register-form {
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

.register-btn {
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

.register-btn:disabled {
  background-color: #90caf9;
  cursor: not-allowed;
}

.error-tip {
  color: #f44336;
  font-size: 13px;
  text-align: center;
  margin-top: 10px;
}

.success-tip {
  color: #4CAF50;
  font-size: 13px;
  text-align: center;
  margin-top: 10px;
}

.login-link {
  font-size: 12px;
  color: #7f8c8d;
  text-align: center;
  margin-top: 10px;
}

.login-link a {
  color: #2196F3;
  text-decoration: none;
}
</style>