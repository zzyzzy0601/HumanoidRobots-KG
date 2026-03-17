import json
import os
from typing import Dict, List, Any
from openai import OpenAI

# ===================== 配置项 =====================
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', "sk-19d3a7b8976a4851bb36649fd07f084c")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
INPUT_JSON_PATH = "robot_specs_final.json"
OUTPUT_JSON_PATH = "data222.json"
# ===================== 工具函数 =====================
def load_original_json(file_path: str) -> Dict[str, Any]:
    """加载原始JSON数据文件（支持任意结构的原始爬虫数据）"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"成功加载原始数据：{file_path}")
        return data
    except FileNotFoundError:
        raise Exception(f"原始文件不存在：{file_path}")
    except json.JSONDecodeError:
        raise Exception(f"原始文件不是有效JSON格式：{file_path}")


def call_deepseek_api(original_data: Dict[str, Any]) -> str:
    """使用OpenAI SDK调用DeepSeek API，转换数据格式"""
    # 初始化OpenAI客户端（适配DeepSeek）
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )

    # 构建精准的系统提示词（核心：强制格式要求）
    system_prompt = """你是一个专业的知识图谱数据格式化助手，需要严格按照以下规则处理输入的机器人领域原始数据：
### 输出格式要求（必须严格遵守，缺失属性填充"无"）：
{
  "nodes": [
    {
      "label": "Robot/Company/BodyPart/Application/Component/HardwareTech/SoftwareTech/ElectricalFeature",
      "properties": {
        // Robot属性：name、height、weight、release_year、battery_life、payload、description、product_type
        提取所有爬虫数据中的机器人型号为节点name、height（身高/尺寸，保留单位）、weight（体重/整机重量，保留单位）、
        battery_life（续航时间，保留单位）、payload（负载/承重力，含手臂/全身负载，保留单位）、
        description（产品核心特性，将所有性能、尺寸、重量、扭矩、速度、硬件配置等信息整合为**通顺、逻辑清晰的单句（或连贯长句）**，按「外观尺寸→重量→运动性能→核心硬件→续航→感知能力」的逻辑排序，语言简洁无重复，不删减关键参数；）、
        product_type（产品类型）；release_year（上市/发布年份，无则填"无"）
        // Company属性：name、country（所属国家，可根据网络信息查找填充）、found_year（成立年份，无明确数据则填"无"）、description（整合为通顺、逻辑清晰的连贯的一段话））
        // BodyPart属性（人型机器人身体都有哪些部位）：name（名称）、DOF（该部位的自由度）
        // HardwareTech(硬件技术):name（名称）、parameter（参数）、description（技术核心特性/功能，提取所有相关描述，整合为通顺、逻辑清晰的一段话）
        // SoftwareTech(软件技术):name（名称）、description（技术核心特性/功能，提取所有相关描述，整合为通顺、逻辑清晰的一段话）
        // ElectricalFeature(机器人电气特性):name（电气项名称）、specification（电气规格参数）
        // Application属性：name、domain（场景领域）
        // Component属性：name、type（部件类型）、specifications（部件规格参数，提取该零件相关参数，保留单位，用分号分隔）
        
        // 所有缺失的属性值必须填充为"无"
      }
    }
  ],
  "relations": [
    {
      "type": "DEVELOPE/IMPLEMENTS/USES_TECH/FEATURE/CONTAINS/APPLIED_IN/HAS_PART",
      "start_node_label": "起始节点类型（如Robot）",
      "start_node_name": "起始节点名称",
      "end_node_label": "终止节点类型（如Company）",
      "end_node_name": "终止节点名称",
      "properties": {
        // DEVELOP（企业研发机器人）属性：关联方向：Company → Robot；year（研发/发布年份，无则填"无"）、version（产品版本，缺失填"无"）
        // APPLIED_IN（机器人应用于某具体场景）属性：关联方向：Robot → Application；maturity（落地成熟度，无则填"无"）、case（应用案例，缺失填"无"）
        // HAS_PART(机器人有那些身体部分)属性：关联方向：Robot → BodyPart；空字典{}
        // CONTAINS(机器人某部位包含哪些部件)属性：关联方向：BodyPart → Component；description（技术核心特性/功能，提取所有相关描述，整合为通顺、逻辑清晰的一段话）
        // IMPLEMENTS(该部件基于某项硬件技术)属性：关联方向：Component → HardwareTech；空字典{} 
        // USES_TECH（该部件基于软件技术）属性：关联方向：Component → SoftwareTech；空字典{}
        // FEATURE（机器人具有哪些电气属性）属性：关联方向：Robot → ElectricalFeature；空字典{}
      }
    }
  ]
}

### 输出约束：
1. 仅返回JSON字符串，不要包含任何解释、说明、markdown代码块
2. 节点label只能是Robot/Company/BodyPart/Application/Component/HardwareTech/SoftwareTech/ElectricalFeature中的一种
3. 关系type只能是DEVELOPE/IMPLEMENTS/USES_TECH/FEATURE/CONTAINS/APPLIED_IN/HAS_PART中的一种
4. 所有属性值必须是字符串类型，缺失值统一填"无"
5. 确保relations中的start_node_name/end_node_name能在nodes中找到对应节点
6. 若原始数据中某节点的部分属性无信息，**必须显式填充为"无"**，不可省略属性键；

