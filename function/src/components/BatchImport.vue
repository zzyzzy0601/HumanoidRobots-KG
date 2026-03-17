<template>
  <div class="batch-import-container">
    <!-- 顶部返回栏 -->
    <div class="import-top-bar">
      <button @click="goBack" class="back-btn">← 返回图谱管理</button>
      <h2>数据批量导入</h2>
    </div>

    <!-- 导入核心区域 -->
    <div class="import-content">
      <!-- 1. 文件上传区域 -->
      <div class="file-upload-section">
        <h3>步骤1：选择导入文件</h3>
        <div class="upload-area" @click="triggerFileInput">
          <input 
            ref="fileInput" 
            type="file" 
            accept=".json" 
            class="file-input"
            @change="handleFileSelect"
          />
          <div v-if="!selectedFile" class="upload-placeholder">
            <span>点击上传JSON文件</span>
          </div>
          <div v-else class="file-selected">
            <span>已选择：{{ selectedFile.name }}</span>
            <button @click="clearFile" class="clear-btn">清空</button>
          </div>
        </div>
      </div>

      <!-- 2. 导入配置/预览区域 -->
      <div class="config-section" v-if="selectedFile && fileContent">
        <h3>步骤2：导入配置 & 数据预览</h3>
        <div class="preview-tip">
          <p>已解析JSON文件，可选择需要导入的节点/关系（自动补全默认属性）</p>
        </div>

        <!-- 节点预览区域 -->
        <div class="preview-section" v-if="fileContent.nodes && fileContent.nodes.length">
          <h4>节点列表 (共{{ fileContent.nodes.length }}条，选中{{ getSelectedCount('nodes') }}条)</h4>
          <div class="preview-list">
            <div 
              class="preview-item" 
              :class="{ 'disabled': !item.import, 'duplicate': item.isDuplicate }"
              v-for="(item, index) in fileContent.nodes" 
              :key="`node-${index}`"
            >
              <div class="item-content">
                <div class="item-label">【节点类型：{{ item.label }}】</div>
                <!-- 重名提示 -->
                <div class="duplicate-tip" v-if="item.isDuplicate">
                  ⚠️ 数据库中已存在同名节点，禁止导入
                </div>
                <!-- 全量展示节点属性（基于模板） -->
                <div class="item-props full-props">
                  <div 
                    class="prop-item" 
                    v-for="(defaultValue, key) in getNodeTemplate(item.label)" 
                    :key="`node-prop-${index}-${key}`"
                  >
                    <span class="prop-key">{{ key }}：</span>
                    <span class="prop-value">{{ formatPropValue(item.properties?.[key] ?? defaultValue) }}</span>
                    <span v-if="!item.properties?.hasOwnProperty(key)" class="default-tag">默认值</span>
                  </div>
                </div>
                <!-- 显示import状态 -->
                <div class="import-status" v-if="!item.import">
                  <span>已取消导入</span>
                </div>
              </div>
              <button 
                class="delete-btn" 
                @click="toggleImport('nodes', index)"
                :disabled="item.isDuplicate"
              >
                {{ item.import ? '取消导入' : '恢复导入' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 关系预览区域 -->
        <div class="preview-section" v-if="fileContent.relations && fileContent.relations.length">
          <h4>关系列表 (共{{ fileContent.relations.length }}条，选中{{ getSelectedCount('relations') }}条)</h4>
          <div class="preview-list">
            <div 
              class="preview-item" 
              :class="{ 'disabled': !item.import, 'duplicate': item.isDuplicate }"
              v-for="(item, index) in fileContent.relations" 
              :key="`relation-${index}`"
            >
              <div class="item-content">
                <div class="item-label">【关系类型：{{ item.type }}】</div>
                <!-- 重名提示 -->
                <div class="duplicate-tip" v-if="item.isDuplicate">
                  ⚠️ 关联节点存在重名或关系已存在，禁止导入
                </div>
                <!-- 基础关联信息 -->
                <div class="relation-basic">
                  <span>源节点：{{ item.start_node_label }}[{{ item.start_node_name }}]</span>
                  <span class="arrow">→</span>
                  <span>目标节点：{{ item.end_node_label }}[{{ item.end_node_name }}]</span>
                </div>
                <!-- 全量展示关系属性（基于模板） -->
                <div class="item-props full-props" v-if="Object.keys(getRelationTemplate(item.type)).length">
                  <div 
                    class="prop-item" 
                    v-for="(defaultValue, key) in getRelationTemplate(item.type)" 
                    :key="`relation-prop-${index}-${key}`"
                  >
                    <span class="prop-key">{{ key }}：</span>
                    <span class="prop-value">{{ formatPropValue(item.properties?.[key] ?? defaultValue) }}</span>
                    <span v-if="!item.properties?.hasOwnProperty(key)" class="default-tag">默认值</span>
                  </div>
                </div>
                <!-- 空属性提示 -->
                <div class="empty-props" v-if="!Object.keys(getRelationTemplate(item.type)).length">
                  无额外属性
                </div>
                <!-- 显示import状态 -->
                <div class="import-status" v-if="!item.import">
                  <span>已取消导入</span>
                </div>
              </div>
              <button 
                class="delete-btn" 
                @click="toggleImport('relations', index)"
                :disabled="item.isDuplicate"
              >
                {{ item.import ? '取消导入' : '恢复导入' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 空数据提示 -->
        <div class="empty-tip" v-if="!fileContent.nodes.length && !fileContent.relations.length">
          未检测到可导入的节点或关系数据
        </div>

        <button 
          @click="handleBatchImport" 
          class="import-btn"
          :disabled="!getTotalSelectedCount()"
        >
          开始批量导入（共选中 {{ getTotalSelectedCount() }} 条）
          <span v-if="hasDuplicateData" class="duplicate-tag">存在重名数据，将自动跳过</span>
        </button>
      </div>

      <!-- 加载状态 -->
      <div class="loading-section" v-if="selectedFile && !fileContent">
        <div class="loading-spinner"></div>
        <p>正在解析文件内容...</p>
      </div>

      <!-- 数据库检测加载状态 -->
      <div class="loading-section" v-if="checkingDuplicate">
        <div class="loading-spinner"></div>
        <p>正在检测数据库中重复数据...</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
// 引入Neo4j驱动（需先安装：npm install neo4j-driver）
import neo4j from 'neo4j-driver';

// 初始化路由
const router = useRouter();
const route = useRoute();

// -------------------------- Neo4j 数据库配置 --------------------------
const NEO4J_CONFIG = {
  uri: 'bolt://localhost:7687', // 替换为你的Neo4j地址
  user: 'neo4j', // 替换为你的用户名
  password: 'Youbuding357' // 替换为你的密码
};

// 创建Neo4j驱动实例
const driver = neo4j.driver(
  NEO4J_CONFIG.uri,
  neo4j.auth.basic(NEO4J_CONFIG.user, NEO4J_CONFIG.password)
);

// 测试数据库连接
const testNeo4jConnection = async () => {
  try {
    const session = driver.session();
    await session.run('MATCH (n) RETURN count(n) AS count LIMIT 1');
    await session.close();
    console.log('Neo4j 数据库连接成功');
    return true;
  } catch (error) {
    console.error('Neo4j 数据库连接失败：', error);
    alert('数据库连接失败，请检查配置！');
    return false;
  }
};

// 初始化时测试连接
testNeo4jConnection();

// -------------------------- 模板定义 --------------------------
// 节点模板定义
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

// 关系模板定义
const RELATION_TEMPLATES = {
  "DEVELOPE": {"year": "无", "version": "无"},
  "CONTAINS": {"description": "无"},
  "APPLIED_IN": {"maturity": "无", "case": "无"},
  "HAS_PART": {},
  "IMPLEMENTS": {},
  "USES_TECH": {},
  "FEATURE": {}
};

// -------------------------- 状态管理 --------------------------
// 文件相关状态
const fileInput = ref(null);
const selectedFile = ref(null);
const fileContent = ref(null);
const checkingDuplicate = ref(false); // 检测重名加载状态

// -------------------------- 核心逻辑 --------------------------
// 修复返回逻辑
const goBack = () => {
  if (router.options.history.state.back) {
    router.go(-1);
  } else {
    router.push('/admin/graph').catch(err => {
      router.push('/AdminGraph').catch(() => {
        alert('图谱管理页面路径配置错误，请检查路由！');
      });
    });
  }
};

// 触发文件选择框
const triggerFileInput = () => {
  fileInput.value.click();
};

// 选择文件后的处理
const handleFileSelect = async (e) => {
  const file = e.target.files[0];
  if (file) {
    if (!file.name.endsWith('.json')) {
      alert('仅支持JSON格式文件！');
      return;
    }
    selectedFile.value = file;
    fileContent.value = null;
    // 解析文件
    await parseFileContent(file);
    // 解析完成后检测重名
    if (fileContent.value) {
      await checkDuplicateData();
    }
  }
};

// 获取节点模板
const getNodeTemplate = (label) => {
  return NODE_TEMPLATES[label] || {};
};

// 获取关系模板
const getRelationTemplate = (type) => {
  return RELATION_TEMPLATES[type] || {};
};

// 补全节点属性
const completeNodeProps = (node) => {
  const template = getNodeTemplate(node.label);
  const completedProps = { ...template };
  
  if (node.properties) {
    Object.keys(node.properties).forEach(key => {
      if (node.properties[key] !== undefined && node.properties[key] !== null) {
        completedProps[key] = node.properties[key];
      }
    });
  }
  
  return {
    ...node,
    properties: completedProps,
    import: node.import ?? true,
    isDuplicate: false // 新增重名标记
  };
};

// 补全关系属性
const completeRelationProps = (relation) => {
  const template = getRelationTemplate(relation.type);
  const completedProps = { ...template };
  
  if (relation.properties) {
    Object.keys(relation.properties).forEach(key => {
      if (relation.properties[key] !== undefined && relation.properties[key] !== null) {
        completedProps[key] = relation.properties[key];
      }
    });
  }
  
  return {
    ...relation,
    properties: completedProps,
    import: relation.import ?? true,
    isDuplicate: false // 新增重名标记
  };
};

// 解析文件内容
const parseFileContent = (file) => {
  return new Promise((resolve) => {
    try {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = JSON.parse(e.target.result);
          
          // 处理节点
          content.nodes = (content.nodes || []).map(node => {
            if (!node.label) {
              alert(`节点缺少必要字段label，已跳过该节点: ${JSON.stringify(node)}`);
              return null;
            }
            return completeNodeProps(node);
          }).filter(Boolean);
          
          // 处理关系
          content.relations = (content.relations || []).map(relation => {
            const requiredFields = ['type', 'start_node_label', 'start_node_name', 'end_node_label', 'end_node_name'];
            const missingFields = requiredFields.filter(field => !relation[field]);
            if (missingFields.length) {
              alert(`关系缺少必要字段${missingFields.join(', ')}，已跳过该关系: ${JSON.stringify(relation)}`);
              return null;
            }
            return completeRelationProps(relation);
          }).filter(Boolean);
          
          fileContent.value = content;
          resolve(content);
        } catch (err) {
          alert(`文件解析失败：${err.message}，请检查JSON格式！`);
          selectedFile.value = null;
          fileInput.value.value = '';
          resolve(null);
        }
      };
      reader.readAsText(file);
    } catch (error) {
      console.error('文件解析失败：', error);
      alert(`文件解析失败：${error.message}`);
      resolve(null);
    }
  });
};

// 检测数据库中重复数据
const checkDuplicateData = async () => {
  if (!fileContent.value) return;
  
  checkingDuplicate.value = true;
  const session = driver.session();
  
  try {
    // 1. 检测节点重名
    if (fileContent.value.nodes.length) {
      for (const node of fileContent.value.nodes) {
        // Cypher查询：检查指定标签+name的节点是否存在
        const result = await session.run(
          `MATCH (n:${node.label} {name: $name}) RETURN count(n) AS count`,
          { name: node.properties.name }
        );
        const count = result.records[0].get('count').toNumber();
        node.isDuplicate = count > 0; // 标记为重名
        // 重名节点自动取消导入
        if (node.isDuplicate) {
          node.import = false;
        }
      }
    }

    // 2. 检测关系关联节点重名 + 关系重复
    if (fileContent.value.relations.length) {
      for (const relation of fileContent.value.relations) {
        // 检查源节点是否存在
        const startNodeResult = await session.run(
          `MATCH (n:${relation.start_node_label} {name: $name}) RETURN count(n) AS count`,
          { name: relation.start_node_name }
        );
        const startNodeExists = startNodeResult.records[0].get('count').toNumber() > 0;

        // 检查目标节点是否存在
        const endNodeResult = await session.run(
          `MATCH (n:${relation.end_node_label} {name: $name}) RETURN count(n) AS count`,
          { name: relation.end_node_name }
        );
        const endNodeExists = endNodeResult.records[0].get('count').toNumber() > 0;

        // 检查关系是否已存在（源节点→目标节点的指定类型关系）
        const relationResult = await session.run(
          `MATCH (a:${relation.start_node_label} {name: $startName})-[r:${relation.type}]->(b:${relation.end_node_label} {name: $endName}) RETURN count(r) AS count`,
          { 
            startName: relation.start_node_name,
            endName: relation.end_node_name
          }
        );
        const relationExists = relationResult.records[0].get('count').toNumber() > 0;

        // 只要关联节点不存在 或 关系已存在，都标记为重名/重复
        relation.isDuplicate = !startNodeExists || !endNodeExists || relationExists;
        // 重复关系自动取消导入
        if (relation.isDuplicate) {
          relation.import = false;
        }
      }
    }
  } catch (error) {
    console.error('检测重复数据失败：', error);
    alert(`检测重复数据失败：${error.message}`);
  } finally {
    await session.close();
    checkingDuplicate.value = false;
  }
};

// 清空选中的文件
const clearFile = () => {
  selectedFile.value = null;
  fileContent.value = null;
  fileInput.value.value = '';
};

// 格式化属性值
const formatPropValue = (value) => {
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value, null, 2);
  }
  if (typeof value === 'string' && value.length > 100) {
    return value.substring(0, 100) + '...';
  }
  return value;
};

