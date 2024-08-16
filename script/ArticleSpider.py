# coding:utf-8
import requests
import json
from lxml import etree
import os
import random
import json
import sys
from datetime import datetime, timezone, timedelta
import time

# ISO日期转正常日期
def format_iso_time(iso_datetime_str):
    iso_datetime_str = iso_datetime_str.replace("+0800", "")
    dt_naive = datetime.strptime(iso_datetime_str, "%Y-%m-%dT%H:%M:%S.%f")
    
    return dt_naive
    
# 获取几小时前的日期    
def get_compare_time(hour):
    now = datetime.now()
    hours_ago = now - timedelta(hours=hour)
    
    dt_formatter = hours_ago.strftime("%Y-%m-%d %H:%M:%S")
    
    return dt_formatter

class Article(object):

    def __init__(self):
        
        self.USER_AGENT = [
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
            "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
            "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
            "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
            "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.163 Safari/535.1',
            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
            'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.9.168 Version/11.50',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; ) AppleWebKit/534.12 (KHTML, like Gecko) Maxthon/3.0 Safari/534.12',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36'
        ]
        
        #self.apiUrl = "api.mdnice.com"
        #self.contentUrl = "mdnice.com"
        
        # 获取secrets环境变量, node使用process.env.MYTOKEN
        #self.apiUrl = os.getenv('API_URL', default='api.mdnice.com')
        self.apiUrl = os.getenv('API_URL', default='api.mdnice.com')
        self.contentUrl = os.getenv('CONTENT_URL', default='mdnice.com')
        
        self.detailsUrl = "https://"+self.contentUrl+"/writing/"
        self.listUrl = "https://"+self.apiUrl+"/writings"
        
        self.header = {
            'Host': self.apiUrl,
            'Referer': "https://"+self.contentUrl,
            'User-Agent': random.choice(self.USER_AGENT),
        }

    def get_list(self, url, params):
        # get传params，post传data
        re = requests.get(url, headers=self.header,params=params)
        return re.content
        
    # 开始采集
    def run(self, currentPage, pageSize, falgDate):        
        
        params = {
            'currentPage': currentPage,
            'pageSize': pageSize
        }
        
        res = article.get_list(self.listUrl, params)
        json_data = json.loads(res)
        
        code = json_data['code']
        data = json_data['data']
        data_count = len(data)
        
        if code != 0:
            return 0
            
        if data_count == 0:
            return -1
            
        # 当前页的最久更新，大于某值则退出不更新
        current_oldest = format_iso_time(data[data_count-1]['updateTime'])
        # 8.13 - 8.14
        if str(falgDate) > str(current_oldest):
            return -2
        
        for item in data:
            
            outId = item['outId']
            info_url = self.detailsUrl+outId
            re = requests.get(info_url)
            
            html = etree.HTML(re.content)
            
            # 获取第一个div下的所有元素
            #article_node = html.xpath('//div[@id="writing-content"]/node()')
            script_element = html.xpath('//script[@id="__NEXT_DATA__"]')[0]  
            
            # 提取<script>标签的文本内容（即JSON字符串）
            json_str = script_element.text if script_element.text else script_element.text_content()
            
            try:  
                json_data = json.loads(json_str)
                
                # 文章详情文件路径
                details_path = 'api/article/details/'+outId+'.json'
                  
                details_directory = os.path.dirname(details_path)  
                if not os.path.exists(details_directory):  
                    os.makedirs(details_directory)  
                  
                with open(details_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                    
                print("article: "+outId+" save success")
                
            except json.JSONDecodeError:  
                print("Failed to decode JSON data")
                return -3
            
        # 文章列表文件路径  
        file_path = 'api/article/list/' + str(currentPage)+'.json'
          
        directory = os.path.dirname(file_path)  
        if not os.path.exists(directory):  
            os.makedirs(directory)  
          
        with open(file_path, 'w', encoding='utf-8') as f:  
            json.dump(data, f, ensure_ascii=False, indent=4)  
       
        print('currentPage: '+ str(currentPage) + ',current_oldest: ' + str(current_oldest))
        
        return 1
        

if __name__ == '__main__':

    currentPage = 1
    pageSize = 30
    flag_date = get_compare_time(24)
    
    error_msg = {
        "0" : "remote request error~",
        "-1": "no data~",
        "-2": "over time~",
        "-3": "parse fail~"
    }
    
    #####测试#####
    #article = Article()
    #return_code = article.run(currentPage, pageSize, flag_date)
    #exit()
    #####测试#####
    
    while(True):
        
        article = Article()
        return_code = article.run(currentPage, pageSize, flag_date)
    
        if return_code<0:
            print("error_code: " + str(return_code) + ", error_msg: " + error_msg[str(return_code)])
            break
            sys.exit(1)  # 使用 sys.exit() 退出程序并返回非零退出码
        
        currentPage += 1
        time.sleep(2)
        
        
    
    