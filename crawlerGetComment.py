## https://zhuanlan.zhihu.com/p/105101268

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time, re, collections
from pymongo import MongoClient
from lxml import etree
import pandas as pd
import env_private as env





""" 变量 """
dbName = "jd"
#collectionName_content = "tv"
#collectionName_sku = "tv_sku"
#excel_sheet_name = 'tv'

collectionName_content = "skincare_bodyCream"
collectionName_sku = "skincare_bodyCream_sku"
excel_sheet_name = 'skincare_bodyCream'


""" 链接 mongo """
myclient = MongoClient(r'mongodb://{}:{}@{}/'.format(env.con_username, env.con_password, env.hostName))


mydb = myclient[dbName]
mycol_content = mydb[collectionName_content]    
mycol_sku = mydb[collectionName_sku]    


""" 获取excel 产品详情页 列表 """
df_url_detail = pd.read_excel(r'url_detail.xlsx', sheet_name=excel_sheet_name)
df_url_detail.set_index(["url_detail"], inplace=True)
#df_url_detail = df_url_detail.iloc[1:,]
#df_url_detail.columns
d_url_detail = {}
for _s in df_url_detail.index:
    d_url_detail[_s] = {
            'category': df_url_detail['category'][_s],
            'brand': df_url_detail['brand'][_s],
            'level': df_url_detail['level'][_s],
            'sku_id': re.findall(r'\d+',_s)[0],
            'url_comment': r'{}#comment'.format(_s),
            'url_detail': _s,
            }
d_url_detail = dict(collections.OrderedDict(sorted(d_url_detail.items(), key=lambda t: t[0])))



""" firefox driver """
def driver_browser():
    driver_path = env.driver_path_firefox
    options = webdriver.FirefoxOptions()
    options.add_argument('-headless')
    browser = webdriver.Firefox(executable_path=driver_path, firefox_options=options)
    browser.maximize_window()  
    wait = WebDriverWait(browser, 10)
    return browser, wait
 
browser, wait = driver_browser()

n_comment = 0
n_product = 0
d_info_all = []
for url in d_url_detail.keys():
#    print(url)
#    url = list(d_url_detail.keys())[0]
#    browser, wait = driver_browser()
    browser.get(d_url_detail.get(url).get('url_comment'))
    time.sleep(5) 
    
    html = browser.page_source    
    htmlElement = etree.HTML(html)
    l_tmp = [s.strip() for s in htmlElement.xpath('//div[@class="sku-name"]/text()')]
    l_tmp1 = [len(s) for s in l_tmp]
    print(l_tmp[l_tmp1.index(max(l_tmp1))])
    d_url_detail[url]['sku_name'] = l_tmp[l_tmp1.index(max(l_tmp1))]
    mycol_sku.update_one(d_url_detail[url],{'$set':d_url_detail[url]},upsert=True)
    time.sleep(1)       
    exsist_next_page = '下一页' in htmlElement.xpath('//div[@id="comment-0"]//div[@class="ui-page"]/a/text()')
    n_product += 1
    #### 获取 content
    n_page = 0
    while exsist_next_page:       
        
        html = browser.page_source  
        htmlElement = etree.HTML(html)
        exsist_next_page = '下一页' in htmlElement.xpath('//div[@id="comment-0"]//div[@class="ui-page"]/a/text()')
        if exsist_next_page:
            n_page +=1
            blocks = htmlElement.xpath('//div[@id="comment-0"]//div[@class="comment-item"]')
            for block in blocks:
    #            block = blocks[3]
                content = ','.join(block.xpath('.//p[@class="comment-con"]/text()'))
                order_info = ','.join(block.xpath('.//div[@class="order-info"]//span/text()'))            
                d_info = {
                        'url_detail': url,
                        'content': content,
                        'order_info': order_info,                    
                        }
                print(d_info)
                print('product:{}, product_page:{}, comment_all:{}'.format(n_product, n_page, n_comment, url))
                print('-'*16)
                n_comment += 1
                mycol_content.update_many(d_info,{'$set':d_info},upsert=True)
                time.sleep(0.1) 
                d_info_all.append(d_info)
            time.sleep(0.3)           
            next_page = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#comment .ui-page .ui-pager-next")))
            browser.execute_script("arguments[0].click();", next_page)
            time.sleep(4)     
            
        
browser.close()      
    