// 切换导入状态（重名数据禁止切换）
const toggleImport = (type, index) => {
  if (fileContent.value[type] && fileContent.value[type][index]) {
    const item = fileContent.value[type][index];
    // 重名数据禁止修改导入状态
    if (!item.isDuplicate) {
      item.import = !item.import;
    }
  }
};

// 获取选中的数量
const getSelectedCount = (type) => {
  if (!fileContent.value || !fileContent.value[type]) return 0;
  return fileContent.value[type].filter(item => item.import).length;
};

// 获取总选中数量
const getTotalSelectedCount = () => {
  const nodeCount = getSelectedCount('nodes');
  const relationCount = getSelectedCount('relations');
  return nodeCount + relationCount;
};

// 检测是否存在重名数据（仅用于提示，不再禁用按钮）
const hasDuplicateData = computed(() => {
  if (!fileContent.value) return false;
  
  // 检查节点是否有重名
  const hasDuplicateNodes = fileContent.value.nodes.some(node => node.isDuplicate);
  // 检查关系是否有重复
  const hasDuplicateRelations = fileContent.value.relations.some(relation => relation.isDuplicate);
  
  return hasDuplicateNodes || hasDuplicateRelations;
});

// 批量导入核心逻辑（写入Neo4j）
const handleBatchImport = async () => {
  if (!selectedFile.value || !fileContent.value) return;

  // 过滤出需要导入的条目（排除重名+取消导入的）
  const importData = {
    nodes: fileContent.value.nodes?.filter(node => node.import && !node.isDuplicate) || [],
    relations: fileContent.value.relations?.filter(relation => relation.import && !relation.isDuplicate) || []
  };

  if (importData.nodes.length === 0 && importData.relations.length === 0) {
    alert('没有可导入的有效数据（已过滤重名/取消导入的条目）！');
    return;
  }

  const session = driver.session();
  try {
    // 开启事务
    const tx = session.beginTransaction();
    
    // 统计导入数量
    let importedNodes = 0;
    let importedRelations = 0;
    
    // 1. 导入节点
    if (importData.nodes.length) {
      for (const node of importData.nodes) {
        // 构建节点创建语句（动态标签+属性）
        const props = { ...node.properties };
        // 移除空值（可选）
        Object.keys(props).forEach(key => {
          if (props[key] === '无' || props[key] === null || props[key] === undefined) {
            delete props[key];
          }
        });
        
        await tx.run(
          `CREATE (n:${node.label} $props) RETURN n`,
          { props }
        );
        importedNodes++;
      }
    }

    // 2. 导入关系（先匹配源/目标节点，再创建关系）
    if (importData.relations.length) {
      for (const relation of importData.relations) {
        // 构建关系属性
        const props = { ...relation.properties };
        Object.keys(props).forEach(key => {
          if (props[key] === '无' || props[key] === null || props[key] === undefined) {
            delete props[key];
          }
        });

        await tx.run(
          `MATCH (a:${relation.start_node_label} {name: $startName}), (b:${relation.end_node_label} {name: $endName}) 
           CREATE (a)-[r:${relation.type} $props]->(b) RETURN r`,
          {
            startName: relation.start_node_name,
            endName: relation.end_node_name,
            props
          }
        );
        importedRelations++;
      }
    }

    // 提交事务
    await tx.commit();
    
    // 计算跳过的数量
    const skippedNodes = fileContent.value.nodes.filter(node => !node.import || node.isDuplicate).length;
    const skippedRelations = fileContent.value.relations.filter(relation => !relation.import || relation.isDuplicate).length;
    
    alert(`批量导入成功！
已导入：${importedNodes} 个节点，${importedRelations} 个关系
自动跳过：${skippedNodes} 个节点，${skippedRelations} 个关系（重名/取消导入）`);
    goBack();
  } catch (error) {
    // 回滚事务
    await tx.rollback();
    console.error('批量导入失败：', error);
    alert(`导入失败：${error.message}`);
  } finally {
    await session.close();
  }
};
</script>

