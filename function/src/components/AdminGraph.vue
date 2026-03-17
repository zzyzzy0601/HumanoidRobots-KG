<template>
  <!-- 主容器：左侧图谱 + 右侧详情栏 + 顶部功能栏 -->
  <div class="admin-graph-page-container">
    <!-- 顶部功能栏 -->
    <div class="admin-top-bar">
      <div class="top-bar-left">
        <h3>人型机器人知识图谱构建与管理系统</h3>
        <button @click="refreshGraph" class="func-btn">刷新图谱</button>
        <button @click="clearAll" class="func-btn">清空选中</button>
        <button @click="showAddNodePanel = true" class="func-btn">添加节点</button>
        <button @click="showAddEdgePanel = true" class="func-btn">添加关系</button>
        <button @click="goToBatchImport" class="func-btn">批量导入数据</button>
        <button @click="exportData" class="func-btn">导出数据</button>
      </div>
      <div class="top-bar-right">
        <span>当前用户：{{ userInfo.username }} (管理员)</span>
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
          <label class="filter-label">节点类型筛选：</label>
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
          <button @click="deleteNode" class="delete-node-btn danger-btn">删除该节点</button>
        </div>

        <!-- 管理员操作区 -->
        <div class="admin-actions" v-if="selectedNode">
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
                  <th class="prop-op-th">操作</th>
                </tr>
              </thead>
              <tbody>
                <!-- 原有属性行 -->
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
                  <td class="prop-op-th">
                    <button @click="editProperty(key)" class="edit-btn">编辑</button>
                    <button @click="deleteProperty(key)" class="delete-btn danger-btn">🗑️</button>
                  </td>
                </tr>
                <!-- 无属性提示 -->
                <tr v-if="Object.keys(getNodeOriginalProperties(selectedNode)).length === 0" class="empty-props-row">
                  <td colspan="3" class="empty-props-text">暂无属性信息（数据库中该节点无属性）</td>
                </tr>
                <!-- 新增属性行 -->
                <tr class="add-prop-row">
                  <td class="prop-key">
                    <input 
                      v-model="newPropKey" 
                      placeholder="属性名" 
                      class="new-prop-input"
                      @input="validatePropKey"
                    />
                    <span v-if="propKeyError" class="error-text">{{ propKeyError }}</span>
                  </td>
                  <td class="prop-value">
                    <input 
                      v-model="newPropValue" 
                      placeholder="属性值" 
                      class="new-prop-input"
                    />
                  </td>
                  <td class="prop-op-th">
                    <button 
                      @click="addProperty" 
                      class="add-btn"
                      :disabled="!newPropKey || !!propKeyError"
                    >+ 新增</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加节点面板（右侧滑出） -->
    <div class="add-node-panel" :class="{ 'active': showAddNodePanel }">
      <div class="panel-close-btn" @click="showAddNodePanel = false">×</div>
      <div class="panel-content">
        <h2 class="panel-title">新增节点</h2>
        <div class="form-item">
          <label class="form-label">标签：</label>
          <select v-model="newNodeGroup" class="form-select">
            <option value="Robot">Robot（机器人）</option>
            <option value="Company">Company（企业）</option>
            <option value="BodyPart">BodyPart（身体部位）</option>
            <option value="Application">Application（应用场景）</option>
            <option value="Component">Component（核心组件）</option>
            <option value="HardwareTech">HardwareTech（硬件技术）</option>
            <option value="SoftwareTech">SoftwareTech（软件技术）</option>
            <option value="ElectricalFeature">ElectricalFeature（电气特性）</option>
            </select>
        </div>
        <div class="form-item">
          <label class="form-label">节点名称：</label>
          <input 
            v-model="newNodeLabel" 
            placeholder="输入节点名称（必填）" 
            class="form-input"
            @input="validateNodeName"
          />
          <span v-if="nodeNameError" class="error-text">{{ nodeNameError }}</span>
        </div>
        <!-- 节点属性动态添加 -->
        <div class="props-section">
          <h3 class="props-subtitle">节点属性</h3>
          <div v-for="(prop, index) in newNodeProps" :key="index" class="prop-item">
            <input 
              v-model="prop.key" 
              placeholder="属性名（英文/数字/下划线）" 
              class="prop-input"
              @input="validateNewNodePropKey(index)"
            />
            <input 
              v-model="prop.value" 
              placeholder="属性值" 
              class="prop-input"
            />
            <span v-if="newNodePropErrors[index]" class="error-text inline-error">{{ newNodePropErrors[index] }}</span>
            <button @click="removeNewNodeProp(index)" class="remove-prop-btn">删除</button>
          </div>
          <button @click="addNewNodeProp" class="add-prop-btn">+ 添加属性</button>
        </div>
        <button 
          @click="submitAddNode" 
          class="submit-btn"
          :disabled="!newNodeLabel || !newNodeGroup || Object.values(newNodePropErrors).some(err => err)"
        >提交新增</button>
      </div>
    </div>

    <!-- 添加关系面板（右侧滑出） -->
    <div class="add-edge-panel" :class="{ 'active': showAddEdgePanel }">
      <div class="panel-close-btn" @click="showAddEdgePanel = false">×</div>
      <div class="panel-content">
        <h2 class="panel-title">新增关系</h2>
        <div class="form-item">
          <label class="form-label">起始节点：</label>
          <select v-model="newEdgeFrom" class="form-select">
            <option value="">-- 选择起始节点 --</option>
            <option v-for="node in allNodes" :key="node.id" :value="node.id">{{ node.label }} [{{ node.group }}]</option>
          </select>
        </div>
        <div class="form-item">
          <label class="form-label">终止节点：</label>
          <select v-model="newEdgeTo" class="form-select">
            <option value="">-- 选择终止节点 --</option>
            <option v-for="node in allNodes" :key="node.id" :value="node.id">{{ node.label }} [{{ node.group }}]</option>
          </select>
          <span v-if="edgeNodeError" class="error-text">{{ edgeNodeError }}</span>
        </div>
        <div class="form-item">
          <label class="form-label">关系类型：</label>
          <input 
            v-model="newEdgeLabel" 
            placeholder="输入关系类型（如：包含、依赖、应用于）" 
            class="form-input"
            @input="validateEdgeLabel"
          />
          <span v-if="edgeLabelError" class="error-text">{{ edgeLabelError }}</span>
        </div>
        <!-- 关系属性动态添加 -->
        <div class="props-section">
          <h3 class="props-subtitle">关系属性</h3>
          <div v-for="(prop, index) in newEdgeProps" :key="index" class="prop-item">
            <input 
              v-model="prop.key" 
              placeholder="属性名（英文/数字/下划线）" 
              class="prop-input"
              @input="validateNewEdgePropKey(index)"
            />
            <input 
              v-model="prop.value" 
              placeholder="属性值" 
              class="prop-input"
            />
            <span v-if="newEdgePropErrors[index]" class="error-text inline-error">{{ newEdgePropErrors[index] }}</span>
            <button @click="removeNewEdgeProp(index)" class="remove-prop-btn">删除</button>
          </div>
          <button @click="addNewEdgeProp" class="add-prop-btn">+ 添加属性</button>
        </div>
        <button 
          @click="submitAddEdge" 
          class="submit-btn"
          :disabled="!newEdgeFrom || !newEdgeTo || !newEdgeLabel || Object.values(newEdgePropErrors).some(err => err)"
        >提交新增</button>
      </div>
    </div>




     <!-- 图片预览弹窗 -->
     <div class="image-preview-modal" v-if="previewImageUrl" @click="closeImagePreview">
       <!-- 阻止点击图片区域触发关闭（事件冒泡） -->
       <div class="preview-content" @click.stop>
         <!-- 关闭按钮 -->
         <span class="preview-close-btn" @click="closeImagePreview">×</span>
         <!-- 预览图片：展示选中的图片URL -->
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
// 导入封装的API函数
import { 
  getGraphData, 
  addNodeProperty, 
  updateNodeProperty, 
  deleteNodeProperty, 
  deleteNode as deleteNodeApi, 
  exportGraphData,
  createNode, // 新增
  createEdge
} from '@/api/neo4jApi';

