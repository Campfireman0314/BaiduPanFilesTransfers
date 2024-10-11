"""
打包命令：pyinstaller -F -w -i BaiduPanFilesTransfers.ico --hidden-import=tkinter --clean -n BaiduPanFilesTransfers BaiduPanFilesTransfers.py

:title: BaiduPanFilesTransfers
:site: https://github.com/hxz393/BaiduPanFilesTransfers
:author: assassing, Robin Lin
:contact: hxz393@gmail.com, lqlyd@outlook.com
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""

import os
import shutil
from src.operations import Operations
from src.ui import MainWindow
import traceback
import requests
import threading
import random
import time
import ctypes
from bypy import ByPy
from flask import Flask, request, g, current_app
from flask_cors import CORS
from datetime import datetime


app = Flask(__name__)
CORS(app, resources=r'/*')	 # 注册CORS, "/*" 允许访问所有api
# CORS(app,  resources={r"/*": {"origins": "*.163.com"}})   # 允许163后缀域名跨域
t = threading.Thread()

funny_reply = [
    '*狗腿子还在翻越边境线，现在可不是送信的好时候*',
    '*狗腿子还在地板油冲关，现在可不是送信的好时候*',
    '*狗腿子还在偷渡，现在可不是送信的好时候*',
    '*狗腿子还在试图把车从沼泽地开出去，现在可不是送信的好时候*'
]

def send_popo_alert(receiver, msg, at_list: str = ''):
    url = 'http://qa.leihuo.netease.com:3316/popo_qatool'
    d = {'receiver': receiver, 'msg': msg, 'at_list': at_list}
    r = requests.post(url, data=d)
    return r

@app.route('/', methods=['POST'])
def responser() -> str:
    time.sleep(2)

    data = request.json  # 获取 JOSN 数据, 以字典形式获取参数
    ext_link_str = data.get('message')  # 获取关键字之后的内容
    popo_group_number = data.get('group')

    # Judge if a previous thread is not finished
    global t
    if t.is_alive():
        if ext_link_str == '做掉':
            # Get ID of the running thread
            thread_id = 0
            for _id, thread in threading._active.items():
                if thread is t:
                    thread_id = _id
                    break

            # Raise exception to force terminate
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                thread_id,
                ctypes.py_object(SystemExit)
            )
            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                print('Exception raise failure. Failed to terminate running thread. ')
                send_popo_alert(popo_group_number, '*狗腿子好像挣脱了你的追杀。*')
                return ""

            t.join()

            # Remove old files in cloud
            bp = ByPy()
            bp.rm('/fetch')
            bp.list()

            # Remove files in local folder
            global current_working_local_dir
            if os.path.isdir(current_working_local_dir):
                shutil.rmtree(current_working_local_dir)
                current_working_local_dir = ''


            send_popo_alert(popo_group_number, '*远处传来一声模糊的枪响……*')

        else:
            rnd_num = random.randint(0, len(funny_reply) - 1)
            send_popo_alert(popo_group_number, funny_reply[rnd_num])

    else:
        t = threading.Thread(target=main, args=(popo_group_number, ext_link_str))
        t.start()
        send_popo_alert(popo_group_number, '*狗腿子点了烟上了车：“明白，好货。”*')

    return ""



remote_dir = 'apps/bypy/fetch'
local_dir = '//10.246.77.61/audio/项目资源/【L36】 逆水寒手游/资源管理专区/录音回收/自动回收'
current_working_local_dir = ''

def main(popo_group_number, ext_link_str) -> None:
    """
    主函数，先创建主窗口实例，然后创建动作实例，更新主窗口实例中的动作对象引用，最后运行.

    :return: 无返回值
    """
    # ext_link_str = 'https://pan.baidu.com/s/1wCc8tW9DVLhQx0VC80g6HQ?pwd=3333'
    cookie = 'XFI=6fb6a409-bd5d-969c-c8ec-a6343dc46890; XFCS=71B2B0909908BB6914E11AF3E34AF5CE6DFAF32EFCABD572323162E5F285EF03; XFT=+TN+rQ4RxS/h9mhS54noeDEM1GSZ2zUjQsByVUdNqj8=; BAIDUID=E14271A8C332B666A9BC11B88F880A87:FG=1; BIDUPSID=E14271A8C332B666A9BC11B88F880A87; PSTM=1539937626; BAIDUID_BFESS=E14271A8C332B666A9BC11B88F880A87:FG=1; csrfToken=7rV4_YTD7sa1JhH3x6lKsQW6; newlogin=1; ppfuid=FOCoIC3q5fKa8fgJnwzbE67EJ49BGJeplOzf+4l4EOvDuu2RXBRv6R3A1AZMa49I27C0gDDLrJyxcIIeAeEhD8JYsoLTpBiaCXhLqvzbzmvy3SeAW17tKgNq/Xx+RgOdb8TWCFe62MVrDTY6lMf2GrfqL8c87KLF2qFER3obJGkdximGddNRzN/k8jMV5fwkGEimjy3MrXEpSuItnI4KDxYsf3uyXTlY9fYDtNkm0unKFuzby0Iny2QWgkQh6SmEF7sFREOBO278QA1QAxsZ/BJsVwXkGdF24AsEQ3K5XBbh9EHAWDOg2T1ejpq0s2eFy9ar/j566XqWDobGoNNfmfpaEhZpob9le2b5QIEdiQcF+6iOKqU/r67N8lf+wxW6FCMUN0p4SXVVUMsKNJv2T2Q0Rs14gDuqHJ3rxHJuOGO4LkPV+7TROLMG0V6r0A++zkWOdjFiy1eD/0R8HcRWYvoof6mSAGHJpuboM5joRsCp+HBavJhpxl858h16cMtKQmxzisHOxsE/KMoDNYYE7ucLE22Bi0Ojbor7y6SXfVj7+B4iuZO+f7FUDWABtt/WWQqHKVfXMaw5WUmKnfSR5wwQa+N01amx6X+p+x97kkGmoNOSwxWgGvuezNFuiJQdt51yrWaL9Re9fZveXFsIu/gzGjL50VLcWv2NICayyI8BE9m62pdBPySuv4pVqQ9Sl1uTC//wIcO7QL9nm+0N6JgtCkSAWOZCh7Lr0XP6QztjlyD3bkwYJ4FTiNanaDaDfvCFcZDaj/VMEMO862jQ2RLLqfdoLR7wwMS09x1r6R3F+exLYdZo4uJ/a6uCmluMSGk66HDxtjKMU4HPNa0dthF7UsHf7NW9eE+gwuTQSa7GLWfOy9+ap4iFBQsmjpefgOF89jAHLbnVUejtrqqvdVSQ/4gzJOb0DGzeEZ5GeyMbphmnO7IiEr2hDZP8wWbf7y6eyTEZFJe2EFicttxfkMD05kuRm4sFZh/o1XJ6o5ZazU62XvOvycqQeNHJHilKXv+Y0q7CT6wHNqzprY+XMxDln8dKB7nefcEun8dlqoZs4uNOo+pkpyckwWP4VbWloC92vUUtZ2lVqKiGsvJKvLgaUA9sPnxLHpdf4XomqPJzwaYMRRvnyvNvptYm/H9TJ82EtrgcP/nqg17T/hHrOFW2byp/ouxpI4lF8dQtOogBfcrGXrDHbdYEoz55OAGISs/kEn2kikYfHcMOTvlvvsfnWwwTasVNneN3K++VbMkJcXe6HpWGsfMtkPHUjgkj; BDUSS=1RIV21BUEU5YVlGb2ZMZlJlNU5BV0t6WWFpdEtHSE9VRnBjeHltb3Bib0tHQzluSUFBQUFBJCQAAAAAAAAAAAEAAAAw40c1tefE1L~xyMtmcmVlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAqLB2cKiwdna; BDUSS_BFESS=1RIV21BUEU5YVlGb2ZMZlJlNU5BV0t6WWFpdEtHSE9VRnBjeHltb3Bib0tHQzluSUFBQUFBJCQAAAAAAAAAAAEAAAAw40c1tefE1L~xyMtmcmVlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAqLB2cKiwdna; STOKEN=513451f942084e77a7951df7ac9c50cd44aa004ea5e212fdfc09060db2a8912d; PANPSC=7485732008216229945%3ADJI9ZdfpjgKwsSsf5jnPIXlibiKzYuqj2z8xw%2B8jjD0uiVtc73OZBmRHELtki1kilpUX3TzHZEYGbqupDlB1gr%2FuRlQzprcgJraHXEBmU2UKZcuc2CzyKHUocrtoIijrpZ6XZlA%2FMDmUc3yUq7odftUUVKfu4goaX2XlUsKRi0awbthkud9n5RkJMsEpLrsSMRmYrlFHgmqyTsPEPFbGFW9ESs1hgadE%2BBPsSDpTJNs%3D; ndut_fmt=27F2592E4BA312664B6C9BF090A4FE3C90903303F4D896D2AD94322492987E93; ab_sr=1.0.1_NGIwYzViNjEyNTVlNDllODk0ZGQ5ZGIzOWViYWM0YmQ2YTI0MjUzYzhkZjRkZDY3OTNlNDI4YWFmM2ZmNWVlNGQ5MzRjZDZlYzQxNWRhYjkxZDZiZWVmZjU5MWZiNTQyMGVmM2M1NDMzYzBjMzQ5Mzg5MDBhNjRlZTBiM2Y1ZmIzYWI4MTkwNjIyNzM5NjIyYjhjNWU0NDhiMWUxNDk1MDFhYzY5ZTE0ZmQ0ZTQxMmY5MWZlNzhmMDI0NDRiYzFi'

    # 创建主窗口实例，先传入 None 占位
    root = MainWindow(None)
    # 创建逻辑处理对象并传递主窗口实例
    op = Operations(root)

    # 更新主窗口中的逻辑处理对象引用
    # root.op = op
    # root.run()

    global remote_dir
    global local_dir

    try:
        op.prepare_run_ext(cookie, remote_dir)
        if op.setup_save_ext(ext_link_str) == False:
            raise Exception('Invalid input')
        op.handle_input()
        op.handle_bdstoken()
        op.handle_create_dir(folder_name=op.folder_name)
        op.handle_process_save()
        send_popo_alert(popo_group_number, '*小灵通上是狗腿子的来电：“‘机长’，货都到了，票子就快。”*')
    except Exception as e:
        op.insert_logs(
            f'程序出现未预料错误，信息如下：\n{e}\n{traceback.format_exc()}', False, 3)
        send_popo_alert(popo_group_number, '*小灵通上是狗腿子的来电：“‘机长’，货不对啊——”*')
        return
    finally:
        op.network.s.close()
        op.change_status_ext('stopped')

    bp = ByPy()
    global current_working_local_dir
    try:
        bp.list()
        now = datetime.now() # current date and time
        date_time = now.strftime("%Y%m%d_%H%M%S")
        current_working_local_dir = local_dir + '/' + date_time
        if not os.path.isdir(current_working_local_dir):
            os.mkdir(current_working_local_dir)
        bp.downdir('/fetch', current_working_local_dir)
        bp.rm('/fetch')
        send_popo_alert(popo_group_number, '*小灵通上是狗腿子的来电：“‘机长’，我到了，老地方。”*')
    except Exception as e:
        op.insert_logs(
            f'程序出现未预料错误，信息如下：\n{e}\n{traceback.format_exc()}', False, 3)
        bp.rm('/fetch')
        if os.path.isdir(current_working_local_dir):
            shutil.rmtree(current_working_local_dir)
            current_working_local_dir = ''
        send_popo_alert(popo_group_number, '*小灵通上是狗腿子的来电：“‘机长’，钱被截了”*')
        return


if __name__ == '__main__':
    # main()
    from waitress import serve
    serve(app, host="0.0.0.0", port=1001)
    #app.run('0.0.0.0', port=1001)
