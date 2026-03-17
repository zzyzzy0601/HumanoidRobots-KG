import requests
from parsel import Selector
import json
import re
import time


class MultiRobotSpider:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
        self.results = []

    def fetch(self, url):
        try:
            res = requests.get(url, headers=self.headers, timeout=15)
            res.encoding = 'utf-8'
            if res.status_code == 200:
                return Selector(text=res.text)
        except Exception as e:
            print(f"请求 {url} 出错: {e}")
        return None

    def clean_text(self, text_list):
        """清洗提取到的文本列表"""
        noise_keywords = ['版权', '联系我们', '电话', '菜单', '微信', 'Copyright', '©', 'App下载','公司概况','关于我们','加入我们','下载中心','行业案例','机器人创新营','技术开源','服务支持','企业责任','媒体中心','技术积累','法律事务','媒体问询','商务合作','公司简介','新闻中心','关于优必选','企业文化','发展历程','合规诚信','投资者关系','核心技术','技术能力','优必选研究院','人形机器人','产品系列','解决方案','期待与您携手','立即咨询','行业应用','资讯动态','开源中心','关于我们','政策条款','加入我们','文档中心','服务与支持','关于宇树','APP下载'
]
        cleaned = []
        for t in text_list:
            t = t.strip()
            # 过滤噪音、空字符串、过短或过长的非参数文本
            if t and not any(k in t for k in noise_keywords) and 2 < len(t) < 200:
                cleaned.append(t)
        return list(dict.fromkeys(cleaned))  # 去重

    def parse_unitree(self, url):
        """专项解析宇树：抓取其特有的参数布局"""
        sel = self.fetch(url)
        if sel:
            # 宇树的参数通常在 valPart 类或 li 标签中
            content = sel.xpath(
                '//div[contains(@class, "valPart")]//text() | '
                '//li//p//text() | '
                '//div[contains(@class, "product-spec")]//text()'
            ).getall()

            data = self.clean_text(content)
            self.results.append({
                'company': '宇树科技',
                'url': url,
                'specifications': data
            })
            print(f"已抓取宇树科技: {url}, 获取项: {len(data)}")

    def parse_others(self, company, url, extra_xpath=""):
        """通用解析：松延、魔法原子、银河通用"""
        sel = self.fetch(url)
        if sel:
            # 抓取表格内容、列表内容以及 div 块内容
            xpath_query = f'//tr//text() | //li//text() | //div[contains(@class, "info")]//text() {extra_xpath}'
            content = sel.xpath(xpath_query).getall()

            data = self.clean_text(content)
            self.results.append({
                'company': company,
                'url': url,
                'specifications': data
            })
            print(f"已抓取{company}: {url}, 获取项: {len(data)}")

    def run(self):
        # 1. 宇树科技
        for url in ["https://www.unitree.com/cn/h1",
                    "https://www.unitree.com/cn/g1",
                    "https://www.unitree.com/cn/R1",
                    "https://www.unitree.com/cn/H2"]:
            self.parse_unitree(url)
            time.sleep(1)

        # 2. 松延动力
        for url in ["https://noetixrobotics.com/n2",
                    "https://noetixrobotics.com/e1"]:
            self.parse_others("松延动力", url,  "| //div[contains(@class, 'text-box')]//text()")
            time.sleep(1)

        # 3. 魔法原子
        for url in ["https://www.magiclab.top/z1",
                    "https://www.magiclab.top/human"]:
            self.parse_others("魔法原子", url, "| //div[contains(@class, 'text-box')]//text()")
            time.sleep(1)


        # 4. 优必选（ubtrobot）
        for url in [
            "https://www.ubtrobot.com/cn/humanoid/products/walker-c",
            "https://www.ubtrobot.com/cn/humanoid/products/walker-x",
            "https://www.ubtrobot.com/cn/humanoid/products/panda-robot",
            "https://www.ubtrobot.com/cn/humanoid/products/walker-s"
        ]:
            self.parse_others("优必选", url)  # 可根据需要添加XPath规则
            time.sleep(1)

        # 5. 傅里叶（fftai）
        for url in [
            "https://www.fftai.cn/products-gr1",
            "https://www.fftai.cn/products-gr2",
            "https://www.fftai.cn/products-gr3series"
        ]:
            self.parse_others("傅里叶", url)  # 可根据需要添加XPath规则
            time.sleep(1)

        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)
        print("\n✅ 数据优化采集完成！")


if __name__ == "__main__":
    spider = MultiRobotSpider()
    spider.run()