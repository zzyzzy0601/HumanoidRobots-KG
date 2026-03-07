<template>
  <!-- 主容器：左侧图谱 + 右侧详情栏 -->
  <div class="graph-page-container">
    <!-- 图谱容器（含搜索栏） -->
    <div class="graph-wrapper">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <div class="search-input-wrapper">
          <input
            type="text"
            v-model="searchKeyword"
            placeholder="输入节点名称搜索（支持模糊匹配）"
            @keyup.enter="handleSearch"
            class="search-input"
          />
          <button @click="handleSearch" class="search-btn">搜索</button>
          <button @click="resetSearch" class="reset-btn">重置</button>
        </div>
        <!-- 搜索结果 -->
        <div class="search-result" v-if="searchResults.length > 0 && searchKeyword">
          <div 
            class="result-item"
            v-for="node in searchResults"
            :key="node.id"
            @click="highlightAndLocateNode(node)"
          >
            {{ node.label }} [{{ node.group }}]
          </div>
        </div>
        <!-- 无结果提示 -->
        <div class="no-result" v-if="searchKeyword && searchResults.length === 0">
          未找到匹配的节点
        </div>
      </div>

      <!-- 图谱画布 -->
      <div ref="graphContainer" class="graph-container"></div>
    </div>

    <!-- 右侧节点详情栏 -->
    <div class="node-detail-panel" :class="{ 'active': selectedNode !== null }">
      <div class="panel-close-btn" @click="selectedNode = null">×</div>
      <div class="panel-content">
        <div class="node-header">
          <h2 class="node-name">{{ selectedNode?.label || '未选择节点' }}</h2>
          <span class="node-category">[{{ selectedNode?.group || '未知类型' }}]</span>
        </div>

        <div class="node-props-section">
          <h3 class="props-title">节点属性</h3>
          <div class="props-table-wrapper">
            <table class="props-table">
              <thead>
                <tr>
                  <th class="prop-key-th">属性名（数据库键）</th>
                  <th class="prop-value-th">属性值（原始值）</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(value, key) in getNodeOriginalProperties(selectedNode)" :key="key" class="prop-row">
                  <td class="prop-key">{{ key }}</td>
                  <td class="prop-value">
                    <!-- 字符串类型 -->
                    <template v-if="typeof value === 'string'">
                      <span v-if="value.length > 100" class="truncated-text">
                        {{ value.slice(0, 100) }}...
                        <span @click="toggleExpand(key)" class="expand-btn">
                          {{ expandedKeys.has(key) ? '收起' : '展开' }}
                        </span>
                      </span>
                      <span v-else class="full-text">{{ value || '无' }}</span>
                      <div v-if="expandedKeys.has(key)" class="expanded-text">{{ value }}</div>
                    </template>
                    <!-- 数组类型 -->
                    <template v-else-if="Array.isArray(value)">
                      <span v-if="value.length > 5" class="truncated-text">
                        {{ value.slice(0, 5).join(', ') }}... (共{{ value.length }}项)
                        <span @click="toggleExpand(key)" class="expand-btn">
                          {{ expandedKeys.has(key) ? '收起' : '展开' }}
                        </span>
                      </span>
                      <span v-else class="full-text">{{ value.join(', ') || '空数组' }}</span>
                      <div v-if="expandedKeys.has(key)" class="expanded-text">{{ value.join(', ') }}</div>
                    </template>
                    <!-- 对象类型 -->
                    <template v-else-if="typeof value === 'object' && value !== null">
                      <span class="expand-btn" @click="toggleExpand(key)">
                        {{ expandedKeys.has(key) ? '收起JSON' : '展开JSON' }}
                      </span>
                      <div v-if="expandedKeys.has(key)" class="expanded-text">
                        {{ JSON.stringify(value, null, 2) }}
                      </div>
                      <span v-else class="full-text">Object (点击展开查看)</span>
                    </template>
                    <!-- 基础类型 -->
                    <template v-else>
                      <span class="full-text">
                        {{ value === null ? 'null' : value === undefined ? 'undefined' : value }}
                      </span>
                    </template>
                  </td>
                </tr>
                <!-- 无属性提示 -->
                <tr v-if="Object.keys(getNodeOriginalProperties(selectedNode)).length === 0" class="empty-props-row">
                  <td colspan="2" class="empty-props-text">暂无属性信息（数据库中该节点无属性）</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue';
import { Network } from 'vis-network';

// 响应式变量
const graphContainer = ref(null);
let network = null;
const selectedNode = ref(null); // 当前选中的节点
const expandedKeys = ref(new Set()); // 展开的属性键
const allNodes = ref([]); // 所有节点数据
const allEdges = ref([]); // 所有边数据
const highlightedNodeId = ref(null); // 高亮节点ID
const searchKeyword = ref(''); // 搜索关键词

