
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import urllib

from journal_statistic import LetpubJournalStatistic

class BaiduScholarSearch(object):
    """
    根据关键词自动搜索论文，并提取文章名称、链接、期刊等关键信息
    """
    def __init__(self) -> None:
        self._init_browser()
        self._init_baidu_scholar_meta()
        self._journal_info_cache = {}

    def _init_baidu_scholar_meta(self):
        self.papers_element_xpath = '/html/body/div[1]/div[4]/div[3]/div[2]/div/div[@class="result sc_default_result xpath-log"]'
        self.paper_name_element_xpath = 'div[1]/h3/a'
        self.paper_link_attribute = 'href'
        self.paper_journal_findkey = r'<a class="journal_title".*?>(.*?)</a>'

    def _init_browser(self):
        self.browser = webdriver.Chrome(options=webdriver.ChromeOptions().add_experimental_option('excludeSwitches', ['enable-automation']))
        self.browser.implicitly_wait(10)
        self.wait = WebDriverWait(self.browser, 15)
        self.ac = ActionChains(self.browser)

    def _clear_temp(self):
        self.word = ''  # 关键词
        self.occt = 'title'  # 检索类型
        self.page_number = 999  # 检索总页码
        self.year_low = 2018 # 检索起始年份
        self.result_dic = {'all_paper_num': 0,
                   'English Journal': {},
                   'Chinese Journal': {},
                   'Conference': {},
                   }

        self.paper_count = 0
        self.english_count = 0
        self.chinese_count = 0
        self.conference_count = 0

    def _wait_by_xpath(self, patten):
        self.wait.until(EC.presence_of_element_located((By.XPATH, patten)))

    def run_search(self, word: str, occt="title", year_low=2018) -> dict:
        self._clear_temp()
        self.word = word
        self.occt = occt
        self.year_low = year_low

        pn_current = 0
        while pn_current <= self.page_number:
            if not self._request_search_results(pn_current):
                break
            pn_current += 1
        self.result_dic['all_paper_num'] = {
            'all_count': self.paper_count,
            'Chinese Journal': self.chinese_count,
            'English Journal': self.english_count,
            'Conference': self.conference_count,
        }
        self.result_dic['Chinese Journal'] = {key: self.result_dic['Chinese Journal'][key] for key in
                                              sorted(self.result_dic['Chinese Journal'].keys())}
        self.result_dic['English Journal'] = {key: self.result_dic['English Journal'][key] for key in
                                              sorted(self.result_dic['English Journal'].keys())}
        self.result_dic['Conference'] = {key: self.result_dic['Conference'][key] for key in
                                              sorted(self.result_dic['Conference'].keys())}
        return self.result_dic
    
    def _request_search_results(self, pn_current=0) -> bool:
        url = self._pack_search_request(pn_current)
        try:
            self.browser.get(url)
        except Exception as e:
            print(f'谷歌浏览器未正常运行，按ctrl+c终止终端可重新进入软件点击运行。错误信息：{e}\n')
            return False
        
        print(f'百度学术搜索第{pn_current + 1}页（无搜索结果可以复制粘贴链接去浏览器查看）:\n {url}\n')
        time.sleep(1)

        try:
            papers_element = self.browser.find_elements(by=By.XPATH, value=self.papers_element_xpath)
        except Exception as e:
            print(f'文章资源定位异常，请检查检索页是否正常。错误信息：{e}\n')
            return False
        if not papers_element:
            print(f'第{pn_current + 1}页未找到论文资源，请检查关键词是否有效、浏览器是否正常\n')
            return False
        
        first_paper = ''
        for i, paper_element in enumerate(papers_element):
            try:
                paper_name = paper_element.find_element(by=By.XPATH, value=self.paper_name_element_xpath)
                paper_link = paper_name.get_attribute(self.paper_link_attribute)
                paper_name = paper_name.text
            except Exception as e:
                print(f'请检查软件打开的谷歌浏览器是否被人为（异常）终止，程序运行期间不要关谷歌闭浏览器，谢谢配合。错误信息：{e}\n')
                break
            if paper_link == first_paper:
                # all page return
                return False
            first_paper = paper_link if i == 0 else first_paper
            
            journal_name = self._find_journal_of_paper(paper_link)
            if not journal_name:
                continue
            
            self.paper_count += 1
            if self.is_contain_chinese(journal_name):
                self.chinese_count += 1
            elif 'Conference' in journal_name:
                self.conference_count += 1
            else:
                self.english_count += 1  
            
            print(f'第{self.paper_count}篇论文 论文名：{paper_name} 论文链接：{paper_link} 期刊名：{journal_name}\n')
            try:
                self._statistic_paper_journal(paper_name, paper_link, journal_name)
            except Exception as e:
                print(f'统计期刊信息异常，请检查，错误信息：{e}\n')
                continue
            journal_type, journal_info = self._journal_info_cache.get(journal_name)
            print(f'期刊类型：{journal_type}  期刊信息：{journal_info}\n')      
        return True
    
    def _pack_search_request(self, pn_current=0) -> str:
        if self.occt == "any":
            url = f'https://xueshu.baidu.com/s?wd={self.word}&pn={pn_current}0&tn=SE_baiduxueshu_c1gjeupa&bs=&ie=utf-8&sc_f_para=sc_tasktype%3D%7BfirstAdvancedSearch%7D&sc_from=&sc_as_para=&bcp=2&filter=sc_year%3D%7B{self.year_low}%2C%2B%7D'
        else:
            url = f'https://xueshu.baidu.com/s?wd=intitle%3A{self.word}&pn={pn_current}0&tn=SE_baiduxueshu_c1gjeupa&bs=&ie=utf-8&sc_f_para=sc_tasktype%3D%7BfirstAdvancedSearch%7D&sc_from=&sc_as_para=&bcp=2&filter=sc_year%3D%7B{self.year_low}%2C%2B%7D'
        # url= urllib.request.quote(url, safe=";/?:@&=+$,", encoding="utf-8")
        return url 
       
    def is_contain_chinese(self, check_str):
        for ch in check_str:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True
        return False
    
    def _find_journal_of_paper(self, paper_link) -> str:
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        }
        try:
            res = requests.get(paper_link, headers=headers).text
        except Exception as e:
            print(f'百度禁掉了你的网络，等一会，按ctrl+c终止终端可重新查询，错误信息：{e}\n')
            time.sleep(5)
            return
        journal_name = re.findall(self.paper_journal_findkey, res, re.S)
        if not journal_name:
            return
        
        journal_name = journal_name[0]
        if ': ' in journal_name:
            journal_name = journal_name.split(': ')[0]
        if '&amp;' in journal_name:
            journal_name = journal_name.replace('&amp;', '&')
        if '&#039;' in journal_name:
            journal_name = journal_name.replace('&#039;', "'")
        return journal_name
    
    def _statistic_journal_infomation(self, journal_name) -> list:
        journal_type = ''
        if self.is_contain_chinese(journal_name):
            journal_type = 'Chinese Journal'
            journal_info = f'{journal_name}'
        elif 'Conference' in journal_name:
            journal_type = 'Conference'
            journal_info = f'{journal_name}'
        else:
            journal_type = 'English Journal'
            try:
                cite_score, journal_split, journal_date, journal_na = LetpubJournalStatistic(journal_name)
            except Exception as e:
                print(f'Letpub查找期刊{journal_name}异常，请检查，错误信息：{e}\n')
                return journal_type, journal_info
            
            journal_split_info = journal_split[0] if len(journal_split) > 0 else '期刊数据库未收录'
            cite_score_info = cite_score[0] if len(cite_score) > 0 else '无记录'
            journal_date_info = journal_date[0] if len(journal_date) > 0 else '无记录'
            journal_na_info = journal_na[0] if len(journal_na) > 0 else '无记录'
            journal_info = f'{journal_split_info} Citescore:{cite_score_info} 审稿周期:{journal_date_info} 是否NA:{journal_na_info} {journal_name}'
        return journal_type, journal_info

    def _statistic_paper_journal(self, paper_name, paper_link, journal_name):
        if not self._journal_info_cache.get(journal_name):
            try:
                journal_type, journal_info = self._statistic_journal_infomation(journal_name)
            except Exception as e:
                print(f'统计期刊信息异常，请检查，错误信息：{e}\n')
                return
            self._journal_info_cache[journal_name] = {journal_type, journal_info}
        else:
            journal_type, journal_info = self._journal_info_cache[journal_name]
        
        if not self.result_dic[journal_type].get(journal_info):
            self.result_dic[journal_type][journal_info] = []
        self.result_dic[journal_type][journal_info].append({paper_name: paper_link})
        for i in list(self.result_dic[journal_type].keys()):
            if '共' in self.result_dic[journal_type][i][0]:
                self.result_dic[journal_type][i][0] = f'共{len(self.result_dic[journal_type][i])-1}篇'
            else:
                self.result_dic[journal_type][i].insert(0, f"共1篇")
        return


