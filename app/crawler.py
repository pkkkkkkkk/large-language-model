"""
纯爬虫工具模块 - 移除Flask依赖
"""
import re
import json
import time
import socket
import urllib.request
import urllib.parse
import urllib.error
import ssl
import logging

logger = logging.getLogger(__name__)

# 设置超时和SSL
timeout = 5
socket.setdefaulttimeout(timeout)
ssl._create_default_https_context = ssl._create_unverified_context

class PureCrawler:
    """纯爬虫类 - 无Flask依赖"""
    
    def __init__(self, time_sleep=0.1):
        self.__time_sleep = time_sleep
        self.__amount = 0
        self.__start_amount = 0
        self.__counter = 0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0',
            'Cookie': ''
        }
        self.__per_page = 30
    
    @property
    def time_sleep(self):
        return self.__time_sleep
    
    @time_sleep.setter
    def time_sleep(self, value):
        self.__time_sleep = value
    
    @staticmethod
    def get_suffix(name):
        """获取文件后缀名"""
        m = re.search(r'\.[^\.]*$', name)
        if m and m.group(0) and len(m.group(0)) <= 5:
            return m.group(0)
        else:
            return '.jpeg'
    
    @staticmethod
    def handle_baidu_cookie(original_cookie, cookies):
        """处理百度Cookie"""
        if not cookies:
            return original_cookie
        result = original_cookie
        for cookie in cookies:
            result += cookie.split(';')[0] + ';'
        result = result.rstrip(';')
        return result
    
    def get_images(self, word):
        """获取图片URL列表"""
        try:
            search = urllib.parse.quote(word)
            pn = self.__start_amount
            image_urls = []
            
            while pn < self.__amount:
                url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592&is=&fp=result&queryWord=%s&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=&hd=&latest=&copyright=&word=%s&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&force=&pn=%s&rn=%d&gsm=1e&1594447993172=' % (
                    search, search, str(pn), self.__per_page)
                
                try:
                    time.sleep(self.time_sleep)
                    req = urllib.request.Request(url=url, headers=self.headers)
                    page = urllib.request.urlopen(req)
                    
                    # 处理Cookie
                    cookies = page.info().get_all('Set-Cookie')
                    if cookies:
                        self.headers['Cookie'] = self.handle_baidu_cookie(
                            self.headers['Cookie'], cookies)
                    
                    rsp = page.read()
                    page.close()
                    
                except UnicodeDecodeError as e:
                    logger.error(f"UnicodeDecodeError: {e}, URL: {url}")
                    continue
                except urllib.error.URLError as e:
                    logger.error(f"URLError: {e}, URL: {url}")
                    continue
                except socket.timeout as e:
                    logger.error(f"Socket timeout: {e}, URL: {url}")
                    continue
                except Exception as e:
                    logger.error(f"其他错误: {e}, URL: {url}")
                    continue
                
                try:
                    rsp_data = json.loads(rsp, strict=False, object_hook=lambda d: {
                        k: urllib.parse.unquote(v) if isinstance(v, str) else v 
                        for k, v in d.items()
                    })
                    
                    if 'data' not in rsp_data:
                        logger.warning(f"响应中无data字段，跳过")
                        continue
                    
                    for image_info in rsp_data['data']:
                        if 'thumbURL' in image_info:
                            thumb_url = image_info['thumbURL']
                            image_urls.append(thumb_url)
                    
                    pn += self.__per_page
                    
                    # 只获取第一页就返回
                    return image_urls
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析错误: {e}")
                    continue
                    
            return image_urls
            
        except Exception as e:
            logger.error(f"获取图片时发生未知错误: {e}")
            return []
    
    def start(self, word):
        """开始爬取图片"""
        self.__per_page = 30
        self.__start_amount = 0
        self.__amount = self.__per_page
        return self.get_images(word)

# 创建全局爬虫实例
crawler_instance = PureCrawler(0.1)