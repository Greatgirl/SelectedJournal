
import re
import time
import requests


def LetpubJournalStatistic(journal_name: str) -> list:
    headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        }
    status_code = True
    cite_score = []
    journal_split = []
    journal_date = []
    journal_na = []

    while status_code:
        try:
            post_dic = {'searchname': journal_name, 'searchsort': 'relevance'}
            search_url = 'http://www.letpub.com.cn/index.php?page=journalapp&view=search'
            res = requests.post(search_url, post_dic, headers=headers)
        except Exception as e:
            print(f'letpub禁掉了你的网络，等一会，按ctrl+c终止终端可重新查询，错误信息:{e}')
            time.sleep(5)
            continue

        if res.status_code == 200:
            status_code = False
        else:
            print(f'letpub禁掉了你的网络，等一会，{journal_name}')
            time.sleep(5)
            continue

        journal_element = re.findall('</style>.*?<tr>(.*?)</tr>', res.text, re.S)[1]
        if '无匹配结果' in journal_element:
            print(f'{journal_name}查询成功，但无匹配结果\n')
            return cite_score, journal_split, journal_date, journal_na
        
        print(f'{journal_name}查询成功: {journal_element}\n')

        cite_score = re.findall(r'CiteScore:(\d+.\d+)', journal_element, re.S)
        journal_split = re.findall(r'(\d区)</td>', journal_element, re.S)
        
        td_elements = re.findall(r'(<td.*?</td>)', journal_element, re.S)
        for td_ele in td_elements:
            # 审稿周期
            date_keys = ['月', '周', 'weeks']
            for j in date_keys:
                if j in td_ele:
                    journal_date = re.findall(r'>(.*?)</td>', td_ele, re.S)
                    break
            # 是否OA
            if 'No' in td_ele or 'Yes' in td_ele:
                journal_na = re.findall(r'>(.*?)</td>', td_ele, re.S)
                continue
    return cite_score, journal_split, journal_date, journal_na
