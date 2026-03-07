import json
from neo4j import GraphDatabase, exceptions

# ===================== 1. 配置项 =====================
# Neo4j 连接配置（根据你的本地环境修改）
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "username": "neo4j",
    "password": "Youbuding357",  # 替换为你的Neo4j密码
    "database": "neo4j"  # 数据库名，默认neo4j
}

# JSON 爬虫数据文件路径
JSON_FILE_PATH = "formatted_robot_data.json"

# ===================== 2. 标准属性模板定义 =====================
# 节点模板：{标签: {属性名: 默认值}}
NODE_TEMPLATES = {
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
    "Technology": {
        "name": "无",
        "category": "无",
        "description": "无"
    },
    "Application": {
        "name": "无",
        "domain": "无"
    },
    "Component": {
        "name": "无",
        "type": "无",
        "specifications": "无"
    }
}

# 关系模板：{类型: {属性名: 默认值}}
RELATION_TEMPLATES = {
    "DEVELOPED_BY": {"year": "无", "version": "无"},
    "USES_TECH": {},  # 无属性
    "CONTAINS": {"quantity": "无"},
    "APPLIED_IN": {"maturity": "无", "case": "无"}
}


# ===================== 3. 工具函数 =====================
def escape_special_chars(value):
    """转义特殊字符，避免Cypher语法错误"""
    if isinstance(value, str):
        # 转义单引号、换行符、制表符
        return value.replace("'", "\\'").replace("\n", "\\n").replace("\t", "\\t")
    return value


def standardize_node(node_data, node_label):
    """
    标准化节点属性：按模板填充，缺失属性设为"无"
    :param node_data: 原始节点数据（dict）
    :param node_label: 节点标签（如"Robot"）
    :return: 标准化后的节点属性（dict）
    """
    if node_label not in NODE_TEMPLATES:
        return None

    template = NODE_TEMPLATES[node_label]
    standardized_props = {}

    for prop_name, default_val in template.items():
        # 提取原始值，无则用默认值，转义特殊字符
        raw_val = node_data.get(prop_name, default_val)
        standardized_props[prop_name] = escape_special_chars(raw_val)

    return standardized_props


def standardize_relation(relation_data, relation_type):
    """
    标准化关系属性：按模板填充，缺失属性设为"无"
    :param relation_data: 原始关系数据（dict）
    :param relation_type: 关系类型（如"DEVELOPED_BY"）
    :return: 标准化后的关系属性（dict）
    """
    if relation_type not in RELATION_TEMPLATES:
        return None

    template = RELATION_TEMPLATES[relation_type]
    standardized_props = {}

    for prop_name, default_val in template.items():
        raw_val = relation_data.get(prop_name, default_val)
        standardized_props[prop_name] = escape_special_chars(raw_val)

    return standardized_props


def load_json_data(file_path):
    """加载并校验JSON爬虫数据"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 校验数据结构
        if not isinstance(data, dict) or "nodes" not in data or "relations" not in data:
            raise ValueError("JSON数据结构错误，必须包含nodes和relations字段")

        return data

    except FileNotFoundError:
        raise
    except json.JSONDecodeError:
        raise
    except Exception as e:
        raise


# ===================== 4. Neo4j 操作核心类 =====================
class Neo4jGraphCreator:
    def __init__(self, uri, username, password, database):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.database = database

    def close(self):
        """关闭Neo4j连接"""
        if self.driver:
            self.driver.close()

    def clear_existing_graph(self):
        """清空现有图谱（可选，避免重复数据）"""
        try:
            with self.driver.session(database=self.database) as session:
                session.run("MATCH (n) DETACH DELETE n")
        except exceptions.Neo4jError as e:
            raise

    def create_standardized_node(self, node_label, node_props):
        """创建标准化节点（MERGE避免重复）"""
        if not node_props or not node_label:
            return

        # 拼接属性字符串（使用反引号包裹属性名，避免关键字冲突）
        props_str = ", ".join([f"`{k}`: '{v}'" for k, v in node_props.items()])
        cypher = f"""
        MERGE (n:{node_label} {{name: '{node_props['name']}'}})
        SET n += {{{props_str}}}
        """

        try:
            with self.driver.session(database=self.database) as session:
                session.run(cypher)
        except exceptions.Neo4jError as e:
            # 单个节点失败不终止整体流程
            pass

    def create_standardized_relation(self, rel_type, start_node_info, end_node_info, rel_props):
        """
        创建标准化关系
        :param rel_type: 关系类型（如DEVELOPED_BY）
        :param start_node_info: 起始节点信息 {label: "", name: ""}
        :param end_node_info: 终止节点信息 {label: "", name: ""}
        :param rel_props: 标准化后的关系属性
        """
        if not all([rel_type, start_node_info, end_node_info]):
            return

        # 拼接关系属性
        rel_props_str = ", ".join([f"`{k}`: '{v}'" for k, v in rel_props.items()]) if rel_props else ""
        rel_props_clause = f"{{{rel_props_str}}}" if rel_props_str else ""

        cypher = f"""
        MATCH (a:{start_node_info['label']} {{name: '{start_node_info['name']}'}})
        MATCH (b:{end_node_info['label']} {{name: '{end_node_info['name']}'}})
        MERGE (a)-[r:{rel_type}]->(b)
        {"SET r += " + rel_props_clause if rel_props_str else ""}
        """

        try:
            with self.driver.session(database=self.database) as session:
                session.run(cypher)
        except exceptions.Neo4jError as e:
            # 单个关系失败不终止整体流程
            pass


# ===================== 5. 主执行流程 =====================
def main():
    # 1. 初始化Neo4j连接
    graph_creator = Neo4jGraphCreator(
        uri=NEO4J_CONFIG["uri"],
        username=NEO4J_CONFIG["username"],
        password=NEO4J_CONFIG["password"],
        database=NEO4J_CONFIG["database"]
    )

    try:
        # 2. 加载JSON数据
        raw_data = load_json_data(JSON_FILE_PATH)

        # 3. 清空现有图谱（可选，根据需求注释/取消注释）
        graph_creator.clear_existing_graph()

        # 4. 处理并创建所有节点
        for node_item in raw_data["nodes"]:
            node_label = node_item.get("label")
            node_raw_props = node_item.get("properties", {})

            # 标准化节点属性
            standardized_props = standardize_node(node_raw_props, node_label)
            if standardized_props:
                graph_creator.create_standardized_node(node_label, standardized_props)

        # 5. 处理并创建所有关系
        for rel_item in raw_data["relations"]:
            rel_type = rel_item.get("type")
            # 起始/终止节点信息（JSON中需包含label和name）
            start_node_info = {
                "label": rel_item.get("start_node_label"),
                "name": escape_special_chars(rel_item.get("start_node_name", "无"))
            }
            end_node_info = {
                "label": rel_item.get("end_node_label"),
                "name": escape_special_chars(rel_item.get("end_node_name", "无"))
            }
            rel_raw_props = rel_item.get("properties", {})

            # 标准化关系属性
            standardized_rel_props = standardize_relation(rel_raw_props, rel_type)
            if standardized_rel_props is not None:
                graph_creator.create_standardized_relation(
                    rel_type, start_node_info, end_node_info, standardized_rel_props
                )

    except Exception as e:
        raise
    finally:
        # 6. 关闭Neo4j连接
        graph_creator.close()


# ===================== 6. 运行入口 =====================
if __name__ == "__main__":
    main()