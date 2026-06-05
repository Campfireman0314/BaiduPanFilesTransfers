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
from collections import deque
from bypy import ByPy
from flask import Flask, request
from flask_cors import CORS
from datetime import datetime


app = Flask(__name__)
CORS(app, resources=r'/*')	 # 注册CORS, "/*" 允许访问所有api
# CORS(app,  resources={r"/*": {"origins": "*.163.com"}})   # 允许163后缀域名跨域
t = threading.Thread()
fetch_queue = deque()
queue_lock = threading.Lock()
worker_running = False
current_job = None
stop_requested = False
queued_job_keys = set()
active_job_keys = set()
recent_job_keys = {}
duplicate_suppression_seconds = 30

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


def normalize_fetch_message(ext_link_str) -> str:
    return (ext_link_str or '').strip()


def is_valid_fetch_message(ext_link_str: str) -> bool:
    return bool(ext_link_str and 'pan.baidu.com' in ext_link_str)


def link_preview(ext_link_str: str, limit: int = 120) -> str:
    preview = ' '.join(ext_link_str.split())
    return preview if len(preview) <= limit else f'{preview[:limit - 3]}...'


def fetch_job_key(ext_link_str: str) -> str:
    return ' '.join(normalize_fetch_message(ext_link_str).split())


def prune_recent_job_keys(now=None) -> None:
    now = now or time.time()
    expired_keys = [
        key for key, timestamp in recent_job_keys.items()
        if now - timestamp > duplicate_suppression_seconds
    ]
    for key in expired_keys:
        recent_job_keys.pop(key, None)


def ensure_worker_running() -> None:
    global t
    global worker_running

    with queue_lock:
        if worker_running:
            return

        worker_running = True
        t = threading.Thread(target=queue_worker, daemon=True)
        t.start()


def enqueue_fetch_job(popo_group_number, ext_link_str: str):
    job_key = fetch_job_key(ext_link_str)

    with queue_lock:
        prune_recent_job_keys()
        if job_key in queued_job_keys or job_key in active_job_keys or job_key in recent_job_keys:
            return False, 0, worker_running

        was_running = worker_running
        queue_position = len(fetch_queue) + (1 if current_job else 0) + 1
        fetch_queue.append((popo_group_number, ext_link_str, job_key))
        queued_job_keys.add(job_key)

    ensure_worker_running()
    return True, queue_position, was_running


def clear_pending_jobs() -> int:
    with queue_lock:
        dropped = len(fetch_queue)
        fetch_queue.clear()
        queued_job_keys.clear()
        return dropped


def queue_worker() -> None:
    global worker_running
    global current_job

    try:
        while True:
            with queue_lock:
                if not fetch_queue:
                    return
                current_job = fetch_queue.popleft()
                queued_job_keys.discard(current_job[2])
                active_job_keys.add(current_job[2])

            popo_group_number, ext_link_str, job_key = current_job
            send_popo_alert(
                popo_group_number,
                f'*狗腿子把这单摊开了：“老大，现在是这个：{link_preview(ext_link_str)}”*'
            )

            try:
                main(popo_group_number, ext_link_str)
            except SystemExit:
                with queue_lock:
                    should_stop = stop_requested
                if should_stop:
                    raise
                send_popo_alert(popo_group_number, '*小灵通上是狗腿子的来电：“这单货单不对，先跳过。”*')
            except Exception:
                send_popo_alert(popo_group_number, '*小灵通上是狗腿子的来电：“这单半路翻车了，先跳过。”*')
                traceback.print_exc()
            finally:
                with queue_lock:
                    active_job_keys.discard(job_key)
                    recent_job_keys[job_key] = time.time()
                    current_job = None
    finally:
        should_restart = False
        with queue_lock:
            worker_running = False
            current_job = None
            should_restart = bool(fetch_queue)
            prune_recent_job_keys()

        if should_restart:
            ensure_worker_running()

