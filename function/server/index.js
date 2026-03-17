import express from 'express';
import cors from 'cors';
import neo4j from 'neo4j-driver';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import pool from './db.js'; 

// ====== 解决 ES 模块中 __dirname 未定义问题 ======
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = 3000;

// 中间件配置
app.use(cors()); // 允许跨域
app.use(express.json()); // 解析JSON请求体

// ====== 节点/关系模板常量 ======
const NODE_TEMPLATES = {
    "Robot": {
        "name": "无",
        "height": "无",
        "weight": "无",
        "release_year": "无",
        "battery_life": "无",
        "payload": "无",
        "description": "无",
        "product_type": "无"
    },
    "Company": {
        "name": "无",
        "country": "无",
        "found_year": "无",
        "description": "无"
    },
    "BodyPart": {
        "name": "无",
        "DOF": "无"
    },
    "Application": {
        "name": "无",
        "domain": "无"
    },
    "Component": {
        "name": "无",
        "specifications": "无"
    },
    "HardwareTech": {
        "name": "无",
        "parameter": "无",
        "description": "无"
    },
    "SoftwareTech": {
        "name": "无",
        "description": "无"
    },
    "ElectricalFeature": {
        "name": "无",
        "specification": "无"
    }
};

const RELATION_TEMPLATES = {
    "DEVELOPE": {"year": "无", "version": "无"},
    "CONTAINS": {"description": "无"},
    "APPLIED_IN": {"maturity": "无", "case": "无"},
    "HAS_PART": {},
    "IMPLEMENTS": {},
    "USES_TECH": {},
    "FEATURE": {}
};

// ====== Neo4j 数据库连接配置 ======
const driver = neo4j.driver(
    'bolt://localhost:7687',
    neo4j.auth.basic('neo4j', 'Your-password') //注意：修改为你的密码
);

// 测试Neo4j连接
async function testNeo4jConnection() {
    const session = driver.session();
    try {
        await session.run('MATCH (n) RETURN count(n) AS count LIMIT 1');
        console.log('Neo4j 数据库连接成功');
    } catch (error) {
        console.error('Neo4j 连接失败:', error.message);
        process.exit(1); // 连接失败退出服务
    } finally {
        await session.close();
    }
}

// 1. 注册接口（明文密码）
app.post('/api/register', async (req, res) => {
    try {
        const { username, password, role = 'user' } = req.body;
        console.log('注册请求：', req.body);

        // 校验参数
        if (!username || !password) {
            return res.status(400).json({ message: '用户名/密码不能为空' });
        }

        // 检查用户名是否已存在
        const [existingUser] = await pool.query(
            'SELECT * FROM users WHERE username = ?',
            [username]
        );
        if (existingUser.length > 0) {
            return res.status(409).json({ message: '用户名已存在' });
        }

        // 直接写入明文密码
        await pool.query(
            'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
            [username, password, role]
        );

        res.status(200).json({ message: '注册成功' });
    } catch (err) {
        console.error('注册接口错误：', err);
        res.status(500).json({ message: '服务器内部错误' });
    }
});

// 2. 登录接口（明文密码验证，基于MySQL，移除重复的JSON文件登录接口）
app.post('/api/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        console.log('登录请求：', req.body);

        // 校验参数
        if (!username || !password) {
            return res.status(400).json({ message: '用户名/密码不能为空' });
        }

        // 查询用户
        const [users] = await pool.query(
            'SELECT * FROM users WHERE username = ?',
            [username]
        );
        if (users.length === 0) {
            return res.status(401).json({ message: '用户名或密码错误' });
        }

        const user = users[0];
        // 明文对比密码
        if (password !== user.password) {
            console.log('密码错误：输入', password, '数据库存储', user.password);
            return res.status(401).json({ message: '用户名或密码错误' });
        }

        // 登录成功，返回用户信息
        res.status(200).json({
            message: '登录成功',
            data: {
                username: user.username,
                role: user.role // 返回角色（user/admin）
            }
        });
    } catch (err) {
        console.error('登录接口错误：', err);
        res.status(500).json({ message: '服务器内部错误' });
    }
});