const router = useRouter();
const goToBatchImport = () => {
  router.push('/admin/batch-import'); // 和路由配置的path一致
};
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
const filteredTypes = ref([]); // 筛选的节点类型
const loading = ref(false);

// 新增属性相关变量
const newPropKey = ref('');       // 新增属性名
const newPropValue = ref('');     // 新增属性值
const propKeyError = ref('');     // 属性名校验错误提示

// 新增节点相关变量
const showAddNodePanel = ref(false);
const newNodeLabel = ref('');     // 新增节点名称
const newNodeGroup = ref('');     // 新增节点类型
const newNodeProps = ref([{ key: '', value: '' }]); // 新增节点属性
const newNodePropErrors = ref({}); // 新增节点属性错误提示
const nodeNameError = ref('');    // 节点名称错误提示

// 新增关系相关变量
const showAddEdgePanel = ref(false);
const newEdgeFrom = ref('');      // 关系起始节点ID
const newEdgeTo = ref('');        // 关系终止节点ID
const newEdgeLabel = ref('');     // 关系类型
const newEdgeProps = ref([{ key: '', value: '' }]); // 新增关系属性
const newEdgePropErrors = ref({}); // 新增关系属性错误提示
const edgeLabelError = ref('');   // 关系类型错误提示
const edgeNodeError = ref('');    // 关系节点选择错误提示

