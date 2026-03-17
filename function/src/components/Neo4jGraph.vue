<template>
  <!-- 主容器：左侧图谱 + 右侧详情栏 + 顶部功能栏 -->
  <div class="user-graph-page-container">
    <!-- 顶部功能栏 -->
    <div class="user-top-bar">
      <div class="top-bar-left">
        <h3>人型机器人知识图谱科普系统</h3>
        <button @click="refreshGraph" class="func-btn">刷新图谱</button>
        <button @click="clearAll" class="func-btn">清空选中</button>
      </div>
      <div class="top-bar-right">
        <span>当前用户：{{ userInfo.username }} (普通用户)</span>
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </div>

    <!-- 图谱容器（含搜索栏） -->
    <div class="graph-wrapper">
      <!-- 扩展搜索栏 -->
      <div class="search-bar">
        <div class="search-input-wrapper">
          <select v-model="searchType" class="search-select">
            <option value="name">节点名称</option>
            <option value="group">标签</option>
            <option value="property">属性值</option>
          </select>
          <input
            type="text"
            v-model="searchKeyword"
            placeholder="输入搜索内容（支持模糊匹配）"
            @keyup.enter="handleSearch"
            class="search-input"
          />
          <button @click="handleSearch" class="search-btn">搜索</button>
          <button @click="resetSearch" class="reset-btn">重置</button>
        </div>
        <!-- 高级筛选 -->
        <div class="advanced-filter">
          <label class="filter-label">标签筛选：</label>
          <div class="filter-tags">
            <span 
              v-for="type in allNodeTypes" 
              :key="type"
              @click="toggleFilterType(type)"
              class="filter-tag"
              :class="{ active: filteredTypes.includes(type) }"
            >
              {{ type }}
            </span>
          </div>
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

        <!-- 仅保留查看关联节点功能 -->
        <div class="user-actions" v-if="selectedNode">
          <h3 class="action-title">节点操作</h3>
          <button @click="showRelatedNodes" class="action-btn">查看关联节点</button>
        </div>

        <!-- 核心修改：适配本地路径的多媒体展示区域 -->
        <div class="node-media-section" v-if="selectedNode">
          <h3 class="media-title">多媒体资源</h3>
          <!-- 图片展示（适配本地路径） -->
          <div class="media-images" v-if="getLocalMediaProperties(selectedNode).images.length > 0">
            <h4 class="sub-title">图片</h4>
            <div class="images-grid">
              <div 
                class="image-item" 
                v-for="(img, index) in getLocalMediaProperties(selectedNode).images" 
                :key="`img-${index}`"
              >
                <img 
                  :src="convertLocalPathToUrl(img)" 
                  :alt="`${selectedNode.label}-图片${index+1}`"
                  class="media-image"
                  @click="openImagePreview(convertLocalPathToUrl(img))"
                  loading="lazy"
                  @error="handleImageError($event, img)"
                />
                <div class="image-desc">图片{{ index+1 }}（本地路径）</div>
              </div>
            </div>
          </div>

          <!-- 视频展示（适配本地路径） -->
          <div class="media-videos" v-if="getLocalMediaProperties(selectedNode).videos.length > 0">
            <h4 class="sub-title">视频</h4>
            <div class="videos-grid">
              <div 
                class="video-item" 
                v-for="(video, index) in getLocalMediaProperties(selectedNode).videos" 
                :key="`video-${index}`"
              >
                <video 
                  :src="convertLocalPathToUrl(video)" 
                  controls 
                  class="media-video"
                  preload="metadata"
                  @error="handleVideoError($event, video)"
                >
                  您的浏览器不支持HTML5视频播放，请检查本地路径是否正确
                </video>
                <div class="video-desc">视频{{ index+1 }}（本地路径）</div>
              </div>
            </div>
          </div>

          <!-- 无多媒体提示 -->
          <div class="no-media" v-if="
            getLocalMediaProperties(selectedNode).images.length === 0 && 
            getLocalMediaProperties(selectedNode).videos.length === 0
          ">
            暂无图片/视频资源
          </div>
        </div>

        <div class="node-props-section">
          <h3 class="props-title">节点属性</h3>
          <div class="props-table-wrapper">
            <table class="props-table">
              <thead>
                <tr>
                  <th class="prop-key-th">属性名</th>
                  <th class="prop-value-th">属性值</th>
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

        <!-- 新增：关联关系属性展示 -->
        <div class="edge-props-section" v-if="selectedNode && relatedEdges.length > 0">
          <h3 class="props-title">关联关系属性</h3>
          <div class="props-table-wrapper">
            <table class="props-table">
              <thead>
                <tr>
                  <th class="prop-key-th">关系类型</th>
                  <th class="prop-key-th">关联节点</th>
                  <th class="prop-value-th">属性值</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(edge, index) in relatedEdges" :key="`edge-${index}`" class="prop-row">
                  <td class="prop-key">{{ edge.label }}</td>
                  <td class="prop-key">
                    {{ edge.from === selectedNode.id 
                      ? allNodes.find(n => n.id === edge.to)?.label || '未知节点' 
                      : allNodes.find(n => n.id === edge.from)?.label || '未知节点' }}
                  </td>
                  <td class="prop-value">
                    <template v-for="(val, key) in getEdgeOriginalProperties(edge)" :key="`edge-prop-${key}-${index}`">
                      <div class="edge-prop-item">
                        <span class="edge-prop-key">{{ key }}：</span>
                        <span class="edge-prop-value">{{ val || '无' }}</span>
                      </div>
                    </template>
                    <template v-if="Object.keys(getEdgeOriginalProperties(edge)).length === 0">
                      <span class="empty-props-text">无关系属性</span>
                    </template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片预览弹窗 -->
    <div class="image-preview-modal" v-if="previewImageUrl" @click="closeImagePreview">
      <div class="preview-content" @click.stop>
        <span class="preview-close-btn" @click="closeImagePreview">×</span>
        <img :src="previewImageUrl" alt="预览图片" class="preview-image" />
      </div>
    </div>