class GoogleScholarSearch(BaiduScholarSearch):
    def __init__(self):
        super(GoogleScholarSearch, self).__init__()
        self._init_google_scholar_meta()

    def _init_google_scholar_meta(self):
        self.papers_element_xpath = '/html/body/div[1]/div[4]/div[3]/div[2]/div/div[@class="result sc_default_result xpath-log"]'
        self.paper_name_element_xpath = 'div[1]/h3/a'
        self.paper_link_attribute = 'href'
        self.paper_journal_findkey = r'<a class="journal_title".*?>(.*?)</a>'
        # '/html/body/div/div[10]/div[2]/div[3]/div[2]/div[1]/div[2]/div[3]/a[2]' '[@class="gs_or_cit gs_or_btn gs_nph"]'
        # '/html/body/div[1]/div[4]/div/div[2]/div/div[2]/a[1]'
    def _request_search_results(self, pn_current=0) -> bool:
        url = self._pack_search_request(pn_current)
        try:
            self.browser.get(url)
        except Exception as e:
            print(f'谷歌浏览器未正常运行，按ctrl+c终止终端可重新进入软件点击运行。错误信息：{e}\n')
            return False
        
        print(f'谷歌学术搜索第{pn_current + 1}页（无搜索结果可以复制粘贴链接去浏览器查看）:\n {url}\n')
        time.sleep(1)

        try:
            papers_element = self.browser.find_elements(by=By.XPATH, value=self.papers_element_xpath)
        except Exception as e:
            print(f'文章资源定位异常，请检查检索页是否正常。错误信息：{e}\n')
            return False
        if not papers_element:
            print(f'未找到论文资源，请检查关键词是否有效、浏览器是否正常\n')
            return False
        
        first_paper = ''
        for i, paper_element in enumerate(papers_element):
            try:
                paper_name = paper_element.find_element(by=By.XPATH, value=self.paper_name_element_xpath)
                paper_link = paper_name.get_attribute(self.paper_link_attribute)
                paper_name = paper_name.text
            except Exception as e:
                print(f'请检查软件打开的谷歌浏览器是否被人为（异常）终止，程序运行期间不要关谷歌闭浏览器，谢谢配合。错误信息：{e}\n')
                break
            if paper_link == first_paper:
                # all page return
                return False
            first_paper = paper_link if i == 0 else first_paper
            
            journal_name = self._find_journal_of_paper(paper_link)
            if not journal_name:
                continue
            self.paper_count += 1
            print(f'第{self.paper_count}篇论文 论文名：{paper_name} 论文链接：{paper_link} 期刊名：{journal_name}\n')
            try:
                self._statistic_paper_journal(paper_name, paper_link, journal_name)
            except Exception as e:
                print(f'统计期刊信息异常，请检查，错误信息：{e}\n')
                continue
            journal_type, journal_info = self._journal_info_cache.get(journal_name)
            print(f'期刊类型：{journal_type}  期刊信息：{journal_info}\n')

            if journal_type == 'Chinese Journal':
                self.chinese_count += 1
            elif journal_type == 'English Journal':
                self.english_count += 1
            elif journal_type == 'Conference':
                self.conference_count += 1        
        return True
    
    def _pack_search_request(self, pn_current=0) -> str:
        if self.occt == "any":
            url = f'https://scholar.google.com/scholar?start={pn_current}0&q={self.word}&hl=zh-CN&as_sdt=0,5&as_ylo={self.year_low}'
        else:
            url = f'https://scholar.google.com/scholar?start={pn_current}0&q=allintitle:+{self.word}&hl=zh-CN&as_sdt=0,5&as_ylo={self.year_low}'
        return url 
    
    def _find_journal_of_paper(self, paper_link) -> str:
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        }
        try:
            res = requests.get(paper_link, headers=headers).text
        except Exception as e:
            print(f'百度禁掉了你的网络，等一会，按ctrl+c终止终端可重新查询，错误信息：{e}\n')
            time.sleep(5)
            return
        journal_name = re.findall(self.paper_journal_findkey, res, re.S)
        if not journal_name:
            return ''
        
        journal_name = journal_name[0]
        if ': ' in journal_name:
            journal_name = journal_name.split(': ')[0]
        if '&amp;' in journal_name:
            journal_name = journal_name.replace('&amp;', '&')
        if '&#039;' in journal_name:
            journal_name = journal_name.replace('&#039;', "'")
        return journal_name

def ScholarSearch(word: str, occt="title", year_low=2018, engine="google") -> dict:
    if engine == "baidu":
        search = BaiduScholarSearch()
    else:
        search = GoogleScholarSearch()
    return search.run_search(word, occt, year_low)