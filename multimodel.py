import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout,
                             QPushButton, QLabel)

from PyQt5.QtGui import QPixmap, QImage
from multiprocessing import Queue, Process,Manager,Value ,Process ,managers
from pyaudio import PyAudio,paInt16
import wave

import concurrent.futures
from socket import *
import cv2
import time
import pickle
import asyncio
from transfer import *

# 麦克风阵列 (Realtek High Definition Audio)
# PC Camera

# 查看设备列表：
#  ffmpeg -list_devices true -f dshow -i dummy




class window(QWidget):
    def __init__(self):
        super().__init__()
        
        

    def initUI(self):
        grid = QGridLayout(self)
        self.setLayout(grid)

        self.label = QLabel(self)
        # self.label.setFixedSize(600,400)
        btn_start = QPushButton("start", self)
        btn_stop = QPushButton("stop", self)
        btn_startServ =QPushButton("serstart",self)
        btn_stopServ = QPushButton("serstop",self)

        grid.addWidget(btn_start, 1, 1)
        grid.addWidget(btn_stop, 1, 2)
        grid.addWidget(btn_startServ,2,1)
        grid.addWidget(btn_stopServ,2,2)
        grid.addWidget(self.label, 0, 0)

        btn_start.clicked.connect(self.startVideo)
        btn_stop.clicked.connect(self.stopVideo)
        btn_startServ.clicked.connect(self.startServ)
        btn_stopServ.clicked.connect(self.stopServ)


        self.showImage()
        self.show()
    
    def initManager(self):
        self.manager= Manager()
        self.video_running = self.manager.Value("b",True)
        self.video_queue =self. manager.Queue(900)
        self.video_queue_1 = self.manager.Queue(900)
        self.audio_running = self.manager.Value("b",True)
        self.audio_queue= self.manager.Queue(300)
        self.audio_queue_1=self.manager.Queue(300)
        
        self.recv_running =self.manager.Value("b",True)
        # self.video_running = Value("b",True)
        # self.video_queue =Queue(900)
        # self.video_queue_1 = Queue(900)
         

    def showImage(self):
        jpg = QPixmap("media/smile")
        self.label.setPixmap(jpg)
    
    def startVideo(self):
        #startVideo(self.video_running,self.video_queue,self.video_queue_1)
        startAudio(self.audio_running,self.audio_queue,self.audio_queue_1)
    def stopVideo(self):
        stopVideo(self.video_running)
        stopAudio(self.audio_running)
    
    def startServ(self):
        startRecv(self.recv_running)
        pass
    def stopServ(self):
        stopRecv(self.recv_running)
        pass
    
  

video_capture = cv2.VideoCapture(0)
executor = concurrent.futures.ProcessPoolExecutor(8)

#manager = Manager()
video_running= True


def videoTask(_running,_queue,_queue_1):
    print("videoTaskStart"+str(os.getpid()))
    if not video_capture.isOpened(): 
        video_capture.open(0)
    success, frame = video_capture.read()
    cv2.namedWindow("video")
    while success and _running.value: 
        cv2.imshow("video", frame)
        success, frame = video_capture.read()
        try:
            _queue.put(frame,False)
            _queue_1.put(frame,False)
        except Exception as e :
            pass
        cv2.waitKey(1)
    video_capture.release()
    
    cv2.destroyWindow("video")
    return "video finish"