<style scoped>
/* 原有样式保持不变，新增以下样式 */
/* 重名数据样式 */
.preview-item.duplicate {
  border-left-color: #f44336;
  background: #fff0f0;
}

.duplicate-tip {
  color: #f44336;
  font-size: 12px;
  margin-bottom: 8px;
  padding: 4px 8px;
  background: #ffebee;
  border-radius: 4px;
}

.duplicate-tag {
  margin-left: 10px;
  font-size: 12px;
  color: #f44336;
}

/* 禁用状态下的按钮样式增强 */
.delete-btn:disabled {
  background: #999;
  cursor: not-allowed;
  opacity: 0.6;
}

/* 原有样式 */
.batch-import-container {
  width: 100%;
  min-height: 100vh;
  background: #f5f5f5;
  box-sizing: border-box;
  padding-bottom: 50px;
}

.import-top-bar {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  background: #fff;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  gap: 20px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.back-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  background: #42b983;
  color: #fff;
  cursor: pointer;
  font-size: 14px;
}

.back-btn:hover {
  background: #359469;
}

.import-top-bar h2 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.import-content {
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
}

.file-upload-section, .config-section {
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  margin-bottom: 20px;
}

.file-upload-section h3, .config-section h3 {
  margin: 0 0 15px 0;
  font-size: 16px;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 8px;
}

