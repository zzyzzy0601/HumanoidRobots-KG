import requests
from bs4 import BeautifulSoup
import json
import time

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

# 可扩展配置：支持多个爬取目标，每个目标可指定公司名称
TARGET_CONFIG = [
    {
        "company": "宇树科技", 
        "url": "https://www.unitree.com/cn/h1",
        "name": "H1",
        "filter_classes": ["tips","footer-container","ant-space-item","face-part"]  
    },
    {
        "company": "宇树科技", 
        "url": "https://www.unitree.com/cn/g1",
        "name": "G1",
        "filter_classes": ["tips","footer-container","ant-space-item","face-part"]  
    },
    {
        "company": "宇树科技", 
        "url": "https://www.unitree.com/cn/R1",
        "name": "R1",
        "filter_classes": ["tips","footer-container","ant-space-item","face-part"]  
    },
    {
        "company": "宇树科技", 
        "url": "https://www.unitree.com/cn/H2",
        "name": "H2",
        "filter_classes": ["tips","footer-container","ant-space-item","face-part"]  
    },
    {
        "company": "松延动力", 
        "url": "https://noetixrobotics.com/n2",
        "name": "N2",
        "filter_classes": ["header","footer","modal fade modal-navbox","ptdet-params-text","modal fade modal-video","modal fade modal-cookie","modal fade modal-cookie-setting lenis-stop"]
    },
    {
        "company": "松延动力", 
        "url": "https://noetixrobotics.com/e1",
        "name": "E1",
        "filter_classes": ["header","footer","modal fade modal-navbox","ptdet-params-text","modal fade modal-video","modal fade modal-cookie","modal fade modal-cookie-setting lenis-stop"]
    },
    {
        "company": "魔法原子", 
        "url": "https://www.magiclab.top/z1",
        "name": "Z1",
        "filter_classes": ["header fixed top-0 left-0 w-full bg-black h-md:bg-opacity-90 z-[9999]","specs-container","footer"]
    },
    {
        "company": "魔法原子", 
        "url": "https://www.magiclab.top/human",
        "name": "Gen 1",
        "filter_classes": ["header fixed top-0 left-0 w-full bg-black h-md:bg-opacity-90 z-[9999]","specs-container","footer"]
    },
    {
        "company": "优必选", 
        "url": "https://www.ubtrobot.com/cn/humanoid/products/walker-c",
        "name": "Walker-C",
        "filter_classes": ["nav_top","header","bar_box","inner","footer","bottom","btn_global_bottom","player","com_form2"]
    },
    {
        "company": "优必选", 
        "url": "https://www.ubtrobot.com/cn/humanoid/products/panda-robot",
        "name": "Panda",
        "filter_classes": ["nav_top","header","bar_box","inner","footer","bottom","btn_global_bottom","player","com_form2"]
    },
    {
        "company": "优必选", 
        "url": "https://www.ubtrobot.com/cn/humanoid/products/walker-s",
        "name": "Walker-S",
        "filter_classes": ["nav_top","header","bar_box","inner","footer","bottom","btn_global_bottom","player","com_form2"]
    },
    {
        "company": "优必选", 
        "url": "https://www.ubtrobot.com/cn/humanoid/products/walker-x",
        "name": "Walker-X",
        "filter_classes": ["nav_top","header","bar_box","inner","footer","bottom","btn_global_bottom","player","com_form2"]
    },
    {
        "company": "傅利叶", 
        "url": "https://www.fftai.cn/products-gr1",
        "name": "GR-1",
        "filter_classes": ["c-header","public-box","c-footer","hi-video-pop","hi-iframe-video","c-code-pop"]
    },
    {
        "company": "傅利叶", 
        "url": "https://www.fftai.cn/products-gr2",
        "name": "GR-2",
        "filter_classes": ["c-header","public-box","c-footer","hi-video-pop","hi-iframe-video","c-code-pop","c-go-top"]
    },
    {
        "company": "傅利叶", 
        "url": "https://www.fftai.cn/products-gr3series",
        "name": "GR-3系列",
        "filter_classes": ["c-header","public-box","c-footer","hi-video-pop","hi-iframe-video","c-code-pop"]
    }
]


# ===================== 工具函数 =====================
def get_page_content(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except Exception as e:
        print(f"请求失败：{url}，错误信息：{e}")
        return None

def clean_and_get_all_text(html, filter_classes):
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    # 过滤指定的所有 class
    for cls in filter_classes:
        for tag in soup.find_all(class_=cls):
            tag.decompose()

    # 获取清理后的文本行（作为specifications的内容）
    full_text = soup.get_text(separator="\n")
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    
    return lines

# ===================== 主逻辑 =====================
def main():
    # 最终结果列表，符合指定输出格式
    result = []

    # 循环爬取所有页面
    for item in TARGET_CONFIG:
        company = item["company"]
        name = item["name"]
        url = item["url"]
        filter_classes = item["filter_classes"]

        print(f"正在爬取：{company} - {name}")

        html = get_page_content(url)
        # 获取规格/文本内容（列表形式）
        specifications = clean_and_get_all_text(html, filter_classes)

        # 组装指定格式的字典
        result_item = {
            "company": company,
            "url": url,
            "specifications": specifications
        }
        result.append(result_item)

        time.sleep(1)  # 防反爬延迟

    # 保存 JSON
    with open("experiment1.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    print("\n爬取完成！")

if __name__ == "__main__":
    main()