def videoWriteTask(_running,_queue):
    print("videoWriteStart"+str(os.getpid()))
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    size = (width,height)
    fps = int(video_capture.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', '2')
    # fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')

    # 创建视频写入对象
    video_writer = cv2.VideoWriter()
    video_writer.open("media/input.mp4", fourcc,fps, size, True)
    while _running.value:
        frame= _queue.get(True)
        video_writer.write(frame)
    video_writer.release()
    return "video write finish"


def videoSendTask(_running, _queue):
    print("videoSendStart:"+str(os.getpid()))
    serverAddr = ('127.0.0.1', 29901)  # 元祖形式
    udpClient = socket(AF_INET, SOCK_DGRAM)  # 创建客户端
    udpClient.setblocking(False)
    while _running.value:
        frame = _queue.get(True)
        data_to_send = prepare_data(frame)
        for data in data_to_send:
            udpClient.sendto(data, serverAddr)
            #time.sleep(0.01)

    return "video send finish"


def videoFinish(future):
    res = future.result()
    print(res)

def videoWriteFinish(future):
    res = future.result()
    print(res)
   
    

def startVideo(_running,_queue,_queue_1):
    print("startVideo")
    _running.value=True;
   # videoSendTask(_running,_queue)
    video_future = executor.submit(videoTask,_running,_queue,_queue_1)
    video_future.add_done_callback(videoFinish)
    write_future = executor.submit(videoWriteTask,_running,_queue)
    write_future.add_done_callback(videoWriteFinish)

    send_future = executor.submit(videoSendTask,_running,_queue_1)
    send_future.add_done_callback(videoFinish)
    #p= executor.submit(target= videoTask, args= (video_running,))
    #p.start()

    # video_future.add_done_callback()

def startRecv(_running):
    _running.value=True
    # video_future= executor.submit(videoRecv,_running)
    # video_future.add_done_callback(videoFinish)
    audio_future= executor.submit(audioRecv,_running)
    audio_future.add_done_callback(videoFinish)

def stopRecv(_running):
    _running.value=False

def videoRecv(_running):
    addr = ("", 29901)
    udp_erver = socket(AF_INET, SOCK_DGRAM)
    udp_erver.settimeout(1)
    udp_erver.bind(addr)  # 开始监听
    video_writer =cv2.VideoWriter()
    video_writer.open("media/test11.mp4", cv2.VideoWriter_fourcc('m', 'p', '4', '2'),10,(640,480),True)
    cv2.namedWindow("video1")
    while _running.value:
       
        try:
            bufsize = 100 * 1024 * 1024
            datae, addr = udp_erver.recvfrom(bufsize)
            data = pickle.loads(datae)  
         
            if  data.get('data_type') =="video_head":  # 组合数据通知  
                header_datas=data
                frame_lenght= data.get('data_len') 
                #print(frame_lenght)
                frame_datas.clear() 
                frame_arr = np.array([],dtype=np.uint8)
            elif data.get('data_type') == "video_data":  # 补发数据处理
                frame_datas.append(data)
                frame_arr = np.append(frame_arr,data.get("data_arr")) 
                if len(frame_datas)== frame_lenght:
                    print("数据接受完成")
                    frame = np.array(frame_arr).reshape(
                        (header_datas.get("data_shape")[0], header_datas.get("data_shape")[1],-1))
                    #frames.append(frame)
                    #video_writer.write(frame)
                    cv2.imshow("video1",frame)
                    cv2.waitKey(1)

        except Exception as error:
            print(error)
           
            continue
    cv2.destroyWindow("video1")
    video_writer.release()
    print("完成")

def audioRecv(_running):
    addr = ("", 29902)
    udp_erver = socket(AF_INET, SOCK_DGRAM)
    udp_erver.settimeout(1)
    udp_erver.bind(addr)  # 开始监听

    wf = wave.open("media/input11.mp3", 'wb')  # 二进制写入模式
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)  # 两个字节16位
    wf.setframerate(framerate)  # 帧速率
    while _running.value:
        try:
            bufsize = 100 * 1024 * 1024
            datae, addr = udp_erver.recvfrom(bufsize)
            data = pickle.loads(datae)  
            
            if data.get('data_type') =="audio_head":  # 组合数据通知  
                header_datas=data
                frame_lenght= data.get('data_len') 
                    #print(frame_lenght)
                frame_datas.clear() 
                frame_arr = np.array([],dtype=np.uint8)
            elif data.get('data_type') == "audio_data":  # 补发数据处理
                frame_datas.append(data)
                frame_arr = np.append(frame_arr,data.get("data_arr")) 
                if len(frame_datas)== frame_lenght:
                    print("数据接受完成")
                    
                string_audio_data =data.get("data_arr")
                wf.writeframes(b"".join([string_audio_data]))
        
        except Exception as error:
            print(error)
           
            continue
    wf.close()
    print("完成")
    