@app.route('/', methods=['POST'])
def responser() -> str:
    time.sleep(2)

    data = request.json or {}  # 获取 JOSN 数据, 以字典形式获取参数
    ext_link_str = normalize_fetch_message(data.get('message'))  # 获取关键字之后的内容
    popo_group_number = data.get('group')

    if not popo_group_number:
        return ""

    global t
    global stop_requested

    if ext_link_str == '做掉':
        dropped = clear_pending_jobs()
        if t.is_alive():
            with queue_lock:
                stop_requested = True
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
            if res == 0:
                with queue_lock:
                    stop_requested = False
                print('Exception raise failure. Failed to find running thread. ')
                send_popo_alert(popo_group_number, '*狗腿子好像已经不在车上了。*')
                return ""

            if res > 1:
                ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
                with queue_lock:
                    stop_requested = False
                print('Exception raise failure. Failed to terminate running thread. ')
                send_popo_alert(popo_group_number, '*狗腿子好像挣脱了你的追杀。*')
                return ""

            t.join()
            with queue_lock:
                stop_requested = False

            # Remove old files in cloud
            bp = ByPy()
            bp.rm('/fetch')
            bp.list()

            # Remove files in local folder
            global current_working_local_dir
            if current_working_local_dir:
                cleanup_temp_download_dir(current_working_local_dir)
                current_working_local_dir = ''

            send_popo_alert(popo_group_number, f'*远处传来一声模糊的枪响……已清掉 {dropped} 单排队。*')
        else:
            send_popo_alert(popo_group_number, f'*车库里没人，已清掉 {dropped} 单排队。*')
        return ""

    if not is_valid_fetch_message(ext_link_str):
        send_popo_alert(popo_group_number, '*狗腿子看了看条子：“这不像百度网盘链接。”*')
        return ""

    queued, queue_position, was_running = enqueue_fetch_job(popo_group_number, ext_link_str)
    if not queued:
        send_popo_alert(popo_group_number, f'*这单已经在路上或刚跑完了，先不重复处理：{link_preview(ext_link_str)}*')
        return ""

    if not was_running:
        send_popo_alert(popo_group_number, f'*狗腿子点了烟上了车：“明白，好货。” 队列：{link_preview(ext_link_str)}*')
    else:
        rnd_num = random.randint(0, len(funny_reply) - 1)
        send_popo_alert(
            popo_group_number,
            f'{funny_reply[rnd_num]} 已入队，前面还有 {queue_position - 1} 单：{link_preview(ext_link_str)}'
        )

    return ""



remote_dir = 'apps/bypy/fetch'
local_dir = '//10.246.77.61/audio/项目资源/【L36】 逆水寒手游/资源管理专区/录音回收/自动回收'
download_tmp_dir_name = '_fetch_tmp'
current_working_local_dir = ''


def build_download_dirs(now=None):
    now = now or datetime.now()
    day_dir = os.path.join(local_dir, now.strftime("%Y%m%d"))
    temp_dir = os.path.join(
        local_dir,
        download_tmp_dir_name,
        now.strftime("%Y%m%d_%H%M%S_%f")
    )
    return day_dir, temp_dir


def unique_destination_path(destination_dir: str, name: str) -> str:
    candidate = os.path.join(destination_dir, name)
    if not os.path.exists(candidate):
        return candidate

    stem, ext = os.path.splitext(name)
    index = 1
    while True:
        candidate = os.path.join(destination_dir, f'{stem}_{index}{ext}')
        if not os.path.exists(candidate):
            return candidate
        index += 1


def move_downloaded_items(temp_dir: str, day_dir: str) -> None:
    os.makedirs(day_dir, exist_ok=True)
    for name in os.listdir(temp_dir):
        source = os.path.join(temp_dir, name)
        destination = unique_destination_path(day_dir, name)
        shutil.move(source, destination)


def cleanup_temp_download_dir(temp_dir: str) -> None:
    if temp_dir and os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)

    temp_parent = os.path.dirname(temp_dir) if temp_dir else ''
    if temp_parent:
        try:
            os.rmdir(temp_parent)
        except OSError:
            pass