// 获取用户信息
const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'));
if (!userInfo.value || userInfo.value.role !== 'admin') {
  router.push('/login');
}

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

// 所有节点类型（计算属性）
const allNodeTypes = computed(() => {
  const types = new Set(allNodes.value.map(node => node.group));
  return Array.from(types);
});

// 获取节点原始属性
const getNodeOriginalProperties = (node) => {
  if (!node || !node.properties) return {};
  return { ...node.properties };
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

const previewImageUrl = ref(''); //预览图片的URL

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
        const props = Object.values(node.properties || {});
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
};

// 刷新图谱
const refreshGraph = () => {
  initGraph();
};

// 清空选中
const clearAll = () => {
  selectedNode.value = null;
  resetSearch();
};

// 查看关联节点
const showRelatedNodes = () => {
  if (!selectedNode.value) {
    alert('请先选中一个节点后再查看关联节点！');
    return;
  }
  
  const nodeId = selectedNode.value.id;
  // 筛选关联边
  const relatedEdges = allEdges.value.filter(edge => edge.from === nodeId || edge.to === nodeId);
  
  // 提取关联节点ID（排除自身）
  const relatedNodeIds = new Set();
  relatedEdges.forEach(edge => {
    if (edge.from !== nodeId) relatedNodeIds.add(edge.from);
    if (edge.to !== nodeId) relatedNodeIds.add(edge.to);
  });
  
  const relatedNodeList = Array.from(relatedNodeIds);
  const relatedNodes = allNodes.value.filter(node => relatedNodeIds.has(node.id));

  // 边界处理：无关联节点
  if (relatedNodeList.length === 0) {
    alert(`【${selectedNode.value.label}】暂无关联节点`);
    // 仅聚焦当前节点
    network.focus(nodeId, {
      scale: 1.2,
      animation: { duration: 800, easingFunction: 'easeInOutQuad' }
    });
    return;
  }

  // 画布聚焦关联节点
  network.focus(relatedNodeList, {
    scale: 1.1,
    animation: { duration: 800, easingFunction: 'easeInOutQuad' }
  });

  // 黄色边框高亮（保留节点原有背景色，仅修改边框）
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

  // 友好的提示弹窗
  alert(`【${selectedNode.value.label}】共找到 ${relatedNodeList.length} 个关联节点，${relatedEdges.length} 条关联关系
已用黄色边框高亮显示关联节点，红色边框为当前选中节点`);
};