def startAudio(_running,_queue,_queue_1):
    print("startAudio")
    _running.value=True
    audio_furture = executor.submit(audioTask,_running,_queue,_queue_1)
    audio_furture.add_done_callback(videoFinish)
    write_future =executor.submit(audioWriteTask,_running,_queue)
    write_future.add_done_callback(videoFinish)
    send_future =executor.submit(audioSendTask,_running,_queue_1)
    send_future.add_done_callback(videoFinish)
    pass



framerate = 44100  # 采样率
CHUNK = 4096  # 采样点
channels = 1  # 一个声道
sampwidth = 2  # 两个字节十六位

def audioTask(_running,_queue,_queue_1):
    print("audioTaskStart")
    pa = PyAudio()
    audioStream = pa.open(format=paInt16, channels=channels,rate=framerate,
                                input=True,frames_per_buffer=CHUNK, output=True)
  
  
    while audioStream.is_active() and _running.value:
        # 采集数据
        string_audio_data = audioStream.read(CHUNK)
        # 播放数据
        audioStream.write(string_audio_data)
        try:
            _queue.put(string_audio_data,False)
            _queue_1.put(string_audio_data,False)
        except Exception as e :
            pass
        
    audioStream.close()
    pa.terminate()

    return "audio finish"

def audioWriteTask(_running,_queue):
    print("audioWriteStart")
    wf = wave.open("media/input.mp3", 'wb')  # 二进制写入模式
    wf.setnchannels(channels)
    wf.setsampwidth(sampwidth)  # 两个字节16位
    wf.setframerate(framerate)  # 帧速率
    while _running.value:
        string_audio_data =_queue.get(True)
        wf.writeframes(b"".join([string_audio_data]))
        
    wf.close()
    return "audio write finish"

    
def audioSendTask(_running,_queue):
    print("audioSendStart")
    serverAddr = ('127.0.0.1', 29902)  # 元祖形式
    udpClient = socket(AF_INET, SOCK_DGRAM)  # 创建客户端
    udpClient.setblocking(False)

    while _running.value:
        frame = _queue.get(True)
        data_to_send = prepare_data_audio(frame)
        for data in data_to_send:
            udpClient.sendto(data, serverAddr)
            time.sleep(0.01)

    return "audio send finish"
   

def stopVideo(_running):
    print("stopVideo")
    _running.value = False
    print ("")

def stopAudio(_running):
    print("stopAudio")
    _running.value =False




def arr_split(arr,size):
    s=[]
    for i in range(0,int(len(arr))+1,size):
        c=arr[i:i+size]
        s.append(c)
    return s


def prepare_data(frame):
    
    data_to_send=[]
    split_arr= arr_split(frame.flatten(),32768)

    header = {
        "data_shape":frame.shape,
        "data_type":"video_head",
        "data_len":len(split_arr)
    }
    data_to_send.append(pickle.dumps(header))
   
    for i in   range (len(split_arr)):
        data={
            "data_index":i,
            "data_type":"video_data",
            "data_arr":split_arr[i]
        }
        data_to_send.append(pickle.dumps(data))

    return data_to_send

def prepare_data_audio(frame):
 
    data_to_send=[]
    split_arr= arr_split(frame,32768)

    header = {
        #"data_shape":frame.shape,
        "data_type":"audio_head",
        "data_len":len(split_arr)
    }
    data_to_send.append(pickle.dumps(header))
   
    for i in   range (len(split_arr)):
        data={
            "data_index":i,
            "data_type":"audio_data",
            "data_arr":split_arr[i]
        }
        data_to_send.append(pickle.dumps(data))

    return data_to_send
  


if __name__ == "__main__":

    # pyqt5 应用需要创建一个应用对象
    app = QApplication(sys.argv)

    win = window()
    win.initUI()
    win.initManager()


    sys.exit(app.exec_())
