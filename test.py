import cv2
import socket
import subprocess as sp
import sys
import time
import threading
from PIL import Image, ImageTk
from PyQt5.QtCore import QThread, pyqtSignal, QDateTime,QUrl
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QGridLayout, QLabel, QPushButton
from PyQt5 import QtMultimedia
import os

import numpy as np
import wave
from datetime import datetime
from pyaudio import PyAudio, paInt16
import pickle

from transfer import *



class window(QDialog):
    def __init__(self):
        super().__init__()
        # 视频参数
        self.video_capture = cv2.VideoCapture(0)
        self.video_thread = True
        self.audio_thread = True
        self.width = int(self.video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.video_count=0
        self.audio_count= 0
        self.audio_file= "media/audio.mp3"
        self.video_file ="media/input.mp4"

        # 音频参数
      
        self.framerate = 44100  # 采样率
        self.CHUNK = 4096  # 采样点
        self.channels = 1  # 一个声道
        self.sampwidth = 2  # 两个字节十六位
        self.TIME = 2  # 条件变量，可以设置定义录音的时间
        self.filename = datetime.now().strftime("%Y-%m-%d_%H_%M_%S")+".wav"

        self.intUI()
        self.path= os.getcwd()
        print("当前路径："+ self.path)

    def intUI(self):

        self.btnStart = QPushButton('Start', self)
        self.btnStop = QPushButton('Stop', self)
        self.btnPlay = QPushButton('Play', self)
        self.btnStopVideo = QPushButton('sockStart', self)
        self.label = QLabel()
        self.label.resize(self.width, self.height)


# 布局设定
        layout = QGridLayout(self)
        layout.addWidget(self.label, 0, 1, 4, 4)
        layout.addWidget(self.btnStart, 4, 1, 1, 1)
        layout.addWidget(self.btnStop, 4, 2, 1, 1)
        layout.addWidget(self.btnPlay, 4, 3, 1, 1)
        layout.addWidget(self.btnStopVideo, 4, 4, 1, 1)

        # 信号与槽进行连接，信号可绑定普通成员函数
        self.btnStart.clicked.connect(self.Start)
        self.btnStop.clicked.connect(self.Stop)
        self.btnPlay.clicked.connect(self.Play)
        self.btnStopVideo.clicked.connect(self.stopVideo)

    def openSlot(self):
        # 调用存储文件
        fileName, tmp = QFileDialog.getOpenFileName(
            self, 'Open Image', 'Image', '*.png *.jpg *.bmp')
        if fileName is '':
            return
        # 采用OpenCV函数读取数据
        self.img = cv2.imread(fileName, -1)
        if self.img.size == 1:
            return
        self.refreshShow()

    def saveSlot(self):
        # 调用存储文件dialog
        fileName, tmp = QFileDialog.getSaveFileName(
            self, 'Save Image', 'Image', '*.png *.jpg *.bmp')
        if fileName is '':
            return
        if self.img.size == 1:
            return
        # 调用OpenCV写入函数
        cv2.imwrite(fileName, self.img)

    def videoTask(self, *args, **kwargs):
       
        print("开始录像")

        success, frame = self.video_capture.read()
        while success and self.video_thread:
            self.video_count += 1
            print("vvvvvvvv:"+ str(self.video_count))
            current_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.video_writer.write(frame)
            self.img = QImage(
                current_image.data, current_image.shape[1], current_image.shape[0], QImage.Format_RGB888)
            self.label.setPixmap(QPixmap.fromImage(self.img))
            success, frame = self.video_capture.read()

    def startVideo(self):
        # 打开摄像头
        self.video_capture=cv2.VideoCapture(0)
        self.video_thread = True
        self.size = (self.width, self.height)
        self.fps = int(self.video_capture.get(cv2.CAP_PROP_FPS))
        self.fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', '2')
        # self.fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')

        # 创建视频写入对象
        self.video_writer = cv2.VideoWriter()
        self.video_writer.open(self.video_file, self.fourcc,
                               self.fps, self.size, True)
        self.video_count=0
        self.tVideo = threading.Thread(target=self.videoTask)
        self.tVideo.start()
        pass

        # self.label.show()
        # sys.sleep(100)

        # if self.img.size == 1:
        #     return
        # # 对图像做模糊处理，窗口设定为5*5
        # self.img = cv2.blur(self.img, (5, 5))
        # self.refreshShow()

    def stopVideo(self):
        threading.Thread(target=scokt_start).start()
        #scokt_start()

        
        # self.video_thread = False
        # time.sleep(0.2)
        # self.tVideo._stop()

        # self.video_writer.release()
        # self.video_capture.release()


    # def save_wave_file(self, filename, data):
    #     wf = wave.open(filename, 'wb')  # 二进制写入模式
    #     wf.setnchannels(self.channels)
    #     wf.setsampwidth(self.sampwidth)  # 两个字节16位
    #     wf.setframerate(self.framerate)  # 帧速率
    #     # 把数据加进去，就会存到硬盘上去wf.writeframes(b"".join(data))
    #     wf.writeframes(b"".join(data))
    #     wf.close()

    def video_play(self):
        
        cap = cv2.VideoCapture(self.video_file)
        ret, frame = cap.read()
    
        while(ret):
            current_image = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            #current_image  =frame
            # get a frame
            # show a frame
            self.img = QImage(
                current_image.data, current_image.shape[1], current_image.shape[0], QImage.Format_RGB888)
            self.label.setPixmap(QPixmap.fromImage(self.img))
            #sed_udp_data(frame)
            ret, frame = cap.read()
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break


    def audioStart(self):
        
        print("开始录音")
        self.pa = PyAudio()
        self.audioStream = self.pa.open(format=paInt16, channels=self.channels,
                                        rate=self.framerate, input=True,
                                        frames_per_buffer=self.CHUNK, output=True)
        self.wf = wave.open(self.audio_file, 'wb')  # 二进制写入模式
        self.wf.setnchannels(self.channels)
        self.wf.setsampwidth(self.sampwidth)  # 两个字节16位
        self.wf.setframerate(self.framerate)  # 帧速率
        self.audio_thread=True
        self.audio_count=0
        self.tAudio = threading.Thread(target=self.audioTask)
        self.tAudio.start()

    def audioTask(self):

        while self.audioStream.is_active() and self.audio_thread:
            self.audio_count += 1
            print( "aaaaaaaaa:"+ str(self.audio_count))
            # 采集数据
            string_audio_data = self.audioStream.read(self.CHUNK)
            # 播放数据
            self.audioStream.write(string_audio_data)
            # 写入文件
            #my_buf.append(string_audio_data)
            self.wf.writeframes(b"".join([string_audio_data]))
           # sed_udp_data(string_audio_data)
        
        #self.wf.writeframes(b"".join(my_buf))

    def audioStop(self):
        self.audio_thread= False
        time.sleep(0.2)
        self.audioStream.close()
        self.wf.close()
        #self.pa.terminate()
        self.tAudio._stop()
        print("录音完成")

    def audio_play(self):
        pa = PyAudio()
        wf = wave.open(self.audio_file, 'rb')
        stream = pa.open(format=paInt16, channels=self.channels,
                         rate=self.framerate, input=True,
                         output=True)

        while True:
            # string_audio_data = stream.read(self.NUM_SAMPLES)
            # audio_data = np.fromstring(string_audio_data, dtype=np.short)
            data = wf.readframes(self.NUM_SAMPLES)
            if data == b'':
                break
            stream.write(data)
        wf.close()
        stream.close()
        pa.terminate()

    def mediaPlay(self):
        self.video_capture = cv2.VideoCapture(0)
        #cv2.namedWindow("src")
        cuccess, frame = self.video_capture.read()
        while cuccess :
            cv2.imshow("src",frame)
            #cv2.imshow("sec",frame)
            
            # print(frame.shape)
            # print(type(frame))
            send_data(frame)
            cuccess, frame = self.video_capture.read()
            cv2.waitKey(1)

    
    def mediaMuxer(self):
        ff = ffmpegEx()
        ff.video_add_mp3(self.video_file,self.audio_file)

    def refreshShow(self):
        # 提取图像的通道和尺寸，用于将OpenCV下的image转换成Qimage
        # height, width, channel = self.img.shape
        # bytesPerline = 3 * width
        # self.qImg = QImage(self.img.data, width, height, bytesPerline, QImage.Format_RGB888).rgbSwapped()
        # 将QImage显示出来
        self.label.setPixmap(QPixmap.fromImage(self.img))
    def Start(self):
        self.startVideo()
        self.audioStart()
      

    def Stop(self):
        self.stopVideo()
        self.audioStop()
        self.mediaMuxer()
    
    def Play(self):
        #threading.Thread(target=self.video_play).start()
        #threading.Thread(target=self.audio_play).start()
        #self.video_play()
        #self.audio_play()
        threading.Thread(target= self.mediaPlay).start()

# 查看设备信息 
# ffmpeg -list_devices true -f dshow -i dummy

# 麦克风阵列 (Realtek High Definition Audio)
# PC Camera
# HP Wide Vision HD Camera

# 推流命令
# ffmpeg -f dshow  -i video="PC Camera"   -f flv rtmp://192.168.8.136:1935/mylive/6 -y
# 播放
# ffplay -i rtmp://192.168.8.136:1935/mylive/6

class ffmpegEx(object):
    def __init__(self):
        self.videoStr = "ffmpeg -f dshow  -i video=\"PC Camera\"  media/test.avi -f h264 udp://192.168.8.100:8990 -y"
        self.audioStr = "ffmpeg -f dshow  -i audio=\"麦克风阵列 (Realtek High Definition Audio)\" -acodec libmp3lame \
            media/test.mp3 -f mp3 udp://192.168.8.100:8989 -y"
        self.testStr = "ffmpeg -h"
        self.testList = ["echo".encode("utf-8"), "hello".encode("utf-8")]

    def start(self):
        pass
    

    def video_add_mp3(self,file_name, mp3_file):
        """
        视频添加音频
        :param file_name: 传入视频文件的路径
        :param mp3_file: 传入音频文件的路径
        :return:
        """
        outfile_name =  'media/media-out.mp4'
        sp.call('ffmpeg -i ' + file_name
                        + ' -i ' + mp3_file + ' -strict -2 -f mp4 -y '
                        + outfile_name, shell=True)



    def videoOut(self, *args, **kwargs):
        print("video out start")
        # if self.ssv.stdout.readable():
        #     print(self.ssv.stdout.readlines())
        #     pass

    def videoPush(self):
        fo = open("out.txt")
        self.ssv = sp.Popen(self.videoStr, stdout=sp.PIPE,
                            stdin=sp.PIPE, shell=True)

        # self.tv=threading.Thread(target= self.videoOut,args=1)
        # self.tv.start()
        # print(self.ss.stdout.read())

    def auidoPush(self):
        self.ssa = sp.Popen(self.audioStr, stdout=sp.PIPE,
                            stdin=sp.PIPE, shell=True)
        pass

    def exit(self):
        print("ss terminate")
        self.ssa.stdin.write("q".encode("utf-8"))
        self.ssa.stdin.flush()
        self.ssv.stdin.write("q".encode("utf-8"))
        self.ssv.stdin.flush()
        # sp.run("taskkill /f /im ffmpeg.exe",shell=False)

        self.ssa.terminate()
        self.ssv.terminate()

    def log(self, *args):
        print(args)



    
if __name__ == "__main__":

    # ff = ffmpegEx()
    # ff.start()
    # ff.videoPush()
    # ff.auidoPush()

    a = QApplication(sys.argv)
    w = window()
    w.show()
   
    # ff.exit()
    sys.exit(a.exec_())