### 处理逻辑
1. 解析输入的原始机器人领域数据，提取所有符合上述节点标签的实体,一些属性可以联网搜索
2. 为每个实体匹配对应的属性，严格按照属性列表填充，不新增/遗漏属性
3. 提取实体间的关系，严格匹配关系类型、起始/终止节点类型，填充对应属性
4. 生成符合上述格式要求的JSON数据，确保语法完全正确

"""

    # 构建用户提示词（传入原始数据）
    user_prompt = f"""请处理以下机器人领域原始数据，严格按照上述格式输出JSON：
{json.dumps(original_data, ensure_ascii=False, indent=2)}"""

    try:
        # 调用DeepSeek API（官方推荐方式）
        print("正在调用DeepSeek API处理数据...")
        response = client.chat.completions.create(
            model="deepseek-chat",  # 官方指定模型名
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,  # 0温度保证输出完全可控
            max_tokens=8192,  # 足够容纳大体积数据
            stream=False  # 非流式输出
        )

        # 提取纯JSON结果
        result_content = response.choices[0].message.content.strip()
        print("DeepSeek API调用完成")
        return result_content

    except Exception as e:
        raise Exception(f"调用DeepSeek API失败：{str(e)}")


def clean_and_validate_json(raw_json_str: str) -> Dict[str, Any]:
    """清理并验证大模型返回的JSON（容错+格式校验）"""
    try:
        # 清理可能的多余字符（如大模型误加的```json标记）
        clean_str = raw_json_str
        if clean_str.startswith("```"):
            clean_str = clean_str.split("```")[1].replace("json", "").strip()

        # 解析JSON
        formatted_data = json.loads(clean_str)

        # 基础格式校验
        if not isinstance(formatted_data, dict):
            raise Exception("返回结果不是JSON对象")
        if "nodes" not in formatted_data or "relations" not in formatted_data:
            raise Exception("缺失nodes或relations顶级字段")
        if not isinstance(formatted_data["nodes"], list) or not isinstance(formatted_data["relations"], list):
            raise Exception("nodes和relations必须是数组类型")

        # 自动填充缺失属性（双重保障）
        formatted_data = auto_fill_missing_properties(formatted_data)

        print("JSON格式验证通过，缺失属性已自动填充")
        return formatted_data

    except json.JSONDecodeError:
        raise Exception(f"大模型返回的不是有效JSON：{raw_json_str[:200]}...")
    except Exception as e:
        raise Exception(f"JSON验证失败：{str(e)}")


def auto_fill_missing_properties(data: Dict[str, Any]) -> Dict[str, Any]:
    """自动填充节点/关系中缺失的属性（兜底逻辑）"""
    # 节点属性模板
    node_prop_templates = {
        "Robot": ["name", "height", "weight", "release_year", "battery_life", "payload", "description", "product_type"],
        "Company": ["name", "country", "found_year", "description"],
        "BodyPart": ["name", "DOF"],
        "Application": ["name", "domain"],
        "Component": ["name", "specifications"],
        "HardwareTech": ["name", "parameter", "description"],
        "SoftwareTech": ["name", "description"],
        "ElectricalFeature": ["name", "specification"]
    }

    # 关系属性模板
    rel_prop_templates = {
        "DEVELOPE": ["year", "version"],
        "APPLIED_IN": ["maturity", "case"],
        "HAS_PART": [],
        "CONTAINS": ["description"],
        "IMPLEMENTS": [],
        "USES_TECH": [],
        "FEATURE": []
    }

    # 填充节点缺失属性
    for node in data["nodes"]:
        label = node.get("label")
        if label in node_prop_templates:
            for prop in node_prop_templates[label]:
                if prop not in node["properties"]:
                    node["properties"][prop] = "无"

    # 填充关系缺失属性
    for rel in data["relations"]:
        rel_type = rel.get("type")
        if rel_type in rel_prop_templates:
            for prop in rel_prop_templates[rel_type]:
                if prop not in rel["properties"]:
                    rel["properties"][prop] = "无"

    return data


def save_formatted_json(data: Dict[str, Any], output_path: str):
    """保存标准化后的JSON文件"""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"标准化JSON已保存：{output_path}")
    except Exception as e:
        raise Exception(f"保存文件失败：{str(e)}")


# ===================== 主执行流程 =====================
def main():
    try:
        # 1. 加载原始数据
        original_data = load_original_json(INPUT_JSON_PATH)

        # 2. 调用DeepSeek API转换格式
        raw_json = call_deepseek_api(original_data)

        # 3. 清理验证并填充缺失属性
        validated_data = clean_and_validate_json(raw_json)

        # 4. 保存结果
        save_formatted_json(validated_data, OUTPUT_JSON_PATH)

        print("\n数据格式化完成！")

    except Exception as e:
        print(f"\n处理失败：{str(e)}")


if __name__ == "__main__":
    # 安装依赖提示（首次运行前执行）
    # pip install openai
    main()