<!-- 根容器末尾：右下角颜色示例框 -->
<div class="color-example-panel-fixed">
  <div class="color-example-title">标签颜色示例</div>
  <div class="color-example-list">
    <div 
      class="color-example-item" 
      v-for="(color, label) in nodeColorMap" 
      :key="label"
      v-if="label !== 'default'"
    >
      <span class="color-label">{{ label }}：</span>
      <span class="color-box" :style="{ backgroundColor: color.background, borderColor: color.border }"></span>
    </div>
  </div>
</div>


  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue';
import { Network } from 'vis-network';
import { useRouter } from 'vue-router';

const router = useRouter();
// 响应式变量
const graphContainer = ref(null);
let network = null;
const selectedNode = ref(null);
const expandedKeys = ref(new Set());
const allNodes = ref([]);
const allEdges = ref([]);
const highlightedNodeId = ref(null);
const searchKeyword = ref('');
const searchType = ref('name'); // 搜索类型：name/group/property
const filteredTypes = ref([]); // 筛选的标签
const loading = ref(false);
const relatedEdges = ref([]); // 选中节点的关联关系

// 图片预览相关变量
const previewImageUrl = ref(''); // 预览图片URL

// 获取用户信息
const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'));
if (!userInfo.value) {
  router.push('/login');
}

// 节点模板：{标签: {属性名: 默认值}}
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

// 关系模板：{类型: {属性名: 默认值}}
const RELATION_TEMPLATES = {
  "DEVELOPE": {"year": "无", "version": "无"},
  "CONTAINS": {"description": "无"},
  "APPLIED_IN": {"maturity": "无", "case": "无"},
  "HAS_PART": {},  // 无属性则为空字典
  "IMPLEMENTS": {},
  "USES_TECH": {},
  "FEATURE": {}
};

