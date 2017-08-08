#!/usr/bin/env python
# -*- coding: utf-8 -*-


'''
Edit by Dong po Zhang

  张栋珀  ＜（￣︶￣）＞     

 （￣▽￣）～■□～（￣▽￣） 干杯~

'''

import sys
import thread
import socket
import time
from time import sleep
import serial
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu

#Set Modbus Port,ttyUSB0(For USB) or ttyAMA0(for UART)
PORT_mod = '/dev/ttyUSB0' #For USB
#PORT_mod = '/dev/ttyAMA0' #For UART
#Set TCP
HOST = '0.0.0.0'
PORT = 1234 

meter_1_list = range(26) # If other meter is not compatible meter_1, Set some list to map meter_1_list!


meter_name = ['A相电压','B相电压','C相电压','AB线电压','BC线电压','AC线电压','A相电流','B相电流','C相电流','A相有功功率','B相有功功率','C相有功功率','总有功功率','A相无功功率','B相无功功率','C相无功功率','总无功功率','A相视在功率','B相视在功率','C相视在功率','总视在功率','A相功率因数','B相功率因数','C相功率因数','总功率因数','频率']

def reset():
    s.close()
    sys.exit(1)

#Modbus part:

def Read(MeterID=1,StartID=7,count=26):
    #logger = modbus_tk.utils.create_logger("console")
    print '时间:',time.strftime('%Y-%m-%d %X',time.localtime()),u'读取电表{}'.format(str(MeterID).zfill(2))    
    try:
        #Connect to the slave
        master = modbus_rtu.RtuMaster(
            serial.Serial(port=PORT_mod, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0)
        )
        master.set_timeout(2.0)
        master.set_verbose(True) 
        #logger.info("connected")
        
        #Get result
        result_list = list(master.execute(MeterID, cst.READ_HOLDING_REGISTERS, StartID, count))
        #Get time
        now_time = time.strftime('%Y-%m-%d %X', time.localtime())
        #print result_list
        #logger.info(result_list)
        print '电表编号:',str(MeterID).zfill(2)
        result_change = list()
        for i in range(26):
            #Data processing:
            if i < 6 :
                res = str(float(result_list[i])/10) + 'V'
            if 6 <= i < 9:
                res = str(float(result_list[i])/1000) + 'A'
            if 9 <= i < 13:
                res = str(int(result_list[i])) + 'W'
            if 13 <= i  < 17:
                res = str(int(result_list[i])) + 'Var'
            if 17 <= i < 21:
                res = str(int(result_list[i])) + 'VA'
            if 21 <= i < 25:
                res = str(float(result_list[i])/1000)
            if i == 25:
                res = str(float(result_list[i])/100) + 'Hz'
            result_change.append(res)
        for i in range(26):
            print meter_name[i],':',result_change[i]
        print ''
        #For Tcp trans:
        result_tcp = 'ID:{},{},'.format(str(MeterID).zfill(2),time.strftime('%Y-%m-%d %X',time.localtime())) # add ID and Time
        for i in result_change:
            result_tcp = result_tcp + i + ','
        return result_tcp
            
    except :
        print '################################################\n','读取编号为{}的电表失败,请检查电表{}是否正常运行！\n'.format(str(MeterID).zfill(2),str(MeterID).zfill(2)),'################################################\n'
        return 'TimeOut,ID:{},'.format(MeterID)
        #logger.error("%s- Code=%d", exc, exc.get_exception_code())
        
#Socket server part:
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print 'Socket created'
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

#Bind socket to local host and port
try:
    s.bind((HOST, PORT))
except socket.error , msg:
    print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print '网络端口绑定成功...'

#Start listening on socket
s.listen(1)
print '网络端口正在侦听...'

def clientthread(conn):
    #Sending message to connected client
    conn.send('Connection#') 

    #infinite loop so that function do not terminate and thread do not end.
    while True:

        #Receiving from client
        data = conn.recv(1024)
        data_list = data.split(',')
        if data_list[0] == 'check' and len(data_list) > 1:
            del data_list[0]
            for i in range(len(data_list)):
                reply = Read(MeterID = int(data_list[i]))
                conn.sendall(reply + '#')
        else:
            pass
        if not data:
            break

        #conn.sendall(reply + '#')

    #came out of loop
    conn.close()

#now keep talking with the client 
if __name__ == "__main__":
    while True:
        try:
            #wait to accept a connection - blocking call
            conn, addr = s.accept()
            print '与上位机' + addr[0] + ':' + str(addr[1]) + ' 连接成功...'
            #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
            thread.start_new_thread(clientthread ,(conn,))
        except KeyboardInterrupt:
            reset()
    s.close()
    #Read()
