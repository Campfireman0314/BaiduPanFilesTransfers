"""
打包命令：pyinstaller -F -w -i BaiduPanFilesTransfers.ico --hidden-import=tkinter --clean -n BaiduPanFilesTransfers BaiduPanFilesTransfers.py

:title: BaiduPanFilesTransfers
:site: https://github.com/hxz393/BaiduPanFilesTransfers
:author: assassing, Robin Lin
:contact: hxz393@gmail.com, lqlyd@outlook.com
:copyright: Copyright 2024, hxz393. 保留所有权利。
"""

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

    # Judge if a previous thread is not finished.
    global t
    if t.is_alive():
        if ext_link_str == '做掉':
            # Get ID of the running thread
            thread_id = 0
            for _id, thread in threading._active.items():
                if thread is t:
                    thread_id = _id
                    break

            # Raise exception to force terminate.
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
            send_popo_alert(popo_group_number, '*远处传来一声模糊的枪响……*')

        else:
            rnd_num = random.randint(0, len(funny_reply) - 1)
            send_popo_alert(popo_group_number, funny_reply[rnd_num])

    else:
        t = threading.Thread(target=main, args=(popo_group_number, ext_link_str))
        t.start()
        send_popo_alert(popo_group_number, '*狗腿子点了烟上了车：“明白，好货。”*')

    return ""


def main(popo_group_number, ext_link_str) -> None:
    """
    主函数，先创建主窗口实例，然后创建动作实例，更新主窗口实例中的动作对象引用，最后运行.

    :return: 无返回值
    """

    remote_dir = 'apps/bypy'
    local_dir = 'Q:/ByPy'
    # ext_link_str = 'https://pan.baidu.com/s/1wCc8tW9DVLhQx0VC80g6HQ?pwd=3333'
    cookie = 'XFI=1dd30f97-b706-9a91-4e26-41c9db85a645; XFCS=8E3F88CE55D4206389385FD7C5B387BEEB8CDDF4FEE7D8F3D07849F2B3075F03; XFT=R3iCfceZ3X9Ra4u5rOYBWoEeJ/pyUASNgDaPtA6Q79Y=; BIDUPSID=317B888C802554BA5A4DC433FEA0F083; PSTM=1658452399; __bid_n=18bd7d682c97456acafc87; ZFY=Z4v:AkDUo6Bwei58A:Al:B7RjeLhBQyKmi764cjgr5xd4g:C; newlogin=1; H_PS_PSSID=60450_60840; BA_HECTOR=0h2g01a40h2l00a4250g21ak12f9kr1jgcdci1u; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; RT="z=1&dm=baidu.com&si=56405693-60ee-484e-80c5-f6e3d492b399&ss=m21kn06g&sl=2&tt=17r&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf&ld=a7n&ul=2az3&hd=2azm"; BAIDUID=7327D64C53BEF1D6054EB460AFDC1173:FG=1; BAIDUID_BFESS=7327D64C53BEF1D6054EB460AFDC1173:FG=1; BDUSS=BldmZqcWNwYXpNVjV5cG1ER1hrdFdUQTBLNXJ4cGF2TXFwYjBnZzVydVc2QzFuSVFBQUFBJCQAAAAAAAAAAAEAAAAw40c1tefE1L~xyMtmcmVlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJZbBmeWWwZnYz; BDUSS_BFESS=BldmZqcWNwYXpNVjV5cG1ER1hrdFdUQTBLNXJ4cGF2TXFwYjBnZzVydVc2QzFuSVFBQUFBJCQAAAAAAAAAAAEAAAAw40c1tefE1L~xyMtmcmVlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJZbBmeWWwZnYz; STOKEN=d8b157e27c0e337e3af1dca45b9a17999a62fdef68d4b096a394d19cecdd272f; PANWEB=1; Hm_lvt_95fc87a381fad8fcb37d76ac51fefcea=1728460284,1728477355; csrfToken=ONKOSPcFD0jfsO5STPw1UC2j; ndut_fmt=2DD169B3FF09D18C21D218623F818D6F2E2DFF3EA9245DD0B779CA8883638DEC; ab_sr=1.0.1_NjZhMWU5ZmQyNjZjN2JjYWJhZTljNTJlNjZiZWZkOTI2MjA5N2MwZDhkODYwMDg0NzBkZjYxNTI4ZmEwZTQzN2U4OTUyMTkzMDI4NTRlODE2NWM2Y2U3YmZkN2EzZDY4ZDE1M2UyOTE3ZDU5NGI1ZTVkODZiYTdkMTZlYzNjZWI5ZmEwZjVmNWZmZTZhOGFjZjgzNmUzNTE5NTE1MmY3NzZlMTc3YzE2NjgxMTJiNWQyM2JkZjA2M2Q0NTRlOWI0; PANPSC=12162860685606541493%3APBu5R64BDn0wlm%2FIJ26EF1cS2d9ns3O5CM3QoQJ7YXfUUERun5%2BOPd3tsxK%2FuXovCOfgdHnp14%2Blq3aOdzuDDWYa2dyKURQjFl7owtXleijihEIzmOtMnRn%2BOGYsIE0xYqZdy9zZ13kc816WHUcopqIT9ar9kqyBEct689Zi52EbJknp%2BIbkWgf7w8OoZQjac0Z4JFwNQ0FFEIreWjytXwU0coV4hk9L2z8xw%2B8jjD0uiVtc73OZBmRHELtki1kid4u3tn0BShySsVZaqyA8TA%3D%3D'

    # 创建主窗口实例，先传入 None 占位
    root = MainWindow(None)
    # 创建逻辑处理对象并传递主窗口实例
    op = Operations(root)

    # 更新主窗口中的逻辑处理对象引用
    # root.op = op
    # root.run()

    # Ideal logic:
    try:
        op.prepare_run_ext(cookie, remote_dir)
        op.setup_save_ext(ext_link_str)
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

    try:
        bp = ByPy()
        bp.list()
        bp.downdir('/', local_dir)
        send_popo_alert(popo_group_number, '*小灵通上是狗腿子的来电：“‘机长’，我到了，老地方。”*')
    except Exception as e:
        op.insert_logs(
            f'程序出现未预料错误，信息如下：\n{e}\n{traceback.format_exc()}', False, 3)
        send_popo_alert(popo_group_number, '*小灵通上是狗腿子的来电：“‘机长’，钱被截了”*')
        return



if __name__ == '__main__':
    # main()
    app.run('0.0.0.0', port=1001)