.upload-area {
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  margin-top: 10px;
  transition: border-color 0.3s;
}

.upload-area:hover {
  border-color: #42b983;
}

.file-input {
  display: none;
}

.upload-placeholder span {
  color: #999;
  font-size: 14px;
}

.file-selected {
  color: #333;
  font-size: 14px;
}

.clear-btn {
  margin-left: 15px;
  padding: 4px 8px;
  background: #f44336;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.preview-tip {
  color: #e67e22;
  font-size: 12px;
  margin: 10px 0;
  padding: 8px;
  background: #fff8e1;
  border-radius: 4px;
}

.preview-section {
  margin: 20px 0;
}

.preview-section h4 {
  font-size: 15px;
  color: #444;
  margin: 0 0 10px 0;
  padding-bottom: 5px;
  border-bottom: 1px solid #eee;
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 600px;
  overflow-y: auto;
  padding-right: 8px;
}

.preview-list::-webkit-scrollbar {
  width: 6px;
}

.preview-list::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.preview-list::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 3px;
}

.preview-list::-webkit-scrollbar-thumb:hover {
  background: #999;
}

.preview-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
  border-left: 3px solid #42b983;
  transition: all 0.2s;
}

.preview-item.disabled {
  background: #fafafa;
  border-left-color: #ccc;
  opacity: 0.8;
}

