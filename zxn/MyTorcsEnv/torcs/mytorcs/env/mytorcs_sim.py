import socket
import random
from struct import *
import traceback
import collections
import numpy as np
import time


class MyTorcsController():
    def __init__(self, time_step=0.05, port=None):
        self.port = port
        self.time_step = time_step
        self.loaded = False
        self.game_over = False
        self.time = 0
        self.stuck = 0
        #for the first obs after reset
        self.first_receive_data = None

        #start
        self.where_I_am_last_check = 0

        self.s = socket.socket()
        self.s.bind(port)
        self.s.listen()
    
    def calc(self, pos_info, time, stuck):
        tmp = 23
        width = pos_info[25] + pos_info[26]
        #tmp_l = pos_info[26]
        l = pos_info[0:19] + pos_info[23:25]  #sensor, angle, tomid
        l = list(l)
        l = l + [pos_info[tmp + 6], pos_info[tmp + 7], pos_info[tmp + 8], pos_info[50]] #speedX,Y,Z,rpm,23+4+4 = 31
        #r = l[21]*np.cos(l[19]) - np.abs(l[21]*np.sin(l[19])) - l[21]*np.abs(l[20])
        # print("cos", np.cos(l[19]))
        # print("l[21]", l[21])

        # print('1:',l[21]*(np.cos(l[19])-0.9))
        # print('2:',abs(l[20]/width)*np.exp(abs(l[19])))

        # r = l[21]*(np.cos(l[19])-0.9) - np.exp(abs(l[20]/width*20*l[19]))
        
        # r = - np.exp(abs(l[20]/width*5))
        # print(pos_info[-3])

        # if(pos_info[-1])
        # print(l[21])

        # r = l[21]*(np.cos(l[19])-0.92)*3 - 2  + (2 - np.exp(abs(l[20]/width*5)))
        r = (2 - np.exp(abs(l[20]/width*5)))

        
        #more distance
        if(pos_info[-3] > self.where_I_am_last_check):
            if(self.where_I_am_last_check != -1):
                #if you donnot move fast enough, you get negative reward
                r += (pos_info[-3] - self.where_I_am_last_check - 0.5)*2
                # print("h",pos_info[-3] - self.where_I_am_last_check)
        self.where_I_am_last_check = pos_info[-3] 

        # r = l[21]*np.cos(l[19])/10 - abs(l[21]*np.sin(l[19]))/10 - np.clip(abs(l[20])-0.4, 0, 1)

        for i in range(19):
            l[i] = l[i]/200

        l[19] = l[19]/3.1416   #angle
        l[20] = l[20]/width   #tomiddle

        for i in range(21, 24):
            l[i] = l[i] * 3.6/300

        l[24] = l[24]/10000

        # if (time % 20 == 0):
        #     for i in range(0, 24):
        #         print(l[i], end = ' ')
        #     print(l[24])
        ##l = pos_info[0:tmp]
        '''for i in range(4):
            if pos_info[tmp + 4*i] == 1:
                l = l + (1.0, 0.0, 0.0)
            if pos_info[tmp + 4*i] == 2:
                l = l + (0.0, 1.0, 0.0)
            if pos_info[tmp + 4*i] == 3:
                l = l + (0.0, 0.0, 1.0)
            l = l + pos_info[tmp + 4*i + 1: tmp + 4*i + 4]
        l = l + pos_info[25] + pos_info[26]
        l = list(l)
        #normal
        #angle and to start
        l[0] = l[0]/3.1415926
        #disttomid/left/right
        l[1] = l[1]/width
        l[2] = l[2]/width
        l[3] = l[3]/width
        #fuel and weight
        l[4] = l[4]/100.0
        l[5] = l[5]/1500.0
        #speed
        l[6] = l[6]/300.0
        l[7] = l[7]/300.0
        l[8] = l[8]/300.0
        #kfiction and length
        l[13] = l[13]/10
        l[14] = l[14]/600
        l[13 + 6] = l[13 + 6]/10
        l[14 + 6] = l[14 + 6]/1000
        l[13 + 6*2] = l[13 + 6*2]/10
        l[14 + 6*2] = l[14 + 6*2]/1000
        l[13 + 6*3] = l[13 + 6*3]/10
        l[14 + 6*3] = l[14 + 6*3]/1000

        print('state------>%.3f %.3f %.3f %.3f %.3f %.3f %.3f' %(np.cos(l[0]*3.1415926), np.sin(l[0]*3.1415926), l[14], l[15]*1000, l[16], l[17], l[20]*1000))
        r = l[6]*np.cos(l[0]*3.1415926)*300 - np.abs(l[6]*np.sin(l[0]*3.1415926)*300)
        '''
        # print("l",l[21])
        if(abs(pos_info[-3]-self.where_I_am_last_check) < 0.001 and l[21] <= 0.001):
            if(l[20] < -1 + 0.4):
                r = -10
                stuck = 1
            if(l[20] > 1 - 0.4):
                r = -10
                stuck = 1
        
        # if l[20] < -1 + 0.4:
        #     r -= 2
        # if l[20] > 1 - 0.4:
        #     r -= 2 

        #if time > TIMELIMIT:
        #    r = -10
        #    stuck = 1
        if np.cos(l[19]*3.1416) < -0.1:
            r = -10
            stuck = 1 

        # if np.cos(l[19]*3.1416) < 0.5 and l[21] < 0.2:
            # r = -100
            # stuck = 1 
        #if time > 300:
        #    if l[6] < 5.0/300:
        #        r = -1
        #        stuck = 1
        l = tuple(l)
        # print('r', r)
        return r, l, stuck

    def wait_until_loaded(self):
        while not self.loaded:
            # print("waiting for sim to start..")
            conn, addr = self.s.accept()
            recv_data = conn.recv(1024)
            if recv_data:
                #init setting:
                self.loaded = True
                self.first_receive_data = recv_data
                self.conn = conn
                self.addr = addr

    def reset(self):
        if self.game_over:
            # print("Game over, reseting")
            self.game_over = False
        self.where_I_am_last_check = -1
        self.time = 0
        self.stuck = 0
        self.wait_until_loaded()

    def take_action(self, action):
        #waiting to be done: time
        # print("want to excute", action)
        # print(type(action))    
        self.conn.send(pack('4f', action[0], action[1], action[2], action[3]))
        
    def observe(self, action_list=[0.0,0.0,0.0,0.0], reset=False):
        recv_data = None
        
        if(reset):
            recv_data = self.first_receive_data
        else:
            recv_data = self.conn.recv(1024)

        if not recv_data:
            self.loaded = False
            self.game_over = True
            return np.ones(25,dtype=np.float32),-1,True,"Gameover"
        
        try:
            pos_info = unpack('51f', recv_data)
            # if(pos_info != self.last):
                # self.last = pos_info
                # print("pos", pos_info)
        except:
            #shutdown
            self.loaded = False
            self.game_over = True
            return np.zeros(25,dtype=np.float32),-1,True,"Gameover"
        
        r, info, self.stuck = self.calc(pos_info, self.time, self.stuck)

        #more speed
        # r -= 20*(action_list[1] - action_list[2])
        # print("r", r)

        if self.stuck:
            pos_info = -1
            # r = -500
            # print("stuck", self.stuck)
        # print("info!!!!!!!!!!", len(list(info)))
        # print(np.array(list(info)).shape)

        return np.array(list(info)), r, self.game_over, pos_info
    
    def is_game_over(self):
        return self.game_over

