// ====== 获取图谱数据 ======
app.get('/api/neo4j/graph', async (req, res) => {
    // 1. 强制转为整数，杜绝浮点数
    let limit = 100; // 默认值
    if (req.query.limit) {
        // 先转字符串，过滤所有非数字字符，再转整数
        const cleanLimit = String(req.query.limit).replace(/[^0-9]/g, '');
        limit = cleanLimit ? parseInt(cleanLimit, 10) : 100;
    }
    // 2. 边界校验：确保是 1~10000 之间的整数
    limit = Math.max(1, Math.min(Math.floor(limit), 10000));

    const session = driver.session();

    try {
        // 3. 拼接整数到 Cypher 语句（LIMIT 是安全参数，无注入风险）
        const nodeResult = await session.run(`MATCH (n) RETURN n LIMIT ${limit}`);
        const edgeResult = await session.run(`MATCH (n)-[r]->(m) RETURN r, n, m LIMIT ${limit}`);

        // 格式化节点数据
        const nodes = nodeResult.records.map(record => {
            const node = record.get('n');
            return {
                id: node.elementId, // Neo4j 5.x 使用 elementId
                label: node.properties.name || node.properties.label || `节点${node.elementId}`,
                group: node.properties.group || node.labels[0] || 'default',
                properties: node.properties
            };
        });

        // 格式化关系数据
        const edges = edgeResult.records.map(record => {
            const rel = record.get('r');
            const fromNode = record.get('n');
            const toNode = record.get('m');
            return {
                id: rel.elementId,
                from: fromNode.elementId,
                to: toNode.elementId,
                label: rel.type,
                properties: rel.properties
            };
        });

        res.json({
            status: 200,
            message: '数据获取成功',
            data: { nodes, edges }
        });
    } catch (error) {
        console.error('获取图谱数据失败:', error);
        res.status(500).json({
            status: 500,
            message: `获取数据失败：${error.message}`,
            data: { nodes: [], edges: [] }
        });
    } finally {
        await session.close();
    }
});

// ====== 节点属性操作（增/删/改） ======
// 1. 新增节点属性（POST）
app.post('/api/neo4j/node/property', async (req, res) => {
    const { nodeId, key, value } = req.body;

    // 严格参数校验
    if (!nodeId || !key || value === undefined) {
        return res.status(400).json({
            status: 400,
            message: '参数错误：nodeId、key 必填，value 不能为空'
        });
    }

    // 属性名安全校验（仅允许英文、数字、下划线，防止注入）
    if (!/^[a-zA-Z0-9_]+$/.test(key)) {
        return res.status(400).json({
            status: 400,
            message: '属性名仅支持英文、数字、下划线'
        });
    }

    const session = driver.session();
    try {
        const cypher = `MATCH (n) WHERE elementId(n) = '${nodeId}' SET n.${key} = $value RETURN n`;
        const result = await session.run(cypher, { value });

        if (result.records.length === 0) {
            return res.status(404).json({
                status: 404,
                message: '节点不存在'
            });
        }

        res.json({
            status: 200,
            message: '属性新增成功'
        });
    } catch (error) {
        console.error('新增属性失败:', error);
        res.status(500).json({
            status: 500,
            message: `服务器错误：${error.message}`
        });
    } finally {
        await session.close();
    }
});

// 2. 修改节点属性（PUT）
app.put('/api/neo4j/node/property', async (req, res) => {
    const { nodeId, key, value } = req.body;

    if (!nodeId || !key || value === undefined) {
        return res.status(400).json({
            status: 400,
            message: '参数错误：nodeId、key 必填，value 不能为空'
        });
    }

    if (!/^[a-zA-Z0-9_]+$/.test(key)) {
        return res.status(400).json({
            status: 400,
            message: '属性名仅支持英文、数字、下划线'
        });
    }

    const session = driver.session();
    try {
        const cypher = `MATCH (n) WHERE elementId(n) = '${nodeId}' SET n.${key} = $value RETURN n`;
        const result = await session.run(cypher, { value });

        if (result.records.length === 0) {
            return res.status(404).json({
                status: 404,
                message: '节点不存在'
            });
        }

        res.json({
            status: 200,
            message: '属性修改成功'
        });
    } catch (error) {
        console.error('修改属性失败:', error);
        res.status(500).json({
            status: 500,
            message: `服务器错误：${error.message}`
        });
    } finally {
        await session.close();
    }
});

