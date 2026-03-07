import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin

# 替换fake-useragent：使用合法的User-Agent列表（模拟不同浏览器）
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

# 最终存储的结构化数据（适配知识图谱入库）
robot_data = {
    "products": [],  # 核心产品数据
    "brands": [],  # 品牌关联数据
    "metadata": {  # 爬取元信息
        "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "total_urls": 3
    }
}


def get_random_headers():
    """生成模拟真实浏览器的请求头（无第三方依赖）"""
    # 随机选择User-Agent
    random_ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": random_ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.7,zh-CN;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1"
    }


def crawl_boston_atlas(url="https://bostondynamics.com/products/atlas/"):
    """爬取波士顿动力Atlas产品页"""
    brand_name = "Boston Dynamics"
    product_name = "Atlas"
    print(f"=== 开始爬取 {brand_name} - {product_name} ===")

    try:
        # 随机延迟2-4秒，规避反爬
        time.sleep(random.uniform(2, 4))
        # 发送请求（禁用重定向跟踪，避免跳转干扰）
        response = requests.get(
            url,
            headers=get_random_headers(),
            timeout=15,
            allow_redirects=True
        )
        response.raise_for_status()  # 捕获HTTP错误（4xx/5xx）
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. 提取品牌基础信息
        brand_info = {
            "brand_name": brand_name,
            "country": "USA",
            "parent_company": "Hyundai Motor Group",
            "official_website": "https://bostondynamics.com/",
            "description": "Global leader in advanced mobile robotics"
        }
        # 去重添加品牌
        if not any(b["brand_name"] == brand_name for b in robot_data["brands"]):
            robot_data["brands"].append(brand_info)

        # 2. 提取产品核心信息（适配Boston Dynamics页面结构）
        # 提取页面标题和描述
        page_title = soup.title.string.strip() if soup.title else f"{product_name} | {brand_name}"
        meta_desc = soup.find("meta", attrs={"name": "description"})
        product_desc = meta_desc["content"].strip() if meta_desc else "Advanced humanoid robot by Boston Dynamics"

        # 提取关键特性（从页面文本/列表中解析）
        key_features = []
        # 定位产品特性区块（适配页面class命名）
        feature_sections = soup.find_all("div", class_=["feature", "product-feature", "content-block"])
        for section in feature_sections:
            feature_text = section.get_text(strip=True)
            if feature_text and len(feature_text) > 10 and feature_text not in key_features:
                key_features.append(feature_text[:200])  # 限制长度，避免冗余

        # 提取产品图片（主视觉图）
        product_images = []
        img_tags = soup.find_all("img", class_=["hero-image", "product-image", "lazyload"])
        for img in img_tags:
            img_src = img.get("src") or img.get("data-src")
            if img_src and "atlas" in img_src.lower():
                # 拼接完整URL
                full_img_url = urljoin(url, img_src)
                product_images.append(full_img_url)

        # 3. 组装产品数据
        product_data = {
            "product_id": f"{brand_name.lower()}_{product_name.lower()}",
            "product_name": product_name,
            "brand_name": brand_name,
            "product_url": url,
            "page_title": page_title,
            "description": product_desc,
            "key_features": key_features[:8],  # 取前8个核心特性
            "product_images": product_images[:5],  # 取前5张核心图片
            "product_type": "Humanoid Robot",
            "application_scenarios": [
                "Industrial Inspection",
                "Disaster Response",
                "R&D",
                "Dynamic Mobility Testing"
            ],
            "specs": {
                "actuation_type": "Electric",
                "mobility": "Dynamic bipedal locomotion",
                "terrain_adaptability": "Multi-terrain (rough ground, stairs, obstacles)"
            }
        }

        robot_data["products"].append(product_data)
        print(f"✅ {brand_name} - {product_name} 爬取成功")

    except Exception as e:
        print(f"❌ 爬取 {brand_name} - {product_name} 失败: {str(e)}")


