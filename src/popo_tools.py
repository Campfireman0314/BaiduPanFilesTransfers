import requests
import threading
import time
from typing import Dict, Any, Union

def send_popo_alert(
        receiver: str,
        msg: str,
        at_list: str,
        url: str = 'http://qa.leihuo.netease.com:3316/popo_qatool',
        timeout: float = 5.0
    ) -> Union[requests.Response, None]:
    """
    发送POPO告警消息
    
    Args:
        receiver: 消息接收者
        msg: 消息内容
        at_list: @提醒列表
        url: 请求地址 (默认QA环境)
        timeout: 请求超时时间(秒)
    
    Returns:
        Response对象 (成功时) 或 None (失败时)
    
    Raises:
        ValueError: 参数验证失败
        requests.exceptions.RequestException: 网络请求异常
    """
    # 1. 参数验证
    if not all([receiver, msg]):
        raise ValueError("Missing required parameters")
    
    # 2. 准备请求数据 (使用JSON格式更安全)
    payload: Dict[str, Any] = {
        'receiver': receiver,
        'msg': msg,
        'at_list': at_list
    }
    
    try:
        # 3. 发送请求 (添加超时和JSON格式)
        response = requests.post(
            url,
            data=payload,  # 使用json参数自动设置Content-Type
            timeout=timeout
        )
        
        # 4. 检查响应状态
        response.raise_for_status()
        return response
    
    except requests.exceptions.RequestException as e:
        # 5. 异常处理 (实际项目中应添加日志记录)
        # 示例: logger.error(f"POPO alert failed: {str(e)}")
        print(f"Error sending POPO alert: {str(e)}")
        return None
    
class PopoMsg:
    def __init__(self, msg: str, at_list: str = '', receiver: str | None = None):
        self.msg = msg
        self.at_list = at_list
        self.receiver = receiver
    
class PopoBroadcaster:
    def __init__(self, receiver:str = '', url: str = 'http://qa.leihuo.netease.com:3316/popo_qatool'):
        self.__url = url
        self.__receiver = receiver
        self.__at_list = ''
        self.__lock = threading.Lock()
        self.__pending_msgs: list[PopoMsg] = []
        self.__thread: threading.Thread | None = None
        self.__stop_flag: bool = False

    def __del__(self):
        self.stop()

    def __broadcast_loop(self):
        while True:
            with self.__lock:
                if self.__stop_flag:
                    break
                if len(self.__pending_msgs) == 0:
                    time.sleep(0.1)
                    continue
                msg = self.__pending_msgs.pop(0)
                send_popo_alert(msg.receiver, msg.msg, msg.at_list, self.__url)

    def start(self):
        with self.__lock:
            if self.__thread is not None:
                return
            self.__stop_flag = False
            self.__thread = threading.Thread(target=self.__broadcast_loop)
            self.__thread.start()

    def stop(self):
        with self.__lock:
            if self.__thread is None:
                return
            self.__stop_flag = True
            self.__thread.join()
            self.__thread = None
            self.__pending_msgs.clear()

    def set_receiver(self, receiver: str):
        with self.__lock:
            self.__receiver = receiver

    def send(self, msg: str, at_list: str | None = None, receiver: str | None = None) -> None:
        """
        发送POPO告警消息

        Args:
            msg: 消息内容
            at_list: @提醒列表
        
        Returns:
            Response对象 (成功时) 或 None (失败时)
        """
        with self.__lock: 
            if self.__thread is None: return
            self.__pending_msgs.append(PopoMsg(msg, at_list or self.__at_list, receiver or self.__receiver))
