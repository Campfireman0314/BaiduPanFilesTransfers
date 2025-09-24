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
from config import *

app = Flask(__name__)
# CORS(app, resources=r'/*')	 # 注册CORS, "/*" 允许访问所有api
CORS(app,  resources={r"/*": {"origins": "*.163.com"}})   # 允许163后缀域名跨域
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

current_working_local_dir = ''

def main(popo_group_number, ext_link_str) -> None:
    """
    主函数，先创建主窗口实例，然后创建动作实例，更新主窗口实例中的动作对象引用，最后运行.

    :return: 无返回值
    """
    # ext_link_str = 'https://pan.baidu.com/s/1wCc8tW9DVLhQx0VC80g6HQ?pwd=3333'
    
    # 创建主窗口实例，先传入 None 占位
    root = MainWindow(None)
    # 创建逻辑处理对象并传递主窗口实例
    op = Operations(root)

    # 更新主窗口中的逻辑处理对象引用
    # root.op = op
    # root.run()

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
        current_working_local_dir = local_dir + '/' + date_time + "_TEMP_NO_MODIFICATION"
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