def crawl_figure_ai(url="https://www.figure.ai/figure"):
    """爬取Figure AI产品页"""
    brand_name = "Figure AI"
    product_name = "Figure 01/02"
    print(f"=== 开始爬取 {brand_name} - {product_name} ===")

    try:
        time.sleep(random.uniform(2, 4))
        response = requests.get(
            url,
            headers=get_random_headers(),
            timeout=15
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. 提取品牌信息
        brand_info = {
            "brand_name": brand_name,
            "country": "USA",
            "parent_company": "Figure AI Inc.",
            "official_website": "https://www.figure.ai/",
            "description": "General-purpose humanoid robotics for manufacturing and logistics"
        }
        if not any(b["brand_name"] == brand_name for b in robot_data["brands"]):
            robot_data["brands"].append(brand_info)

        # 2. 提取产品信息（适配Figure AI页面结构）
        page_title = soup.title.string.strip() if soup.title else f"{product_name} | {brand_name}"
        meta_desc = soup.find("meta", attrs={"name": "description"})
        product_desc = meta_desc[
            "content"].strip() if meta_desc else "General-purpose humanoid robot for industrial use"

        # 提取关键特性
        key_features = []
        feature_items = soup.find_all("li", class_=["feature-item", "benefit-item"])
        for item in feature_items:
            feature_text = item.get_text(strip=True)
            if feature_text and len(feature_text) > 5:
                key_features.append(feature_text)

        # 提取产品图片
        product_images = []
        img_tags = soup.find_all("img", src=True)
        for img in img_tags:
            if "figure" in img["src"].lower() and "robot" in img["src"].lower():
                full_img_url = urljoin(url, img["src"])
                product_images.append(full_img_url)

        # 组装产品数据
        product_data = {
            "product_id": f"{brand_name.lower()}_{product_name.lower()}",
            "product_name": product_name,
            "brand_name": brand_name,
            "product_url": url,
            "page_title": page_title,
            "description": product_desc,
            "key_features": key_features[:8],
            "product_images": product_images[:5],
            "product_type": "General-Purpose Humanoid Robot",
            "application_scenarios": [
                "Automotive Manufacturing",
                "Warehousing & Logistics",
                "Retail",
                "Industrial Automation"
            ],
            "specs": {
                "collaboration_partners": "BMW, Amazon",
                "focus": "Human-level dexterity and task adaptability"
            }
        }

        robot_data["products"].append(product_data)
        print(f"✅ {brand_name} - {product_name} 爬取成功")

    except Exception as e:
        print(f"❌ 爬取 {brand_name} - {product_name} 失败: {str(e)}")


def crawl_pudu_d9(url="https://www.pudurobotics.com/en/products/d9"):
    """爬取普渡机器人D9产品页（Pudu Robotics）"""
    brand_name = "Pudu Robotics"
    product_name = "D9"
    print(f"=== 开始爬取 {brand_name} - {product_name} ===")

    try:
        time.sleep(random.uniform(2, 4))
        response = requests.get(
            url,
            headers=get_random_headers(),
            timeout=15
        )
        response.raise_for_status()
        # 处理中文编码（Pudu是中国品牌，页面含中英文）
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. 提取品牌信息
        brand_info = {
            "brand_name": brand_name,
            "country": "China",
            "parent_company": "Pudu Robotics Inc.",
            "official_website": "https://www.pudurobotics.com/",
            "description": "Leading provider of commercial service robots"
        }
        if not any(b["brand_name"] == brand_name for b in robot_data["brands"]):
            robot_data["brands"].append(brand_info)

        # 2. 提取产品信息（适配Pudu Robotics英文页结构）
        page_title = soup.title.string.strip() if soup.title else f"{product_name} | {brand_name}"
        meta_desc = soup.find("meta", attrs={"name": "description"})
        product_desc = meta_desc["content"].strip() if meta_desc else "D9 delivery robot by Pudu Robotics"

        # 提取关键特性
        key_features = []
        # 定位特性区块（适配Pudu页面class）
        feature_divs = soup.find_all("div", class_=["product-detail", "feature-box", "desc-box"])
        for div in feature_divs:
            feature_text = div.get_text(strip=True)
            if feature_text and len(feature_text) > 10 and feature_text not in key_features:
                key_features.append(feature_text[:200])

        # 提取产品图片
        product_images = []
        img_tags = soup.find_all("img", class_=["product-img", "detail-img"])
        for img in img_tags:
            img_src = img.get("src") or img.get("data-src")
            if img_src and "d9" in img_src.lower():
                full_img_url = urljoin(url, img_src)
                product_images.append(full_img_url)

        # 组装产品数据
        product_data = {
            "product_id": f"{brand_name.lower()}_{product_name.lower()}",
            "product_name": product_name,
            "brand_name": brand_name,
            "product_url": url,
            "page_title": page_title,
            "description": product_desc,
            "key_features": key_features[:8],
            "product_images": product_images[:5],
            "product_type": "Delivery Humanoid Robot (Service Robot)",
            "application_scenarios": [
                "Restaurant Delivery",
                "Hotel Service",
                "Hospital Logistics",
                "Commercial Catering"
            ],
            "specs": {
                "navigation": "SLAM-based autonomous navigation",
                "load_capacity": "Up to 9kg",
                "battery_life": "12+ hours"
            }
        }

        robot_data["products"].append(product_data)
        print(f"✅ {brand_name} - {product_name} 爬取成功")

    except Exception as e:
        print(f"❌ 爬取 {brand_name} - {product_name} 失败: {str(e)}")


def save_crawled_data(output_file="robot_crawled_data.json"):
    """保存爬取数据到JSON文件（UTF-8编码，便于入库）"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(robot_data, f, ensure_ascii=False, indent=4)
    print(f"\n=== 数据保存完成 ===")
    print(f"📁 输出文件: {output_file}")
    print(f"📊 爬取统计:")
    print(f"   - 品牌数量: {len(robot_data['brands'])}")
    print(f"   - 产品数量: {len(robot_data['products'])}")
    print(f"   - 爬取时间: {robot_data['metadata']['crawl_time']}")


if __name__ == "__main__":
    # 执行爬取任务（按顺序爬取3个URL）
    crawl_boston_atlas()
    crawl_figure_ai()
    crawl_pudu_d9()

    # 保存数据到JSON文件
    save_crawled_data()

    # 打印数据预览
    print("\n=== 数据预览（前100字符）===")
    for product in robot_data["products"]:
        print(f"\n{product['product_name']} ({product['brand_name']}):")
        print(f"  URL: {product['product_url']}")
        print(f"  Desc: {product['description'][:100]}...")