const nodeColorMap = {
  // 核心产品：采用鲜明的蓝色，代表科技感
  Robot: { background: '#5C7CFA', border: '#364FC7', highlight: { background: '#748FFC' } },
  
  // 商业主体：低饱和度的冷灰色，作为稳定的背景
  Company: { background: '#ADB5BD', border: '#495057', highlight: { background: '#CED4DA' } },
  
  // 机械结构：生机盎然的绿色，代表肢体和硬件
  BodyPart: { background: '#51CF66', border: '#2B8A3E', highlight: { background: '#69DB7C' } },
  
  // 应用场景：优雅的紫色，代表多元的落地领域
  Application: { background: '#BE4BDB', border: '#862E9C', highlight: { background: '#D0BFFF' } },
  
  // 核心组件：醒目的橘红色，代表硬件的心脏
  Component: { background: '#FF922B', border: '#D9480F', highlight: { background: '#FFA94D' } },
  
  // 硬件技术：清爽的青蓝色，区分于Robot和Software
  HardwareTech: { background: '#22B8CF', border: '#0C8599', highlight: { background: '#3BC9DB' } },
  
  // 软件技术/算法：明亮的亮黄色，代表智能逻辑
  SoftwareTech: { background: '#FCC419', border: '#F08C00', highlight: { background: '#FFE066' } },
  
  // 电气特性：柔和的粉褐色，代表底层的电气连接
  ElectricalFeature: { background: '#FF8787', border: '#E03131', highlight: { background: '#FFA8A8' } },
  
  default: { background: '#DEE2E6', border: '#868E96', highlight: { background: '#F1F3F5' } }
};

// 所有标签（计算属性）
const allNodeTypes = computed(() => {
  const types = new Set(allNodes.value.map(node => node.group));
  return Array.from(types);
});

// 封装：请求 Neo4j 数据
const getNeo4jGraphData = async (limit = 100) => {
  try {
    loading.value = true;
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
  } finally {
    loading.value = false;
  }
};

// 获取节点原始属性（适配模板默认值）
const getNodeOriginalProperties = (node) => {
  if (!node || !node.group) return {};
  
  // 获取该节点类型的模板
  const template = NODE_TEMPLATES[node.group] || {};
  // 节点实际属性
  const nodeProps = node.properties || {};
  
  // 合并：模板默认值 + 实际属性（实际属性覆盖默认值）
  const mergedProps = { ...template };
  Object.keys(nodeProps).forEach(key => {
    if (nodeProps[key] !== undefined && nodeProps[key] !== null) {
      mergedProps[key] = nodeProps[key];
    }
  });
  
  return mergedProps;
};

// 获取关系原始属性（适配模板默认值）
const getEdgeOriginalProperties = (edge) => {
  if (!edge || !edge.label) return {};
  
  // 获取该关系类型的模板
  const template = RELATION_TEMPLATES[edge.label] || {};
  // 关系实际属性
  const edgeProps = edge.properties || {};
  
  // 合并：模板默认值 + 实际属性（实际属性覆盖默认值）
  const mergedProps = { ...template };
  Object.keys(edgeProps).forEach(key => {
    if (edgeProps[key] !== undefined && edgeProps[key] !== null) {
      mergedProps[key] = edgeProps[key];
    }
  });
  
  return mergedProps;
};

// 核心修改1：提取本地路径的图片/视频属性（适配image_path/video_path字段）
const getLocalMediaProperties = (node) => {
  if (!node || !node.properties) return { images: [], videos: [] };
  
  const properties = node.properties || {};
  const images = [];
  const videos = [];

  // 适配单张图片路径（image_path字段）
  if (properties.image_path && properties.image_path.trim()) {
    images.push(properties.image_path.trim());
  }
  // 适配多张图片（可选：如果有images数组字段也兼容）
  if (Array.isArray(properties.images) && properties.images.length > 0) {
    images.push(...properties.images.filter(img => img.trim()));
  }

  // 适配单个视频路径（video_path字段）
  if (properties.video_path && properties.video_path.trim()) {
    videos.push(properties.video_path.trim());
  }
  // 适配多个视频（可选：如果有videos数组字段也兼容）
  if (Array.isArray(properties.videos) && properties.videos.length > 0) {
    videos.push(...properties.videos.filter(video => video.trim()));
  }

  return { images, videos };
};

