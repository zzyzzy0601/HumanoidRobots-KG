## 部署运行
1. 初始化 Neo4j 数据库
   
进入项目根目录下的data文件夹，修改neo4j密码，再运行creator.py创建数据库
```
python creator.py
```
2. 配置数据库连接
   
打开function/server/index.js文件，修改Neo4j数据库账户密码

打开function/server/db.js文件，修改MySQL数据库账户密码

3. 安装依赖并启动服务
   
进入function目录，安装项目依赖（首次运行）
```
npm install
```
终端一：启动前端开发服务器
```
npm run dev
```
终端二：启动后端 Node.js 服务
```
node server/index.js
```
4. 打开浏览器，访问 http://localhost:5173

## 项目结构
```
前端：vue3+vite
后端：node.js+express

HumanoidRobots-KG/  <-- 项目根目录
|
+- package.json                  <-- 根目录npm配置文件
+- package-lock.json             <-- 根目录依赖锁定文件
|
+- data/                 <-- 数据获取与处理目录
|  +- spider1.py               <-- 国内人形机器人企业官网爬虫脚本
|  +- spider2.py               <-- 国外人形机器人企业官网爬虫脚本
|  +- DEEPSEEK_API.py          <-- 调用大模型api对数据进行结构化处理
|  +- result.json              <-- 爬虫原始采集数据
|  +- data.json                <-- 经大模型处理后的结构化数据
|  +- creator.py               <-- 知识图谱数据批量写入Neo4j数据库脚本
|
+- function/             <-- 系统核心功能目录
|  +- src/                  <-- 前端源码目录
|  |  +- assets/                <-- 静态文件目录
|  |  |  +- css/                  <-- 存放css文件
|  |  +- api/                   <-- API请求封装层
|  |  |  +- neo4jApi.js           <-- 封装请求获取Neo4j图谱数据
|  |  +- components/            <-- vue组件目录
|  |  |  +- AdminGraph.vue        <-- 管理员界面
|  |  |  +- Login.vue             <-- 登录界面
|  |  |  +- Neo4jGraph.vue        <-- 普通用户界面
|  |  |  +- BatchImport.vue       <-- 批量导入界面
|  |  |  +- Register.vue          <-- 用户注册界面
|  |  +- router/                <-- 路由配置目录
|  |  |  +- index.js              <-- 定义路由规则与页面跳转逻辑
|  |  +- view/                  <-- 页面视图目录
|  |  |  +- Neo4jGraph.vue        <-- 核心页面视图文件
|  |  +- App.vue              <-- 根组件
|  |  +- main.js              <-- 项目入口文件
|  +- server/              <-- Express.js后端接口服务目录
|  |  +- db.js                <-- MySQL连接配置文件
|  |  +- index.js             <-- 图谱后端接口文件
|  +- public/              <-- 默认静态资源目录
|  |  +- image                <-- 多媒体资源存放目录
```