.item-content {
  flex: 1;
  overflow: hidden;
  margin-right: 15px;
}

.item-label {
  font-weight: 600;
  color: #333;
  margin-bottom: 10px;
  font-size: 14px;
}

.full-props {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #555;
  max-height: 200px;
  overflow-y: auto;
  padding-right: 5px;
}

.full-props::-webkit-scrollbar {
  width: 4px;
}

.full-props::-webkit-scrollbar-thumb {
  background: #ddd;
}

.prop-item {
  display: flex;
  flex-wrap: wrap;
  word-break: break-all;
  padding: 4px 0;
  border-bottom: 1px solid #f0f0f0;
  align-items: center;
}

.prop-key {
  font-weight: 500;
  color: #333;
  min-width: 80px;
}

.prop-value {
  flex: 1;
  color: #666;
  line-height: 1.4;
}

.prop-value:hover {
  background: #f5f5f5;
}

.default-tag {
  font-size: 11px;
  color: #999;
  background: #f0f0f0;
  padding: 1px 6px;
  border-radius: 3px;
  margin-left: 8px;
}

.relation-basic {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
  color: #444;
  flex-wrap: wrap;
}

.arrow {
  color: #42b983;
  font-weight: bold;
}

.empty-props {
  font-size: 12px;
  color: #999;
  margin: 8px 0;
  font-style: italic;
}

.import-status {
  margin-top: 8px;
  font-size: 12px;
  color: #f44336;
}

.delete-btn {
  padding: 8px 12px;
  background: #f44336;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  transition: background 0.2s;
  margin-top: 5px;
  flex-shrink: 0;
}

.delete-btn:hover {
  background: #d32f2f;
}

.preview-item.disabled .delete-btn {
  background: #42b983;
}

.preview-item.disabled .delete-btn:hover {
  background: #359469;
}

.empty-tip {
  text-align: center;
  padding: 20px;
  color: #999;
  font-size: 14px;
}

.loading-section {
  text-align: center;
  padding: 40px;
  color: #666;
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #eee;
  border-top: 3px solid #42b983;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.import-btn {
  padding: 12px 30px;
  background: #42b983;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 20px;
  transition: background 0.3s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.import-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.import-btn:hover:not(:disabled) {
  background: #359469;
}
</style>