// 核心修改：适配public目录下的相对路径
const convertLocalPathToUrl = (localPath) => {
  if (!localPath) return '';
  // 如果是相对路径（以/开头），直接返回；如果是旧的绝对路径，兼容转换
  if (localPath.startsWith('/')) {
    return localPath; // 相对路径直接使用
  } else {
    // 兼容旧的绝对路径，提取文件名（可选）
    const fileName = localPath.split('/').pop();
    return `/image/${fileName}`;
  }
};

// 核心修改3：图片加载失败处理（提示路径错误）
const handleImageError = (e, originalPath) => {
  e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjEyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZTBlMGUwIi8+PHBhdGggZD0iTTUwIDMwIEw0MCA0MCAgTDcwIDcwIEwxMDAgMzAgIEw5MCAyMCBMNzAgNTAgTDUwIDMwIFoiIGZpbGw9IiNmNDQzMzYiLz48dGV4dCB4PSI2MCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM5OTk5OTkiPuWbvueJhzEyvLXEsOi9rTwvdGV4dD48L3N2Zz4=';
  console.error(`图片加载失败：${originalPath}，请检查：1.路径是否正确 2.浏览器是否允许访问本地文件`, e);
  alert(`图片加载失败：\n${originalPath}\n1. 请检查文件是否存在\n2. 浏览器需开启允许访问本地文件权限`);
};

// 核心修改4：视频加载失败处理（提示路径错误）
const handleVideoError = (e, originalPath) => {
  console.error(`视频加载失败：${originalPath}，请检查：1.路径是否正确 2.浏览器是否允许访问本地文件 3.视频格式是否支持`, e);
  alert(`视频加载失败：\n${originalPath}\n1. 请检查文件是否存在\n2. 浏览器需开启允许访问本地文件权限\n3. 推荐使用MP4格式视频`);
};

// 打开图片预览
const openImagePreview = (url) => {
  previewImageUrl.value = url;
  // 禁止页面滚动
  document.body.style.overflow = 'hidden';
};

// 关闭图片预览
const closeImagePreview = () => {
  previewImageUrl.value = '';
  // 恢复页面滚动
  document.body.style.overflow = 'auto';
};

// 切换属性展开/折叠
const toggleExpand = (key) => {
  const newSet = new Set(expandedKeys.value);
  newSet.has(key) ? newSet.delete(key) : newSet.add(key);
  expandedKeys.value = newSet;
};

// 切换筛选类型
const toggleFilterType = (type) => {
  const newTypes = [...filteredTypes.value];
  const index = newTypes.indexOf(type);
  if (index > -1) {
    newTypes.splice(index, 1);
  } else {
    newTypes.push(type);
  }
  filteredTypes.value = newTypes;
};

// 重置搜索
const resetSearch = () => {
  searchKeyword.value = '';
  highlightedNodeId.value = null;
  filteredTypes.value = [];
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

// 搜索结果（多类型模糊匹配）
const searchResults = computed(() => {
  if (!searchKeyword.value.trim()) return [];
  const keyword = searchKeyword.value.toLowerCase().trim();
  
  // 先筛选类型
  let filteredNodes = [...allNodes.value];
  if (filteredTypes.value.length > 0) {
    filteredNodes = filteredNodes.filter(node => filteredTypes.value.includes(node.group));
  }

  // 根据搜索类型匹配
  return filteredNodes.filter(node => {
    switch (searchType.value) {
      case 'name':
        return node.label.toLowerCase().includes(keyword) || (node.properties?.name && node.properties.name.toLowerCase().includes(keyword));
      case 'group':
        return node.group.toLowerCase().includes(keyword);
      case 'property':
        const props = Object.values(getNodeOriginalProperties(node));
        return props.some(val => {
          if (typeof val === 'string') return val.toLowerCase().includes(keyword);
          if (Array.isArray(val)) return val.some(item => item.toString().toLowerCase().includes(keyword));
          return val.toString().toLowerCase().includes(keyword);
        });
      default:
        return false;
    }
  });
});

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
  
  // 获取关联关系
  relatedEdges.value = allEdges.value.filter(edge => edge.from === node.id || edge.to === node.id);
};

