import json
import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By

def get_driver():
    edge_options = EdgeOptions()
    edge_options.add_argument("--headless")  # 无窗口模式
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--window-size=1920,1080")
    # 模拟真实 Edge 浏览器，避免被识别为爬虫
    edge_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0")
    
    try:
        # 移除 webdriver_manager 依赖，使用 Selenium 4 自带的驱动定位功能
        driver = webdriver.Edge(options=edge_options)
        return driver
    except Exception as e:
        print(f"启动 Edge 失败，请确保已安装 Edge 浏览器。错误信息: {e}")
        raise

def scrape_robots():
    targets = [
        {
            "company": "Boston Dynamics",
            "url": "https://bostondynamics.com/products/atlas/",
            "keywords": ["height", "weight", "payload", "speed", "battery"]
        },
        {
            "company": "Pudu Robotics",
            "url": "https://www.pudurobotics.com/en/products/d9",
            "keywords": ["size", "weight", "battery", "clearance", "payload"]
        }
    ]

    driver = get_driver()
    results = []

    for target in targets:
        print(f"正在深度解析 {target['company']}...")
        try:
            driver.get(target['url'])
            if "figure.ai" in target['url']:
                # 模拟滚动到底部再回到顶部，触发所有动画
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(10) # 给数字滚动预留充足时间
            else:
                time.sleep(8)
            specs = set()
            
            # 策略：寻找包含关键词的元素，并提取其父级或附近的所有文本
            for kw in target['keywords']:
                # 寻找包含该关键词的元素（不区分大小写）
                xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{kw}')]"
                elements = driver.find_elements(By.XPATH, xpath)
                
                for el in elements:
                    try:
                        # 核心改动：获取该元素及其父容器的完整文本，通常数值就在旁边
                        parent_text = el.find_element(By.XPATH, "..").text.strip()
                        if parent_text and len(parent_text) < 200:
                            # 将多行文本压缩成一行，方便阅读
                            formatted = parent_text.replace('\n', ': ')
                            specs.add(formatted)
                    except:
                        continue

            results.append({
                "company": target['company'],
                "url": target['url'],
                "specifications": sorted(list(specs))
            })
            print(f"✅ {target['company']} 提取完成")

        except Exception as e:
            print(f"❌ 错误: {e}")

    driver.quit()

    with open('robot_specs_final.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    print("\n✨ 最终数据已保存至: robot_specs_final.json")

if __name__ == "__main__":
    scrape_robots()