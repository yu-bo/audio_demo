import json
import pickle
import threading
import time
from socket import *
import func_timeout
from queue import Queue
import numpy as np

import cv2

# udp服务端 -----------------------------------------------


addr = ("", 29901)
udp_erver = socket(AF_INET, SOCK_DGRAM)
#udp_erver.bind(addr)  # 开始监听
haad = []  # 存数据
lack_list_data = []  # 存回发的缺少数据
header_datas = None  # 拼装成功的数据
frame_datas = []
frame_arr= np.array([],dtype=np.uint8)

    # header = {
    #     "data_shape":frame.shape,
    #     "data_type":"video_head"
    #     "data_len":len(split_arr)
    # }

    # data = {
    #     "data_index": i,
    #     "data_type": "video_data",
    #     "data_arr": split_arr[i]
    # }
def scokt_start():
    frame_lenght =0 
    video_capture=cv2.VideoCapture(0)
    cv2.namedWindow("cap") 
    count=10000
    frames=[]
    video_writer =cv2.VideoWriter()
    video_writer.open("media/test11.mp4", cv2.VideoWriter_fourcc('m', 'p', '4', '2'),5,(640,480),True)

    while count>0:
        count -=1
       
        bufsize = 100 * 1024 * 1024
        datae, addr = udp_erver.recvfrom(bufsize)
        try:
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
                    #print("数据接受完成")
                    frame = np.array(frame_arr).reshape(
                        (header_datas.get("data_shape")[0], header_datas.get("data_shape")[1],-1))
                    #frames.append(frame)
                    video_writer.write(frame)

        except Exception as error:
            print(error)
           
            continue
    
    video_writer.release()
    print("完成")


def screen_datas(addr):
    addr_datas = []
    for i in range(udp_datas.qsize()):
        data = udp_datas.get()
        if data[0] == addr:
            addr_datas.append(data)
        else:
            udp_datas.put(data)
    datas = [i[1] for i in addr_datas]
    return datas


def handle_request(data, addr):
    try:
        pack_len = data['pack_len']
        datas = screen_datas(addr)
        if len(datas) == pack_len:
        	# 开始拼装
            full_data = data_paste(datas)
        else:
        	# 数据丢失，查找丢失部分，要求客服端重发
            tj = find_incomplete_data(datas, pack_len)
            addr_time = str(int(time.time())) + '-' + \
                            addr[0] + '-' + str(addr[1])
            udpServer.sendto(pickle.dumps(
                {'lack': tj, 'times': addr_time}), addr)
            # 等待1秒后开始组装，就不用双发通信交流确认，
            # 或是改双方通信交流确认，就不必等待， （就需要更好的完整并发分布架构来实现，不然再多个ip进来，程序数据容易停歇，
            time.sleep(1)
            # 开始组装
    except Exception as ex:
        print(ex)


# udp  客服端 --------------------------------------


serverAddr = ('127.0.0.1', 29901)  # 元祖形式
upd_tasks = []
udpClient = socket(AF_INET, SOCK_DGRAM)  # 创建客户端
tg = []  # 缓存数据


def sed_udp_data(data):
    while True:
        split_datas = data_incision(json.dumps(data))
        for i in split_datas :
            udpClient.sendto(i,serverAddr)
            time.sleep(0.05)
        udpClient.sendto(pickle.dumps({'pack_len': len(split_datas)}),serverAddr)
        copy_split_datas = copy.deepcopy(split_datas)
        lack_1 = threading.Thread(target=lack_thread_, args=(udpClient, copy_split_datas,))
        lack_1.start()


def send_data(frame):
    
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

    for data in data_to_send:
        udpClient.sendto(data,serverAddr)
        time.sleep(0.01)
    
    # for i in split_datas :
    #     udpClient.sendto(arr,serverAddr)
       # time.sleep(0.05)
    #udpClient.sendto(pickle.dumps({'pack_len': len(split_datas)}),serverAddr)

def arr_split(arr,size):
    s=[]
    for i in range(0,int(len(arr))+1,size):
        c=arr[i:i+size]
        s.append(c)
    return s




def lack_thread_(udp_client, copy_split_datas):
	""" 数据丢失补发"""
	tg.append(copy_split_datas)  # 临时存储
	bufsize = 20 * 1024 * 1024
	try:
	    datae, addr = get_data(udp_client, bufsize)
	except:
	    print('------等待超时，数据成功发送')
	    return
	else:
	    data = pickle.loads(datae)
	    t = get_incomplete_data(copy_split_datas, data['lack'])
	    for i in t:
	        udp_client.sendto(pickle.dumps({'s_lack': i, 'times': data['times']}), addr)  # 发送数据
	        time.sleep(0.05)
	    print('发送缺少数据成功')
	finally:
	    tg.remove(copy_split_datas)

@func_timeout.func_set_timeout(2)
def get_data(udpClient, bufsize):
    data, addr = udpClient.recvfrom(bufsize)
    return data, addr



# -------------数据拆分------

def data_incision(data):
    # byte_ = random.choice([300, 900, 2060, 3200, 1056])
    byte_ = 4000
    residue_list = []

    def arithmetic():
        a = round(len(data) / byte_, 2)
        nub = str(a).split('.')
        if int(nub[1]) > 0:
            return int(nub[0]) + 1
        return int(nub[0])

    nubers = arithmetic()
    a = 0
    for i in range(0, nubers):
        try:
            residue = data[a:a + byte_:]
            residue = residue.encode('utf-8')
        except:
            print('数据切割失败', len(data), type(data))
            return
        residue_list.append(B'udp%d|\n\t' % (i) + residue)
        a += byte_
    return residue_list

# ------------数据拼接------------------


def data_extract(data):
    figure = data.decode('utf-8')
    figure = figure.split('|\n\t')[0].split('p')[1]
    return int(figure)


# 冒泡排序
def data_sort(list):
    """
    数据出装
    :param list:组装数据为list
    :return:
    """
    l = len(list)
    for i in range(l - 1, 0, -1):
        for j in range(i):
            a = data_extract(list[j])
            b = data_extract(list[j + 1])
            if a > b:
                list[j], list[j + 1] = list[j + 1], list[j]
    return list


def data_paste(data):
    """数据组装"""
    data = data_sort(data)
    b = ''
    for i in range(len(data)):
        figure = data[i].decode('utf-8')
        figure = figure.split('\n\t')[1]
        b = b + figure
    return b


# ----------------------数据缺少补起--------
def find_incomplete_data(data, number):
    """
    获取缺少的数据号
    :param data:
    :param number:
    :return:
    """
    j = list(range(0, number))
    t = [data_extract(i) for i in data]
    lack_ = [e for e in j if e not in t]
    return lack_


def get_incomplete_data(data, number):
    """
    获取需要的某个数据
    :param data:
    :param number:
    :return:
    """
    t = []
    for e in number:
        for i in data:
            a = data_extract(i)
            if e == a:
                t.append({'nuber': e, 'dada': i})
    return t