// 刷新图谱
const refreshGraph = () => {
  initGraph();
};

// 清空选中
const clearAll = () => {
  selectedNode.value = null;
  relatedEdges.value = [];
  resetSearch();
};

// 查看关联节点
const showRelatedNodes = () => {
  if (!selectedNode.value) {
    alert('请先选中一个节点后再查看关联节点！');
    return;
  }
  
  const nodeId = selectedNode.value.id;
  // 1. 筛选关联边
  const relatedEdgesList = allEdges.value.filter(edge => edge.from === nodeId || edge.to === nodeId);
  relatedEdges.value = relatedEdgesList;
  
  // 2. 提取关联节点ID（排除自身）
  const relatedNodeIds = new Set();
  relatedEdgesList.forEach(edge => {
    if (edge.from !== nodeId) relatedNodeIds.add(edge.from);
    if (edge.to !== nodeId) relatedNodeIds.add(edge.to);
  });
  
  const relatedNodeList = Array.from(relatedNodeIds);
  const relatedNodes = allNodes.value.filter(node => relatedNodeIds.has(node.id));

  // 3. 边界处理：无关联节点
  if (relatedNodeList.length === 0) {
    alert(`【${selectedNode.value.label}】暂无关联节点`);
    // 仅聚焦当前节点
    network.focus(nodeId, {
      scale: 1.2,
      animation: { duration: 800, easingFunction: 'easeInOutQuad' }
    });
    return;
  }

  // 4. 画布聚焦关联节点
  network.focus(relatedNodeList, {
    scale: 1.1,
    animation: { duration: 800, easingFunction: 'easeInOutQuad' }
  });

  // 5. 黄色边框高亮（保留节点原有背景色，仅修改边框）
  network.body.data.nodes.update(allNodes.value.map(node => {
    // 恢复所有节点的原始样式
    const baseStyle = {
      id: node.id,
      color: { ...node.originalColor }, // 保留原有背景色
      size: 30 // 恢复默认尺寸
    };

    // 对关联节点添加黄色高亮边框
    if (relatedNodeIds.has(node.id)) {
      baseStyle.color.border = '#FFD700'; // 金黄色边框
      baseStyle.color.borderWidth = 5;    // 加宽边框（5px）
      baseStyle.size = 32;                // 轻微放大（仅2px，不突兀）
    }

    // 对当前选中节点额外标记（红色边框）
    if (node.id === nodeId) {
      baseStyle.color.border = '#F44336'; // 红色边框区分选中节点
      baseStyle.color.borderWidth = 6;
      baseStyle.size = 35;
    }

    return baseStyle;
  }));

  // 6. 友好的提示弹窗
  alert(`【${selectedNode.value.label}】共找到 ${relatedNodeList.length} 个关联节点，${relatedEdgesList.length} 条关联关系`);
};

// 退出登录
const logout = () => {
  localStorage.removeItem('userInfo');
  router.push('/login');
};

