<template>
  <div class="graph-page">
    <h1 style="text-align: center; padding: 10px 0;">人形机器人知识图谱展示</h1>
    <Neo4jGraph />
  </div>
</template>

<script setup>
import Neo4jGraph from '../components/Neo4jGraph.vue';
</script>

<style scoped>
.graph-page {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}
</style>