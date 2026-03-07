import express from 'express';
import neo4j from 'neo4j-driver';
import cors from 'cors';
import fs from 'fs';
import path from 'path';

const app = express();

// 1. 配置
const PORT = 3000;
const NEO4J_CONFIG = {
  uri: 'bolt://localhost:7687',
  user: 'neo4j',
  password: 'Youbuding357' // 替换为你的 Neo4j 密码
};

// 2. 增强跨域配置
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type']
}));
app.use(express.json());

// 3. 初始化 Neo4j 驱动
const driver = neo4j.driver(
  NEO4J_CONFIG.uri,
  neo4j.auth.basic(NEO4J_CONFIG.user, NEO4J_CONFIG.password)
);

// 验证 Neo4j 连接
driver.verifyConnectivity()
  .then(() => console.log('✅ Neo4j 连接成功'))
  .catch(err => console.error('❌ Neo4j 连接失败:', err));

// ========== 登录接口 ==========
app.post('/api/login', (req, res) => {
  try {
    const { username, password } = req.body;
    if (!username || !password) {
      return res.status(400).json({
        status: 400,
        message: '用户名和密码不能为空'
      });
    }

    // 读取用户数据
    const usersPath = 'D:/CODE/PCODE/work/frontend/server/users.json';

    // 检查文件是否存在
    if (!fs.existsSync(usersPath)) {
      console.error('users.json 文件不存在:', usersPath);
      return res.status(500).json({
        status: 500,
        message: `用户数据文件不存在，请检查路径：${usersPath}`
      });
    }


    const users = JSON.parse(fs.readFileSync(usersPath, 'utf8'));
    const user = users.find(u => u.username === username && u.password === password);

    if (!user) {
      return res.status(401).json({
        status: 401,
        message: '用户名或密码错误'
      });
    }

    // 返回用户信息（生产环境建议生成token）
    res.status(200).json({
      status: 200,
      data: {
        id: user.id,
        username: user.username,
        role: user.role
      }
    });
  } catch (error) {
    console.error('登录接口异常:', error);
    res.status(500).json({
      status: 500,
      message: '服务器内部错误'
    });
  }
});


// 4. 核心接口：获取图谱数据（彻底修复 LIMIT 类型问题）
app.get('/api/neo4j/graph', async (req, res) => {
  console.log(`收到图谱查询请求 [${new Date().toISOString()}]`);
  
  const session = driver.session();
  try {
    // ========== 关键修复：强制转为整数并验证 ==========
    // 1. 先转字符串再转整数，避免浮点数残留
    const limitStr = (req.query.limit || '100').toString().trim();
    // 2. 正则匹配纯数字，杜绝非整数
    const isInteger = /^[0-9]+$/.test(limitStr);
    // 3. 最终值：合法整数则用，否则兜底 100
    const limit = isInteger ? Number.parseInt(limitStr, 10) : 100;
    // 4. 范围限制
    const finalLimit = Math.max(1, Math.min(limit, 1000));

    console.log(`执行Cypher:
      MATCH (n)
      OPTIONAL MATCH (n)-[r]->(m)
      RETURN n, r, m
      LIMIT $limit
     (limit: ${finalLimit}) (类型: ${typeof finalLimit})`); // 打印类型确认

    // ========== 执行查询：确保参数是纯整数 ==========
    const result = await session.run(
      `
      MATCH (n)
      OPTIONAL MATCH (n)-[r]->(m)
      RETURN n, r, m
      LIMIT $limit
      `,
      { limit: neo4j.int(finalLimit) } // 关键：用 neo4j.int() 强制转为 Neo4j 整数类型
    );

    // 格式化数据
    const nodesMap = new Map();
    const edges = [];

    result.records.forEach(record => {
      const nodeN = record.get('n');
      const relR = record.get('r');
      const nodeM = record.get('m');

      if (nodeN) {
        const nodeId = nodeN.identity.toNumber();
        nodesMap.set(nodeId, {
          id: nodeId,
          label: nodeN.properties.name || nodeN.properties.label || `节点${nodeId}`,
          group: nodeN.labels[0] || 'default',
          properties: { ...nodeN.properties }
        });
      }

      if (nodeM) {
        const nodeId = nodeM.identity.toNumber();
        nodesMap.set(nodeId, {
          id: nodeId,
          label: nodeM.properties.name || nodeM.properties.label || `节点${nodeId}`,
          group: nodeM.labels[0] || 'default',
          properties: { ...nodeM.properties }
        });
      }

      if (relR && nodeN && nodeM) {
        edges.push({
          id: relR.identity.toNumber(),
          from: nodeN.identity.toNumber(),
          to: nodeM.identity.toNumber(),
          label: relR.type || '关系',
          properties: { ...relR.properties }
        });
      }
    });

    // 返回数据
    res.status(200).json({
      status: 200,
      data: {
        nodes: Array.from(nodesMap.values()),
        edges: edges
      }
    });

  } catch (error) {
    console.error('接口处理失败 =====');
    console.error(`错误信息: ${error.message}`);
    console.error(`错误类型: ${error.name}`);
    
    res.status(500).json({
      status: 500,
      message: `Neo4j 查询失败：${error.message}`,
      stack: process.env.NODE_ENV === 'development' ? error.stack : ''
    });
  } finally {
    await session.close();
    console.log('Neo4j会话已关闭');
  }
});

// 5. 启动服务
app.listen(PORT, () => {
  console.log(`✅ 后端服务已启动，地址：http://localhost:${PORT}`);
  console.log(`📡 图谱接口：http://localhost:${PORT}/api/neo4j/graph`);
});

// 6. 优雅关闭
process.on('SIGINT', async () => {
  console.log('\n📤 正在关闭 Neo4j 驱动...');
  await driver.close();
  process.exit(0);
});