// 导出数据（使用封装API）
const exportData = async () => {
  try {
    const blob = await exportGraphData();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `neo4j_graph_data_${new Date().getTime()}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
    alert('数据导出成功！');
  } catch (error) {
    console.error('导出数据失败:', error);
    alert(`导出失败：${error.message}`);
  }
};

// 删除节点（使用封装API）
const deleteNode = async () => {
  if (!selectedNode.value) return;
  if (!confirm(`确定删除节点【${selectedNode.value.label}】吗？此操作不可恢复！`)) return;
  
  const nodeId = selectedNode.value.id;
  try {
    await deleteNodeApi(nodeId);
    
    // 前端同步更新
    allNodes.value = allNodes.value.filter(node => node.id !== nodeId);
    allEdges.value = allEdges.value.filter(edge => edge.from !== nodeId && edge.to !== nodeId);
    network.body.data.nodes.remove(nodeId);
    network.body.data.edges.remove(allEdges.value.filter(edge => edge.from === nodeId || edge.to === nodeId).map(edge => edge.id));
    selectedNode.value = null;
    alert('节点删除成功！');
  } catch (error) {
    console.error('删除节点失败:', error);
    alert(`删除失败：${error.message}`);
  }
};

// ========== 节点属性增删改核心方法（使用封装API） ==========
// 1. 校验属性名（限英文/数字/下划线，且不能重复）
const validatePropKey = () => {
  const key = newPropKey.value.trim();
  const originalProps = getNodeOriginalProperties(selectedNode.value);
  
  // 空值校验
  if (!key) {
    propKeyError.value = '属性名不能为空';
    return;
  }
  
  // 格式校验（仅英文、数字、下划线）
  const reg = /^[a-zA-Z0-9_]+$/;
  if (!reg.test(key)) {
    propKeyError.value = '属性名仅支持英文、数字、下划线';
    return;
  }
  
  // 重复校验
  if (originalProps.hasOwnProperty(key)) {
    propKeyError.value = '该属性名已存在';
    return;
  }
  
  // 校验通过
  propKeyError.value = '';
};

// 2. 新增属性（使用封装API）
const addProperty = async () => {
  if (!selectedNode.value || !newPropKey.value || propKeyError.value) return;
  
  const nodeId = selectedNode.value.id;
  const propKey = newPropKey.value.trim();
  const propValue = newPropValue.value.trim();
  
  try {
    await addNodeProperty(nodeId, propKey, propValue);
    
    // 前端同步更新
    selectedNode.value.properties[propKey] = propValue;
    // 刷新图谱节点属性
    network.body.data.nodes.update([{
      id: nodeId,
      properties: { ...selectedNode.value.properties }
    }]);
    
    // 清空输入框
    newPropKey.value = '';
    newPropValue.value = '';
    alert('属性新增成功！');
  } catch (error) {
    console.error('新增属性失败:', error);
    alert(`新增失败：${error.message}`);
  }
};

// 3. 修改属性（使用封装API）
const editProperty = async (key) => {
  if (!selectedNode.value) return;
  const currentValue = selectedNode.value.properties[key];
  const newValue = prompt(`编辑属性【${key}】`, currentValue);
  
  if (newValue === null) return; // 取消编辑
  
  const nodeId = selectedNode.value.id;
  try {
    await updateNodeProperty(nodeId, key, newValue);
    
    // 前端同步更新
    selectedNode.value.properties[key] = newValue;
    network.body.data.nodes.update([{
      id: nodeId,
      properties: { ...selectedNode.value.properties }
    }]);
    alert('属性修改成功！');
  } catch (error) {
    console.error('修改属性失败:', error);
    alert(`修改失败：${error.message}`);
  }
};

// 4. 删除属性（使用封装API）
const deleteProperty = async (key) => {
  if (!selectedNode.value) return;
  if (!confirm(`确定删除属性【${key}】吗？此操作不可恢复！`)) return;
  
  const nodeId = selectedNode.value.id;
  try {
    await deleteNodeProperty(nodeId, key);
    
    // 前端同步更新
    delete selectedNode.value.properties[key];
    network.body.data.nodes.update([{
      id: nodeId,
      properties: { ...selectedNode.value.properties }
    }]);
    alert('属性删除成功！');
  } catch (error) {
    console.error('删除属性失败:', error);
    alert(`删除失败：${error.message}`);
  }
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
    loading.value = true;

    // 请求 Neo4j 数据（使用封装API）
    const result = await getGraphData(1000);
    if (result.status !== 200) throw new Error(result.message || '数据返回异常');
    const { nodes: rawNodes, edges: rawEdges } = result.data;

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
  } finally {
    loading.value = false;
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

// ========== 新增节点相关方法 ==========
// 校验节点名称
const validateNodeName = () => {
  const name = newNodeLabel.value.trim();
  if (!name) {
    nodeNameError.value = '节点名称不能为空';
  } else {
    nodeNameError.value = '';
  }
};

// 校验新增节点的属性名
const validateNewNodePropKey = (index) => {
  const key = newNodeProps.value[index].key.trim();
  const reg = /^[a-zA-Z0-9_]+$/;
  
  if (!key) {
    newNodePropErrors.value[index] = '属性名不能为空';
  } else if (!reg.test(key)) {
    newNodePropErrors.value[index] = '仅支持英文、数字、下划线';
  } else {
    // 检查属性名重复
    const duplicate = newNodeProps.value.some((prop, i) => i !== index && prop.key.trim() === key);
    newNodePropErrors.value[index] = duplicate ? '属性名重复' : '';
  }
};

// 添加新增节点的属性行
const addNewNodeProp = () => {
  newNodeProps.value.push({ key: '', value: '' });
  // 初始化错误提示
  newNodePropErrors.value[newNodeProps.value.length - 1] = '';
};

// 删除新增节点的属性行
const removeNewNodeProp = (index) => {
  newNodeProps.value.splice(index, 1);
  // 删除对应的错误提示
  const newErrors = { ...newNodePropErrors.value };
  delete newErrors[index];
  newNodePropErrors.value = newErrors;
};

// 2. 完善提交新增节点方法
const submitAddNode = async () => {
  if (!newNodeLabel.value || !newNodeGroup.value) return;

  const properties = {};
  newNodeProps.value.forEach(p => {
    if (p.key.trim()) properties[p.key.trim()] = p.value;
  });

  try {
    const result = await createNode({
      label: newNodeLabel.value,
      group: newNodeGroup.value,
      properties
    });

    alert('节点创建成功！');
    showAddNodePanel.value = false;
    // 重置表单
    newNodeLabel.value = '';
    newNodeProps.value = [{ key: '', value: '' }];
    // 刷新图谱以显示新节点
    refreshGraph(); 
  } catch (error) {
    alert(`创建失败：${error.message}`);
  }
};

// ========== 新增关系相关方法 ==========
// 校验关系类型
const validateEdgeLabel = () => {
  const label = newEdgeLabel.value.trim();
  if (!label) {
    edgeLabelError.value = '关系类型不能为空';
  } else {
    edgeLabelError.value = '';
  }
};

// 校验新增关系的属性名
const validateNewEdgePropKey = (index) => {
  const key = newEdgeProps.value[index].key.trim();
  const reg = /^[a-zA-Z0-9_]+$/;
  
  if (!key) {
    newEdgePropErrors.value[index] = '属性名不能为空';
  } else if (!reg.test(key)) {
    newEdgePropErrors.value[index] = '仅支持英文、数字、下划线';
  } else {
    // 检查属性名重复
    const duplicate = newEdgeProps.value.some((prop, i) => i !== index && prop.key.trim() === key);
    newEdgePropErrors.value[index] = duplicate ? '属性名重复' : '';
  }
};

// 校验关系节点选择
const validateEdgeNodes = () => {
  if (newEdgeFrom.value === newEdgeTo.value && newEdgeFrom.value) {
    edgeNodeError.value = '起始节点和终止节点不能相同';
    return false;
  } else {
    edgeNodeError.value = '';
    return true;
  }
};

// 添加新增关系的属性行
const addNewEdgeProp = () => {
  newEdgeProps.value.push({ key: '', value: '' });
  // 初始化错误提示
  newEdgePropErrors.value[newEdgeProps.value.length - 1] = '';
};

// 删除新增关系的属性行
const removeNewEdgeProp = (index) => {
  newEdgeProps.value.splice(index, 1);
  // 删除对应的错误提示
  const newErrors = { ...newEdgePropErrors.value };
  delete newErrors[index];
  newEdgePropErrors.value = newErrors;
};

// 3. 完善提交新增关系方法
const submitAddEdge = async () => {
  if (!newEdgeFrom.value || !newEdgeTo.value || !newEdgeLabel.value) return;

  const properties = {};
  newEdgeProps.value.forEach(p => {
    if (p.key.trim()) properties[p.key.trim()] = p.value;
  });

  try {
    await createEdge({
      from: newEdgeFrom.value,
      to: newEdgeTo.value,
      label: newEdgeLabel.value,
      properties
    });

    alert('关系创建成功！');
    showAddEdgePanel.value = false;
    // 重置表单
    newEdgeFrom.value = '';
    newEdgeTo.value = '';
    newEdgeLabel.value = '';
    newEdgeProps.value = [{ key: '', value: '' }];
    // 刷新图谱以显示新关系
    refreshGraph();
  } catch (error) {
    alert(`创建失败：${error.message}`);
  }
};

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
.admin-graph-page-container {
  display: flex;
  flex-direction: column;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background-color: #f5f5f5;
}

/* 顶部功能栏 - 保留原有逻辑，适配新样式规范 */
.admin-top-bar {
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

/* 搜索栏 - 复用参考样式 */
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

/* 右侧详情栏 - 核心样式统一 */
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

.edge-detail-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  height: 100%;
  background: #fff;
  box-shadow: -2px 0 10px rgba(0,0,0,0.1);
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 100;
  overflow-y: auto;
}
.edge-detail-panel.active {
  transform: translateX(0);
}
.edge-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
}
.edge-name {
  margin: 0;
  font-size: 18px;
}
.edge-category {
  margin-left: 10px;
  color: #666;
  font-size: 14px;
}
.delete-edge-btn {
  margin-top: 10px;
}
.edge-props-section {
  padding: 20px;
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

.delete-node-btn.danger-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  margin-left: 10px;
  background: #f44336;
  color: white;
}

.delete-node-btn.danger-btn:hover {
  background: #d32f2f;
}

/* 管理员操作区 */
.admin-actions {
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

.action-btn:hover {
  background: #1976D2;
}

/* ========== 核心优化：多媒体展示样式 ========== */
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

/* 图片网格布局 */
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
  transition: box-shadow 0.2s ease;
}

.image-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

/* 视频列表布局 */
.videos-grid {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.video-item {
  border: 1px solid #eee;
  border-radius: 4px;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.video-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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

/* 无多媒体提示 */
.no-media {
  font-size: 14px;
  color: #999;
  font-style: italic;
  padding: 10px 0;
  text-align: center;
}

/* 节点属性区域样式 */
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
  width: 25%;
}

.prop-value-th {
  width: 60%;
}

.prop-op-th {
  width: 15%;
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

/* 新增属性输入框样式 */
.new-prop-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.new-prop-input:focus {
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.error-text {
  font-size: 12px;
  color: #f44336;
  margin-top: 4px;
  display: block;
}

.edit-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background: #2196F3;
  color: white;
  cursor: pointer;
  font-size: 12px;
  margin-right: 4px;
}

.delete-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background: #f44336;
  color: white;
  cursor: pointer;
  font-size: 12px;
}

.add-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  background: #4CAF50;
  color: white;
  cursor: pointer;
  font-size: 14px;
}

.add-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

/* 添加节点/关系面板样式 */
.add-node-panel, .add-edge-panel {
  width: 500px;
  height: 100%;
  background-color: white;
  box-shadow: -2px 0 15px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 0;
  right: 0;
  transform: translateX(100%);
  transition: transform 0.3s ease;
  z-index: 100;
  overflow-y: auto;
  padding: 20px 0;
  padding-top: 70px;
}

.add-node-panel.active, .add-edge-panel.active {
  transform: translateX(0);
}

.panel-title {
  font-size: 20px;
  color: #2c3e50;
  margin: 0 0 20px 0;
  font-weight: 600;
}

.form-item {
  margin-bottom: 15px;
}

.form-label {
  display: block;
  font-size: 14px;
  color: #2c3e50;
  margin-bottom: 6px;
  font-weight: 500;
}

.form-select, .form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.form-select:focus, .form-input:focus {
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.props-section {
  margin: 20px 0;
}

.props-subtitle {
  font-size: 16px;
  color: #34495e;
  margin: 0 0 15px 0;
  font-weight: 600;
}

.prop-item {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.prop-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 14px;
  outline: none;
}

.prop-input:focus {
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.2);
}

.inline-error {
  position: absolute;
  font-size: 12px;
  color: #f44336;
  margin-top: 28px;
}

.remove-prop-btn {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background: #f44336;
  color: white;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.add-prop-btn {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background: #4CAF50;
  color: white;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

.submit-btn {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 4px;
  background: #2196F3;
  color: white;
  cursor: pointer;
  font-size: 16px;
  margin-top: 20px;
}

.submit-btn:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

/* 图片预览弹窗样式 */
.image-preview-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.85); /* 半透明黑色遮罩 */
  z-index: 9999; /* 层级置顶 */
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-content {
  position: relative;
  max-width: 90%; /* 限制最大宽度，适配不同屏幕 */
  max-height: 90%; /* 限制最大高度 */
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
  border-radius: 50%; /* 圆形关闭按钮 */
}

.preview-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain; /* 保持图片比例，不拉伸 */
  border-radius: 4px;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .node-detail-panel, .add-node-panel, .add-edge-panel {
    width: 100%;
  }
  .search-bar {
    width: calc(100% - 30px);
  }
  .search-input-wrapper {
    flex-wrap: wrap;
  }
  .admin-top-bar {
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