// 节点类型-颜色映射
const nodeColorMap = {
  Company: { background: '#2196F3', border: '#0D47A1', highlight: { background: '#64B5F6' } },
  Robot: { background: '#FF9800', border: '#E65100', highlight: { background: '#FFB74D' } },
  Technology: { background: '#4CAF50', border: '#2E7D32', highlight: { background: '#81C784' } },
  Application: { background: '#9C27B0', border: '#4A148C', highlight: { background: '#BA68C8' } },
  Component: { background: '#F44336', border: '#B71C1C', highlight: { background: '#EF5350' } },
  default: { background: '#795548', border: '#3E2723', highlight: { background: '#A1887F' } }
};

// 封装：请求 Neo4j 数据
const getNeo4jGraphData = async (limit = 100) => {
  try {
    // 强制传递整数参数
    const intLimit = Math.max(1, parseInt(limit, 10) || 100);
    const response = await fetch(`http://localhost:3000/api/neo4j/graph?limit=${intLimit}`);
    
    if (!response.ok) {
      throw new Error(`请求失败：${response.status} ${response.statusText}`);
    }
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('获取 Neo4j 数据失败:', error);
    alert(`数据加载失败：${error.message}`);
    return { status: 500, data: { nodes: [], edges: [] } };
  }
};

// 获取节点原始属性（完全保留 Neo4j 数据）
const getNodeOriginalProperties = (node) => {
  if (!node || !node.properties) return {};
  return { ...node.properties };
};

// 切换属性展开/折叠
const toggleExpand = (key) => {
  const newSet = new Set(expandedKeys.value);
  newSet.has(key) ? newSet.delete(key) : newSet.add(key);
  expandedKeys.value = newSet;
};

// 重置搜索
const resetSearch = () => {
  searchKeyword.value = '';
  highlightedNodeId.value = null;
  if (network && allNodes.value.length > 0) {
    network.body.data.nodes.update(allNodes.value.map(node => ({
      id: node.id,
      color: node.originalColor,
      size: 30
    })));
  }
};

// 处理搜索
const handleSearch = () => {
  if (!searchKeyword.value.trim()) {
    resetSearch();
    return;
  }
  if (searchResults.value.length === 1) {
    highlightAndLocateNode(searchResults.value[0]);
  }
};

// 高亮并定位节点
const highlightAndLocateNode = (node) => {
  if (!network || !node) return;
  resetSearch();
  highlightedNodeId.value = node.id;
  
  // 高亮样式
  network.body.data.nodes.update([{
    id: node.id,
    color: { background: '#e74c3c', border: '#c0392b', highlight: { background: '#f1707a' } },
    size: 40
  }]);

  // 视图定位
  network.focus(node.id, {
    scale: 1.2,
    animation: { duration: 1000, easingFunction: 'easeInOutQuad' }
  });

  // 选中节点显示详情
  selectedNode.value = { ...node };
};

// 搜索结果（模糊匹配）
const searchResults = computed(() => {
  if (!searchKeyword.value.trim()) return [];
  const keyword = searchKeyword.value.toLowerCase().trim();
  return allNodes.value.filter(node => 
    node.label.toLowerCase().includes(keyword) || 
    (node.properties?.name && node.properties.name.toLowerCase().includes(keyword))
  );
});

// 初始化图谱
const initGraph = async () => {
  try {
    await nextTick();
    const container = graphContainer.value;
    if (!container) throw new Error('图谱容器不存在');

    // 设置容器样式
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.backgroundColor = '#f8f9fa';

    // 请求 Neo4j 数据
    const response = await getNeo4jGraphData(1000);
    if (response.status !== 200) throw new Error(response.message || '数据返回异常');
    const { nodes: rawNodes, edges: rawEdges } = response.data;

    // 处理节点数据（保留原始属性）
    allNodes.value = rawNodes.map(node => {
      const nodeColor = nodeColorMap[node.group] || nodeColorMap.default;
      return {
        id: node.id,
        label: node.label || `节点${node.id}`,
        group: node.group || 'default',
        size: 30,
        properties: node.properties || {},
        color: nodeColor,
        originalColor: nodeColor // 存储原始颜色
      };
    });

    // 处理边数据
    allEdges.value = rawEdges.map(edge => ({
      id: edge.id || `${edge.from}-${edge.to}`,
      from: edge.from,
      to: edge.to,
      label: edge.label || '关系',
      width: 2,
      properties: edge.properties || {}
    }));

    // 图谱配置
    const options = {
      nodes: { shape: 'box', font: { size: 12, color: '#000', bold: true }, borderWidth: 2 },
      edges: { color: '#666', font: { size: 10, color: '#000' }, arrows: { to: { enabled: true } }, smooth: false },
      interaction: { dragNodes: true, dragView: true, zoomView: true, hover: true },
      layout: { randomSeed: 42, improvedLayout: true },
      physics: {
        enabled: true,
        stabilization: { enabled: true, iterations: 500, fit: true },
        barnesHut: { gravitationalConstant: -1500, springLength: 100 }
      },
      animation: { enabled: true, duration: 500 }
    };

    // 渲染图谱
    if (network) network.destroy();
    network = new Network(container, { nodes: allNodes.value, edges: allEdges.value }, options);

    // 节点点击事件
    network.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = allNodes.value.find(n => n.id === nodeId);
        if (node) {
          selectedNode.value = { ...node };
          if (highlightedNodeId.value !== nodeId) {
            highlightAndLocateNode(node);
          }
        }
      } else {
        selectedNode.value = null;
      }
    });

    // 稳定化后适配视图
    network.on('stabilizationIterationsDone', () => {
      network.fit({ padding: 50 });
    });

  } catch (error) {
    console.error('图谱初始化失败：', error);
    alert(`图谱加载失败：${error.message}`);
    if (graphContainer.value) {
      graphContainer.value.innerHTML = '<div style="text-align:center; padding-top: 50px; color: #999;">数据加载失败，请检查后端服务并刷新页面</div>';
    }
  }
};

