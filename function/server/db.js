// function/server/db.js 完整修正代码
import mysql from 'mysql2/promise'; // 注意：ES模块用import，不是require

// 创建MySQL连接池
const pool = mysql.createPool({
  host: 'localhost',  
  user: 'root', 
  password: 'Your-password', //注意：修改为你的密码
  database: 'robot_kg',  // 数据库名
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
});

// 测试连接
pool.getConnection().then(conn => {
  console.log('MySQL连接成功');
  conn.release();
}).catch(err => {
  console.error('MySQL连接失败：', err);
});

// 关键：改为默认导出（export default）
export default pool;
