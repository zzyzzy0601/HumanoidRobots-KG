// 基础请求配置
const BASE_URL = 'http://localhost:3000/api/neo4j';
const LOGIN_URL = 'http://localhost:3000/api/login';

// 请求工具函数
async function request(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    const response = await fetch(url, {
        method: options.method || 'GET',
        headers,
        body: options.body ? JSON.stringify(options.body) : null
    });

    const data = await response.json();
    
    if (!response.ok) {
        throw new Error(data.message || `请求失败：${response.status}`);
    }
    
    return data;
}

// ====== 图谱数据相关 ======
/**
 * 获取图谱数据
 * @param {number} limit - 数据条数限制
 * @returns {Promise} 图谱数据
 */
export function getGraphData(limit = 100) {
    // 强制转为整数
    const intLimit = Math.max(1, Math.min(parseInt(limit) || 100, 10000));
    return request(`${BASE_URL}/graph?limit=${intLimit}`);
}

/**
 * 导出图谱数据
 * @returns {Promise} 导出的Blob数据
 */
export async function exportGraphData() {
    const response = await fetch(`${BASE_URL}/export`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || '导出失败');
    }
    return response.blob();
}

// ====== 节点属性相关 ======
/**
 * 新增节点属性
 * @param {string} nodeId - 节点ID
 * @param {string} key - 属性名
 * @param {string} value - 属性值
 * @returns {Promise} 操作结果
 */
export function addNodeProperty(nodeId, key, value) {
    return request(`${BASE_URL}/node/property`, {
        method: 'POST',
        body: { nodeId, key, value }
    });
}

/**
 * 修改节点属性
 * @param {string} nodeId - 节点ID
 * @param {string} key - 属性名
 * @param {string} value - 新属性值
 * @returns {Promise} 操作结果
 */
export function updateNodeProperty(nodeId, key, value) {
    return request(`${BASE_URL}/node/property`, {
        method: 'PUT',
        body: { nodeId, key, value }
    });
}

/**
 * 删除节点属性
 * @param {string} nodeId - 节点ID
 * @param {string} key - 属性名
 * @returns {Promise} 操作结果
 */
export function deleteNodeProperty(nodeId, key) {
    return request(`${BASE_URL}/node/property`, {
        method: 'DELETE',
        body: { nodeId, key }
    });
}

// ====== 节点操作相关 ======
/**
 * 删除节点
 * @param {string} nodeId - 节点ID
 * @returns {Promise} 操作结果
 */
export function deleteNode(nodeId) {
    return request(`${BASE_URL}/node/${nodeId}`, {
        method: 'DELETE'
    });
}

/**
 * 新增节点（适配模板）
 * @param {Object} nodeData - 包含 label, group, properties
 */
export function createNode(nodeData) {
    return request(`${BASE_URL}/node`, {
        method: 'POST',
        body: nodeData
    });
}

// ====== 关系操作相关 ======
/**
 * 新增关系（适配模板）
 * @param {Object} edgeData - 包含 from, to, label, properties
 */
export function createEdge(edgeData) {
    return request(`${BASE_URL}/edge`, {
        method: 'POST',
        body: edgeData
    });
}

/**
 * 获取所有关系类型（优先返回模板中的类型）
 */
export function getRelationshipTypes() {
    return request(`${BASE_URL}/relationship-types`);
}

/**
 * 获取节点模板
 * @returns {Promise} 节点模板数据
 */
export function getNodeTemplates() {
    return request(`${BASE_URL}/node-templates`);
}

/**
 * 获取关系模板
 * @returns {Promise} 关系模板数据
 */
export function getRelationTemplates() {
    return request(`${BASE_URL}/relation-templates`);
}

// ====== 用户登录 ======
/**
 * 用户登录
 * @param {string} username - 用户名
 * @param {string} password - 密码
 * @returns {Promise} 登录结果
 */
export function login(username, password) {
    return request(LOGIN_URL, {
        method: 'POST',
        body: { username, password }
    });
}