// 3. 删除节点属性（DELETE）
app.delete('/api/neo4j/node/property', async (req, res) => {
    const { nodeId, key } = req.body;

    if (!nodeId || !key) {
        return res.status(400).json({
            status: 400,
            message: '参数错误：nodeId、key 必填'
        });
    }

    if (!/^[a-zA-Z0-9_]+$/.test(key)) {
        return res.status(400).json({
            status: 400,
            message: '属性名仅支持英文、数字、下划线'
        });
    }

    const session = driver.session();
    try {
        const cypher = `MATCH (n) WHERE elementId(n) = '${nodeId}' REMOVE n.${key} RETURN n`;
        const result = await session.run(cypher);

        if (result.records.length === 0) {
            return res.status(404).json({
                status: 404,
                message: '节点不存在'
            });
        }

        res.json({
            status: 200,
            message: '属性删除成功'
        });
    } catch (error) {
        console.error('删除属性失败:', error);
        res.status(500).json({
            status: 500,
            message: `服务器错误：${error.message}`
        });
    } finally {
        await session.close();
    }
});

// 4. 删除节点接口
app.delete('/api/neo4j/node/:nodeId', async (req, res) => {
    const { nodeId } = req.params;

    const session = driver.session();
    try {
        // 先删除关联关系，再删除节点
        await session.run(
            `MATCH (n)-[r]-() WHERE elementId(n) = $nodeId DELETE r`,
            { nodeId }
        );
        const result = await session.run(
            `MATCH (n) WHERE elementId(n) = $nodeId DELETE n RETURN count(n) AS count`,
            { nodeId }
        );

        if (result.records[0].get('count').toNumber() === 0) {
            return res.status(404).json({
                status: 404,
                message: '节点不存在'
            });
        }

        res.json({
            status: 200,
            message: '节点删除成功'
        });
    } catch (error) {
        console.error('删除节点失败:', error);
        res.status(500).json({
            status: 500,
            message: `服务器错误：${error.message}`
        });
    } finally {
        await session.close();
    }
});

// 5. 导出数据接口
app.get('/api/neo4j/export', async (req, res) => {
    const session = driver.session();
    try {
        const nodeResult = await session.run(`MATCH (n) RETURN n`);
        const edgeResult = await session.run(`MATCH (n)-[r]->(m) RETURN r, n, m`);

        // 格式化导出数据
        const exportData = {
            nodes: nodeResult.records.map(record => {
                const node = record.get('n');
                return {
                    id: node.elementId,
                    label: node.properties.name || node.properties.label,
                    group: node.properties.group || node.labels[0],
                    properties: node.properties
                };
            }),
            edges: edgeResult.records.map(record => {
                const rel = record.get('r');
                const fromNode = record.get('n');
                const toNode = record.get('m');
                return {
                    id: rel.elementId,
                    from: fromNode.elementId,
                    to: toNode.elementId,
                    label: rel.type,
                    properties: rel.properties
                };
            }),
            exportTime: new Date().toISOString()
        };

        // 设置响应头，触发文件下载
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Content-Disposition', `attachment; filename=neo4j_graph_export_${Date.now()}.json`);
        res.json(exportData);
    } catch (error) {
        console.error('导出数据失败:', error);
        res.status(500).json({
            status: 500,
            message: `导出失败：${error.message}`
        });
    } finally {
        await session.close();
    }
});

// 6. 新增节点接口（适配节点模板）
app.post('/api/neo4j/node', async (req, res) => {
    const { label, group, properties } = req.body;

    if (!label || !group) {
        return res.status(400).json({ status: 400, message: '名称和类型不能为空' });
    }

    // 校验group是否在模板中
    if (!NODE_TEMPLATES[group]) {
        return res.status(400).json({ 
            status: 400, 
            message: `节点类型${group}不在模板中，支持的类型：${Object.keys(NODE_TEMPLATES).join(', ')}` 
        });
    }

    const session = driver.session();
    try {
        // 合并模板默认属性和传入属性（传入属性优先级更高）
        const defaultProps = NODE_TEMPLATES[group];
        const mergedProps = { 
            ...defaultProps, 
            name: label, // 强制覆盖name为label
            ...(properties || {}) 
        };

        // 使用 Cypher 创建节点。注意：Neo4j 标签不支持参数化，需要拼接（已做合法性检查）
        const safeGroup = group.replace(/[^a-zA-Z0-9]/g, ''); 
        const cypher = `CREATE (n:${safeGroup} $props) RETURN n`;
        
        const result = await session.run(cypher, { props: mergedProps });
        const newNode = result.records[0].get('n');

        res.json({
            status: 200,
            message: '节点创建成功',
            data: { id: newNode.elementId }
        });
    } catch (error) {
        console.error('创建节点失败:', error);
        res.status(500).json({ status: 500, message: error.message });
    } finally {
        await session.close();
    }
});

