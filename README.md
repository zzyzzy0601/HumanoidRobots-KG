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
HumanoidRobots-KG/  <-- 项目根目录
|
+- package.json                  <-- 根目录npm配置文件
+- package-lock.json             <-- 根目录依赖锁定文件
|
+- data/                 <-- 数据获取写入目录
|  +- creator.py               <-- 知识图谱数据批量写入Neo4j数据
|  +- spider1.py               <-- 国内企业爬虫脚本
|  +- spider2.py               <-- 国外企业爬虫脚本
|  +- DEEPSEEK_API.py          <-- 调用大模型api对数据进行结构化处理
|  +- result.json              <-- 爬虫原始采集数据文件
|  +- data.json                <-- 处理后的结构化数据，用于导入数据库
|
+- function/             <-- 前端目录
|  +- src/                  <-- 源码目录
|  |  +- assets/                <-- 静态文件目录
|  |  |  +- css/                  <-- 存放css文件
|  |  +- api/                   <-- 前端API请求封装层
|  |  |  +- neo4jApi.js           <-- 封装请求获取Neo4j图谱数据
|  |  +- components/            <-- 存放组件
|  |  |  +- AdminGraph.vue        <-- 管理员界面
|  |  |  +- Login.vue             <-- 登录界面
|  |  |  +- Neo4jGraph.vue        <-- 普通用户界面
|  |  |  +- BatchImport.vue       <-- 批量导入界面
|  |  |  +- Register.vue          <-- 用户注册界面
|  |  +- router/                <-- 路由
|  |  |  +- index.js              <-- 定义路由规则与页面跳转逻辑
|  |  +- view/                <-- 存放前端项目的页面视图
|  |  |  +- Neo4jGraph.vue        <-- 核心页面视图文件
|  |  +- App.vue              <-- 根组件
|  |  +- main.js              <-- 入口文件
|  +- server/              <-- 系统服务后端接口
|  |  +- db.js                <-- MySQL连接配置文件
|  |  +- index.js             <-- 图谱后端接口文
|  +- public/              <-- 默认静态资源目录
|  |  +- image                <-- 存放图片视频资源
```