// 初始化图谱
const initGraph = async () => {
  try {
    await nextTick();
    const container = graphContainer.value;
    if (!container) throw new Error('图谱容器不存在');

    container.style.width = '100%';
    container.style.height = '100%';
    container.style.backgroundColor = '#f8f9fa';

    // 请求 Neo4j 数据
    const response = await getNeo4jGraphData(1000);
    if (response.status !== 200) throw new Error(response.message || '数据返回异常');
    const { nodes: rawNodes, edges: rawEdges } = response.data;

    // 处理节点数据
    allNodes.value = rawNodes.map(node => {
      const nodeColor = nodeColorMap[node.group] || nodeColorMap.default;
      return {
        id: node.id,
        label: node.label || `节点${node.id}`,
        group: node.group || 'default',
        size: 30,
        properties: node.properties || {},
        color: nodeColor,
        originalColor: nodeColor
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
      interaction: { dragNodes: true, dragView: true, zoomView: true, hover: true, selectable: true },
      layout: { randomSeed: 42, improvedLayout: true, hierarchical: { enabled: false } },
      physics: {
        enabled: true,
        stabilization: { enabled: true, iterations: 800, fit: true },
        barnesHut: { gravitationalConstant: -2000, springLength: 80, damping: 0.4 },
        minVelocity: 0.1
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
          relatedEdges.value = allEdges.value.filter(edge => edge.from === nodeId || edge.to === nodeId);
          if (highlightedNodeId.value !== nodeId) {
            highlightAndLocateNode(node);
          }
        }
      } else {
        selectedNode.value = null;
        relatedEdges.value = [];
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

// 监听筛选类型变化
watch(filteredTypes, () => {
  if (network && allNodes.value.length > 0) {
    const filteredNodes = filteredTypes.value.length > 0 
      ? allNodes.value.filter(node => filteredTypes.value.includes(node.group))
      : allNodes.value;
    // 更新节点样式：仅修改边框为亮黄色，保留原有背景色
    network.body.data.nodes.update(allNodes.value.map(node => ({
      id: node.id,
      // 核心修改：保留原背景色，筛选节点边框改为亮黄色+加宽
      color: {
        ...node.originalColor, // 继承原有背景色
        border: filteredTypes.value.length > 0 && filteredTypes.value.includes(node.group) 
          ? '#FFD700' // 亮黄色边框
          : node.originalColor.border, // 非筛选节点用原边框色
        borderWidth: filteredTypes.value.length > 0 && filteredTypes.value.includes(node.group) 
          ? 5 // 边框加宽到5px，更明显
          : 2 // 非筛选节点用原边框宽度
      },
      size: filteredTypes.value.length > 0 && filteredTypes.value.includes(node.group) ? 35 : 30
    })));
  }
});

// 生命周期
onMounted(() => setTimeout(initGraph, 500));
onUnmounted(() => {
  if (network) {
    network.destroy();
    network = null;
  }
  // 组件卸载时恢复页面滚动
  document.body.style.overflow = 'auto';
});
</script>

<style scoped>
/* 主容器 */
.user-graph-page-container {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: #f5f5f5;
}

/* 顶部功能栏 */
.user-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: white;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.top-bar-left h3 {
  margin: 0;
  color: #2c3e50;
}

.func-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  background: #2196F3;
  color: white;
  cursor: pointer;
  font-size: 14px;
}

.func-btn:hover {
  opacity: 0.9;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 15px;
  font-size: 14px;
  color: #666;
}

.logout-btn {
  padding: 6px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: white;
  color: #f44336;
  cursor: pointer;
  font-size: 14px;
}

.logout-btn:hover {
  background: #fef0f0;
}

/* 图谱容器 */
.graph-wrapper {
  flex: 1;
  position: relative;
  height: calc(100% - 60px);
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
  width: 600px;
}

.search-input-wrapper {
  display: flex;
  gap: 8px;
  align-items: center;
}

.search-select {
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
  background: white;
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

/* 高级筛选 */
.advanced-filter {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #eee;
}

.filter-label {
  font-size: 14px;
  color: #666;
  margin-right: 10px;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 5px;
}

.filter-tag {
  padding: 4px 10px;
  background: #f0f0f0;
  border-radius: 16px;
  font-size: 13px;
  cursor: pointer;
}

.filter-tag.active {
  background: #2196F3;
  color: white;
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
  width: 500px;
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
  padding-top: 70px;
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

/* 用户操作区 */
.user-actions {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.action-title {
  font-size: 16px;
  color: #34495e;
  margin: 0 0 10px 0;
  font-weight: 600;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  margin-right: 10px;
  margin-bottom: 10px;
  background: #2196F3;
  color: white;
}

/* 核心修改：本地多媒体样式优化 */
.node-media-section {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.media-title {
  font-size: 16px;
  color: #34495e;
  margin: 0 0 15px 0;
  font-weight: 600;
}

.sub-title {
  font-size: 14px;
  color: #2c3e50;
  margin: 0 0 10px 0;
  font-weight: 500;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 15px;
}

.image-item {
  border: 1px solid #eee;
  border-radius: 4px;
  overflow: hidden;
}

.media-image {
  width: 100%;
  height: 120px;
  object-fit: cover;
  cursor: zoom-in;
  transition: transform 0.2s ease;
}

.media-image:hover {
  transform: scale(1.02);
}

.image-desc {
  padding: 5px 8px;
  font-size: 12px;
  color: #666;
  background: #f8f9fa;
  text-align: center;
}

.videos-grid {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.video-item {
  border: 1px solid #eee;
  border-radius: 4px;
  overflow: hidden;
}

.media-video {
  width: 100%;
  height: 200px;
  object-fit: cover;
}

.video-desc {
  padding: 8px;
  font-size: 13px;
  color: #666;
  background: #f8f9fa;
  text-align: center;
}

.no-media {
  font-size: 14px;
  color: #999;
  font-style: italic;
  padding: 10px 0;
  text-align: center;
}

.node-props-section, .edge-props-section {
  margin-top: 10px;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
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
  width: 25%;
}

.prop-value-th {
  width: 75%;
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

/* 关系属性样式 */
.edge-prop-item {
  display: flex;
  margin-bottom: 4px;
}

.edge-prop-key {
  font-weight: 500;
  min-width: 60px;
  color: #2c3e50;
}

.edge-prop-value {
  color: #34495e;
}

/* 图片预览弹窗样式 */
.image-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.85);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-content {
  position: relative;
  max-width: 90%;
  max-height: 90%;
}

.preview-close-btn {
  position: absolute;
  top: -40px;
  right: 0;
  color: white;
  font-size: 24px;
  cursor: pointer;
  width: 36px;
  height: 36px;
  line-height: 36px;
  text-align: center;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 50%;
}

.preview-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
  border-radius: 4px;
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
  .user-top-bar {
    flex-direction: column;
    padding: 10px;
    gap: 10px;
  }
  .images-grid {
    grid-template-columns: 1fr;
  }
  .media-video {
    height: 150px;
  }
}

/* 右下角固定定位的颜色示例面板 */
.color-example-panel-fixed {
  position: fixed; /* 固定在视窗右下角，不随滚动移动 */
  bottom: 20px;    /* 距离底部20px */
  le: 20px;     /* 距离右侧20px */
  padding: 12px 20px; /* 轻微放大内边距，适配更大的内容 */
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08); /* 轻微阴影，增加层次感但不突兀 */
  z-index: 100;    /* 确保在其他元素上方，但不遮挡弹窗 */
  /* 适配放大后的内容，微调最大宽度 */
  max-width: 220px;
}

.color-example-title {
  font-size: 14px; /* 标题字体放大 */
  color: #666;
  margin-bottom: 8px; /* 微调间距 */
  font-weight: bold;
}

/* 核心修改：取消flex横向布局，改为块级让每个item换行 */
.color-example-list {
  /* 移除flex相关属性，改为默认块级布局 */
  gap: 10px; /* 微调垂直间距 */
}

.color-example-item {
  display: flex; /* 保持标签和颜色块横向对齐 */
  align-items: center;
  font-size: 14px; /* 标签字体从12px放大到14px */
  /* 每个item独占一行 */
  width: 100%;
  margin-bottom: 6px; /* 微调行间距 */
}

.color-box {
  width: 18px; /* 颜色方框宽度从16px放大到18px */
  height: 18px; /* 颜色方框高度从16px放大到18px */
  border-radius: 2px;
  border-width: 1px;
  border-style: solid;
  /* 调整间距：标签在左，颜色块在右，间距改为左边 */
  margin-left: 6px; /* 微调间距适配放大后的元素 */
}

.color-label {
  color: #333;
  /* 标签文字宽度固定，对齐更整齐（适配14px字体） */
  display: inline-block;
  width: 110px; /* 微调宽度适配14px字体 */
}


</style>