// 7. 新增关系接口（适配关系模板）
app.post('/api/neo4j/edge', async (req, res) => {
    const { from, to, label, properties } = req.body;

    if (!from || !to || !label) {
        return res.status(400).json({ status: 400, message: '起始、终止节点和关系类型必填' });
    }

    // 校验label是否在关系模板中
    if (!RELATION_TEMPLATES[label]) {
        return res.status(400).json({ 
            status: 400, 
            message: `关系类型${label}不在模板中，支持的类型：${Object.keys(RELATION_TEMPLATES).join(', ')}` 
        });
    }

    const session = driver.session();
    try {
        // 合并模板默认属性和传入属性（传入属性优先级更高）
        const defaultRelProps = RELATION_TEMPLATES[label];
        const mergedRelProps = { ...defaultRelProps, ...(properties || {}) };

        // 关系类型同样需要安全过滤
        const safeLabel = label.replace(/[^a-zA-Z0-9_]/g, '');
        const cypher = `
            MATCH (a), (b)
            WHERE elementId(a) = $from AND elementId(b) = $to
            CREATE (a)-[r:${safeLabel} $props]->(b)
            RETURN r
        `;

        const result = await session.run(cypher, { 
            from, 
            to, 
            props: mergedRelProps 
        });

        if (result.records.length === 0) {
            throw new Error('未找到指定的节点，无法建立关系');
        }

        res.json({ status: 200, message: '关系创建成功' });
    } catch (error) {
        console.error('创建关系失败:', error);
        res.status(500).json({ status: 500, message: error.message });
    } finally {
        await session.close();
    }
});

// 8. 获取所有关系类型
app.get('/api/neo4j/relationship-types', async (req, res) => {
    try {
        // 优先返回模板中的关系类型（而非数据库中已有的）
        const templateTypes = Object.keys(RELATION_TEMPLATES);
        res.json({ status: 200, data: templateTypes });
    } catch (error) {
        res.status(500).json({ status: 500, message: error.message });
    }
});

// 9. 获取节点模板接口（新增）
app.get('/api/neo4j/node-templates', async (req, res) => {
    try {
        res.json({ status: 200, data: NODE_TEMPLATES });
    } catch (error) {
        res.status(500).json({ status: 500, message: error.message });
    }
});

// 10. 获取关系模板接口（新增）
app.get('/api/neo4j/relation-templates', async (req, res) => {
    try {
        res.json({ status: 200, data: RELATION_TEMPLATES });
    } catch (error) {
        res.status(500).json({ status: 500, message: error.message });
    }
});

// ====== 启动服务 ======
testNeo4jConnection().then(() => {
    app.listen(PORT, () => {
        console.log(`服务运行在 http://localhost:${PORT}`);
        console.log(`接口文档：`);
        console.log(`  - GET  /api/neo4j/graph?limit=100  # 获取图谱数据`);
        console.log(`  - POST /api/neo4j/node/property    # 新增节点属性`);
        console.log(`  - PUT  /api/neo4j/node/property    # 修改节点属性`);
        console.log(`  - DELETE /api/neo4j/node/property # 删除节点属性`);
        console.log(`  - DELETE /api/neo4j/node/:nodeId   # 删除节点`);
        console.log(`  - GET  /api/neo4j/export           # 导出数据`);
        console.log(`  - POST /api/register               # 用户注册`);
        console.log(`  - POST /api/login                  # 用户登录`);
        console.log(`  - POST /api/neo4j/node             # 新增节点`);
        console.log(`  - POST /api/neo4j/edge             # 新增关系`);
        console.log(`  - GET  /api/neo4j/relationship-types # 获取所有关系类型`);
        console.log(`  - GET  /api/neo4j/node-templates   # 获取节点模板`);
        console.log(`  - GET  /api/neo4j/relation-templates # 获取关系模板`);
    });
});

// 优雅退出
process.on('SIGINT', async () => {
    console.log('\n正在关闭Neo4j连接...');
    await driver.close();
    process.exit(0);
});
