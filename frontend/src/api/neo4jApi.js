import axios from 'axios';

// 配置axios实例
const api = axios.create({
  baseURL: 'http://localhost:3001/api',
  timeout: 30000, // 延长超时时间（图谱数据可能较大）
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 添加请求拦截器（调试用）
api.interceptors.request.use(
  (config) => {
    console.log('请求配置：', config);
    return config;
  },
  (error) => {
    console.error('请求拦截器错误：', error);
    return Promise.reject(error);
  }
);

// 添加响应拦截器（精准处理错误）
api.interceptors.response.use(
  (response) => {
    console.log('响应数据：', response);
    return response;
  },
  (error) => {
    console.error('响应拦截器错误：', error);
    // 保留原始错误信息
    return Promise.reject(error);
  }
);

// 获取图谱数据
export const getNeo4jGraphData = () => {
  return api.get('/neo4j/graph');
};