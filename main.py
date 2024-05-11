import json
import os
import time
import tkinter as tk
from scholar_search import ScholarSearch

def wd_split_dou(wd, num=1):
    wd_new = ''
    if ',' in wd:
        wd_lis = wd.split(',')
    elif '，' in wd:
        wd_lis = wd.split('，')
    else:
        return f'({wd})'

    if num == 1:
        for i in range(len(wd_lis)):
            if i == 0:
                wd_new = f'"{wd_lis[i].strip()}"'
            else:
                wd_new = wd_new + ' + '+ f'"{wd_lis[i].strip()}"'

    elif num == 2:
        wd_lis.reverse()
        for i in range(len(wd_lis)):
            if i == 0:
                wd_new = wd_lis[i].strip()
            else:
                wd_new = wd_new + ' | '+ wd_lis[i].strip()

    return f'({wd_new})'


# 按扭调用的函数，
def reg():
    wd1 = e_keyword1.get()
    wd2 = e_keyword2.get()

    if wd1:
        wd = wd_split_dou(wd1, num=1)
    elif wd2:
        wd = wd_split_dou(wd2, num=2)
    else:
        wd = '(video+captioning)'

    occt = 'any' if e_pos.get() == '1' else 'title'
    year_low = e_year.get() if e_year.get() else '2018'
    engine = 'google' if e_engine.get() == '1' else 'baidu'

    now_time = str(time.strftime("%H_%M_%S", time.localtime(time.time())))
    fpath = e_fpath.get()
    fpath = fr'{fpath}'

    print(f'\n如果路径无用，检查路径，{fpath}是否存在\n')
    if not fpath:
        dir = os.path.dirname(os.path.abspath(__file__))
        fpath = os.path.join(dir, f'result_{now_time}.txt')
    else:
        fpath = os.path.join(fpath, f'result_{now_time}.txt')

    try:
        dict = ScholarSearch(word=wd, occt=occt, year_low=year_low, engine=engine)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(json.dumps(dict, ensure_ascii=False))
            f.flush()
        l_msg['text'] = '成功获取所有期刊，谢谢使用！~\n'
    except KeyboardInterrupt:
        print('手动终止，可以前往软件重新输入检索词，重新运行软件\n')
    except Exception as e:
        l_msg['text'] = f'异常终止，错误信息：{e}\n'

if __name__ == '__main__':
    root = tk.Tk()
    root.geometry('750x350')
    root.title('论文选刊工具')

    l_keyword1 = tk.Label(root, text='包含精确检索词\n(多个检索词以逗号，分隔）：')
    l_keyword1.grid(row=1, sticky=tk.W)
    e_keyword1 = tk.Entry(root)
    e_keyword1.grid(row=1, column=1, sticky=tk.W)

    l_keyword2 = tk.Label(root, text='包含至少一个检索词\n(多个检索词以逗号，分隔）：')
    l_keyword2.grid(row=2, sticky=tk.W)
    e_keyword2 = tk.Entry(root)
    e_keyword2.grid(row=2, column=1, sticky=tk.W)

    l_pos = tk.Label(root, text='出现检索词的位置在\n（输入0为位于标题，默认为0\n输入1为位于文章任何位置）')
    l_pos.grid(row=3, sticky=tk.W)
    e_pos = tk.Entry(root)
    e_pos.grid(row=3, column=1, sticky=tk.W)

    l_year = tk.Label(root, text='多少年之后\n（默认2018年之后）：')
    l_year.grid(row=4, sticky=tk.W)
    e_year = tk.Entry(root)
    e_year.grid(row=4, column=1, sticky=tk.W)

    l_engine = tk.Label(root, text='检索引擎\n（输入0为baidu，\n默认为baidu）')
    l_engine.grid(row=5, sticky=tk.W)
    e_engine = tk.Entry(root)
    e_engine.grid(row=5, column=1, sticky=tk.W)

    l_fpath = tk.Label(root, text='结果文件存放的文件夹地址 \n（****必填****）：')
    l_fpath.grid(row=6, sticky=tk.W)
    e_fpath = tk.Entry(root)
    e_fpath.grid(row=6, column=1, sticky=tk.W)

    b_l = tk.Label(root, text='程序启动后不要关掉谷歌浏览器\n关掉它程序会立马停止')
    b_l.config(fg='red',font=18)
    b_l.grid(row=7, sticky=tk.W)
    b_login = tk.Button(root, text='点击运行软件（运行期间程序会假死，终端会打印结果，ctrl+c 关闭终端运行即恢复）', command=reg)
    b_login.grid(row=7, column=1, sticky=tk.W)
    b_login.config(fg='red')

    l_msg = tk.Label(root, text='')
    l_msg.grid(row=8)
    l_msg.config(fg='red', font=35)

    root.mainloop()