// 监听搜索关键词
watch(searchKeyword, (newVal) => {
  if (!newVal.trim()) resetSearch();
}, { immediate: true });

// 生命周期
onMounted(() => setTimeout(initGraph, 500));
onUnmounted(() => {
  if (network) {
    network.destroy();
    network = null;
  }
});
</script>

<style scoped>
/* 主容器 */
.graph-page-container {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: #f5f5f5;
}

/* 图谱容器 */
.graph-wrapper {
  flex: 1;
  position: relative;
  height: 100%;
}

/* 搜索栏 */
.search-bar {
  position: absolute;
  top: 15px;
  left: 15px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.98);
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 500px;
}

.search-input-wrapper {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.search-input:focus {
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.search-btn, .reset-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

.search-btn {
  background-color: #2196F3;
  color: white;
}

.search-btn:hover {
  background-color: #1976D2;
}

.reset-btn {
  background-color: #f0f0f0;
  color: #666;
}

.reset-btn:hover {
  background-color: #e0e0e0;
}

.search-result {
  margin-top: 10px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 4px;
  background: white;
}

.result-item {
  padding: 8px 12px;
  font-size: 14px;
  cursor: pointer;
}

.result-item:hover {
  background-color: #f8f9fa;
}

.no-result {
  margin-top: 10px;
  font-size: 14px;
  color: #999;
  font-style: italic;
}

/* 图谱画布 */
.graph-container {
  width: 100%;
  height: 100%;
}

/* 右侧详情栏 */
.node-detail-panel {
  width: 400px;
  height: 100%;
  background-color: white;
  box-shadow: -2px 0 15px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 0;
  right: 0;
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 99;
  overflow-y: auto;
  padding: 20px 0;
}

.node-detail-panel.active {
  transform: translateX(0);
}

.panel-close-btn {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 32px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  font-size: 20px;
  color: #666;
  cursor: pointer;
  border-radius: 50%;
  background-color: #f5f5f5;
  z-index: 10;
}

.panel-close-btn:hover {
  background-color: #e0e0e0;
  color: #333;
}

.panel-content {
  padding: 20px;
  margin-top: 10px;
}

.node-header {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.node-name {
  font-size: 20px;
  color: #2c3e50;
  margin: 0 0 5px 0;
  font-weight: 600;
}

.node-category {
  font-size: 14px;
  color: #7f8c8d;
}

.node-props-section {
  margin-top: 10px;
}

.props-title {
  font-size: 16px;
  color: #34495e;
  margin: 0 0 15px 0;
  font-weight: 600;
}

.props-table-wrapper {
  width: 100%;
}

.props-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.props-table th {
  background-color: #f8f9fa;
  color: #2c3e50;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 2px solid #eee;
}

.prop-key-th {
  width: 30%;
}

.prop-value-th {
  width: 70%;
}

.props-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #eee;
  vertical-align: top;
}

.prop-key {
  color: #2c3e50;
  font-weight: 500;
}

.prop-value {
  color: #34495e;
  line-height: 1.5;
}

.truncated-text {
  display: block;
}

.expand-btn {
  color: #2196F3;
  cursor: pointer;
  margin-left: 5px;
  font-size: 13px;
}

.expanded-text {
  margin-top: 8px;
  padding: 8px;
  background-color: #f8f9fa;
  border-radius: 4px;
  color: #666;
  white-space: pre-wrap;
  font-family: monospace;
}

.full-text {
  display: block;
}

.empty-props-row {
  text-align: center;
}

.empty-props-text {
  color: #999;
  font-style: italic;
  padding: 20px 0;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .node-detail-panel {
    width: 100%;
  }
  .search-bar {
    width: calc(100% - 30px);
  }
  .search-input-wrapper {
    flex-wrap: wrap;
  }
}
</style>