def main(popo_group_number, ext_link_str) -> None:
    """
    主函数，先创建主窗口实例，然后创建动作实例，更新主窗口实例中的动作对象引用，最后运行.

    :return: 无返回值
    """
    # ext_link_str = 'https://pan.baidu.com/s/1wCc8tW9DVLhQx0VC80g6HQ?pwd=3333'
    cookie = 'XFI=0113ffb7-1c35-8a25-d0de-ca1303557c1d; XFCS=0183E154D63F2DF834F0CA4F06F172A1245817C31A5EA86FEE5D559063148853; XFT=IdHICLcNhkwEmvRkP0Y0hAmLjbG3yOUnt12n/9mVCwI=; BAIDUID_BFESS=533AA039A6950F50B3758239469ED095:FG=1; PANWEB=1; csrfToken=o0UfzfCj_6TIVoO4uXxy-reF; Hm_lvt_7a3960b6f067eb0085b7f96ff5e660b0=1780565151; HMACCOUNT=5867B8E89A5E4749; BDCLND=GqFQKiP9bAUCpeOsy1ShWXkn3tshd0e7NtCQ2XJDF6c%3D; Hm_lpvt_7a3960b6f067eb0085b7f96ff5e660b0=1780565153; newlogin=1; ploganondeg=1; ppfuid=9788a854bc31c1fa3c85e6146f3a1059; XFI=7e720b00-5ff7-11f1-9d71-fb8bc3dcf273; XFCS=C2EEDB0BBE46DD1EC70935350419BDC3E679183EC6127EAC89DA8F0154D04275; XFT=mK0Msk8HJEQoTlYDqvqAaDCGn2utPj69jA74R50R4SI=; BDUSS=FIUjRiaERPeG1NSldvNWxkYkw3Qm81YXNtcU9TUEhpdmxHfnJjZWJWRGowVWhxSVFBQUFBJCQAAAAAAAAAAAEAAAAw40c1tefE1L~xyMtmcmVlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAONEIWrjRCFqbU; BDUSS_BFESS=FIUjRiaERPeG1NSldvNWxkYkw3Qm81YXNtcU9TUEhpdmxHfnJjZWJWRGowVWhxSVFBQUFBJCQAAAAAAAAAAAEAAAAw40c1tefE1L~xyMtmcmVlAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAONEIWrjRCFqbU; STOKEN=bdfe2e80baa4be4354ea1137b45d03147f16be0e0b4e2516c3fd60d9adb5e05e; Hm_lvt_182d6d59474cf78db37e0b2248640ea5=1780565222; Hm_lpvt_182d6d59474cf78db37e0b2248640ea5=1780565222; PANPSC=5588841341407733514%3Afuky8UrKH%2BnsP6R1CTude1cS2d9ns3O5C61tf8CKQki8amN%2BJMzWzPEZy5xVYxZqIi%2Fo2hbQKHo4EhHQlt8W9eNHiOwr%2ByPWC%2BYWBHXUXSu2ddnuR8GWugsgWfSxLY3STmybY5q%2Fl%2BFtcQe%2BbgwEaXWegKR%2ByMKcWP%2FWBC2ONxfgK8WiEYvObjEIKJQ%2BkRn2uPZxTPIZzXRtoLnfYC42LfDSJFbrrClxohP1qv2SrIERy3rz1mLnYRsmSen4huRaB%2FvDw6hlCNpzRngkXA1DQUUQit5aPK1fBTRyhXiGT0vbPzHD7yOMPS6JW1zvc5kGZEcQu2SLWSJ3i7e2fQFKHA%3D%3D; ndut_fmt=C4ED512250735DDB232450E45DA02EB836D3FF44CC39FA0031BE64FC1CA17CC9; ab_sr=1.0.1_NWVhNDMxYTVmMTU5NjRlNTZhZmVjYTY4M2VjMDBiMTNhMzk4YTA5MDg1ZjU0NTQ0MTAyNTdiZWY3NWY3NDIxY2FhZGQ0YzMxNzMyNzEzZDRjMzRjMTIxNTM2MjQyMjAzZGE1OTcyN2NjMzVjNzJmNDY2ZDYwZWVjZWY2ODE5ZTUzODg1NmRlMDUwMDc1ZmEwZmM2OGI3N2RiMmY3ZDA3MzI0NDgwMDQwMjljZGZjZjRiNTM1ZTZjYzJiNjk3ZmM5'
    
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
        if op.failed_task_count:
            raise Exception(f'{op.failed_task_count} transfer task(s) failed')
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
        day_dir, temp_dir = build_download_dirs()
        current_working_local_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        bp.downdir('/fetch', current_working_local_dir)
        move_downloaded_items(current_working_local_dir, day_dir)
        cleanup_temp_download_dir(current_working_local_dir)
        current_working_local_dir = ''
        bp.rm('/fetch')
        send_popo_alert(popo_group_number, f'*小灵通上是狗腿子的来电：“‘机长’，我到了，{os.path.basename(day_dir)} 那个大箱子里。”*')
    except Exception as e:
        op.insert_logs(
            f'程序出现未预料错误，信息如下：\n{e}\n{traceback.format_exc()}', False, 3)
        bp.rm('/fetch')
        if current_working_local_dir:
            cleanup_temp_download_dir(current_working_local_dir)
            current_working_local_dir = ''
        send_popo_alert(popo_group_number, '*小灵通上是狗腿子的来电：“‘机长’，钱被截了”*')
        return


if __name__ == '__main__':
    # main()
    from waitress import serve
    serve(app, host="0.0.0.0", port=1001)
    #app.run('0.0.0.0', port=1001)
