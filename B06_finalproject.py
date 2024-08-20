import tkinter
from PIL import Image, ImageTk
import time
import board
import adafruit_dht
# import project.py
import RPi.GPIO as GPIO
import spidev
import struct
from enum import Enum
import speech_recognition as sr
import apa102
from gtts import gTTS
import os
# import finger.py
import cv2
from collections import Counter
from module import findnameoflandmark,findpostion,speak
import math


#---------------------溫溼度
# Initialize the DHT11 with GPIO pin 4:
dhtDevice = adafruit_dht.DHT11 (board.D4)
# Print the values ​​(temperature and humidity) to the serial port
temperature_c = dhtDevice.temperature
humidity = dhtDevice.humidity
#-------------------辨別使用者
cap = cv2.VideoCapture(0)
tip=[8,12,16,20]
tipname=[8,12,16,20]
fingers=[] 
finger=[]



#---------------------語音
LED_NUM = 3

leds = apa102.APA102(num_led=3)
colors = [[255,0,0],[0,255,0],[0,0,255]] # LED0: R, LED1: G, LED2: B
#obtain audio from the microphone
r=sr.Recognizer()

#---------------------三軸
# LED_PIN = 12
# GPIO.setmode(GPIO.BOARD)
# GPIO.setup(LED_PIN, GPIO.OUT)
# pwm = GPIO.PWM(LED_PIN, 100)
# pwm.start(0)

spi = spidev.SpiDev()
spi.open(0, 0)
spi.mode = 0b11
spi.max_speed_hz = 2000000

def writeByte(reg, val):
    spi.xfer2([reg, val])

def writeRegBytes(reg, vals):
    packet = [0] * (len(vals) + 1)
    packet[0] = reg | 0x40
    packet[1:(len(vals)+1)] = vals
    spi.xfer2(packet)

def readByte(reg):
    packet = [0] * 2
    packet[0] = reg | 0x80
    reply = spi.xfer2(packet)
    return reply[1]

deviceID = readByte(0x00)
print("ID: %x" % deviceID)
writeByte(0x2D, 0x00)
time.sleep(0.1)
writeByte(0x2D, 0x08)
writeByte(0x31, 0x08)
time.sleep(0.5)
#---------------------------------------gui介面
def define_layout(obj, cols=1, rows=1):
    def method(trg, col, row):
        for c in range(cols):    
            trg.columnconfigure(c, weight=1)
        for r in range(rows):
            trg.rowconfigure(r, weight=1)

    if type(obj)==list:        
        [ method(trg, cols, rows) for trg in obj ]
    else:
        trg = obj
        method(trg, cols, rows)

def create_image(name,c,r):
    img=Image.open(name)
    imgTk=ImageTk.PhotoImage(img.resize((img_size//2, img_size//2)))
    clothes_label=tkinter.Label(div3, image=imgTk)
    clothes_label['height'] = img_size/2
    clothes_label['width'] = img_size/2
    clothes_label.image=imgTk
    clothes_label.grid(column=c, row=r, sticky=align_mode)



try:
    while True:
        accel = {'x' : 0, 'y' : 0, 'z': 0}
        data0 = readByte(0x32)
        data1 = readByte(0x33)
        xAccl = struct.unpack('<h', bytes([data0, data1]))[0]
        accel['x'] = xAccl / 256

        data0 = readByte(0x34)
        data1 = readByte(0x35)
        yAccl = struct.unpack('<h', bytes([data0, data1]))[0]
        accel['y'] = yAccl / 256

        data0 = readByte(0x36)
        data1 = readByte(0x37)
        zAccl = struct.unpack('<h', bytes([data0, data1]))[0]
        accel['z'] = zAccl / 256

        # print ("Ax Ay Az: %.3f %.3f %.3f" % (accel['x'], accel['y'], accel['z']))
        time.sleep(0.1)      

        if(accel['y'] > 0.5):
            print("門已開啟")
            flag = 0
            while True:
                whichFinger=[0,0,0,0]
                ret, frame = cap.read()
                # Determines the frame size, 640 x 480 offers a nice balance between speed and accurate identification
                frame1 = cv2.resize(frame, (640, 480))
                # Below is used to determine location of the joints of the fingers
                a = findpostion(frame1)
                b = findnameoflandmark(frame1)
                # Below is a series of If statement that will determine if a finger is up or down and
                # then will print the details to the console
                if len(b and a) != 0:
                    finger = []
                    if a[0][1:] < a[4][1:]:
                        finger.append(1)
                        # print (b[4])
                    else:
                        finger.append(0)
                        fingers = []
                        for id in range(0, 4):
                            if a[tip[id]][2:] < a[tip[id]-2][2:]:
                                # print(b[tipname[id]])
                                whichFinger[id] = 1
                                fingers.append(1)
                            else:
                                fingers.append(0)

                cv2.imshow("Frame", frame1)
                key = cv2.waitKey(1) & 0xFF

                if whichFinger[0] == 1 and whichFinger[1] == 0:
                    print("使用者1號")
                    flag = 1
                    cap.release()
                    break
                elif whichFinger[0] == 1 and whichFinger[1] == 1 and whichFinger[2] == 0:
                    print("使用者2號")
                    flag = 2
                    cap.release()
                    break
                # else:
                #     print("使用者3號")

            if flag == 1:
                #-----------------------------------語音問候
                hour = int(time.strftime('%H', time.localtime()))
                if(hour >= 11 and hour <= 16):
                    print('午安1號')
                    tts = gTTS(text='午安一號', lang='zh-TW')
                    tts.save('weather_tw.mp3')
                    os.system('omxplayer -o local -p weather_tw.mp3 > /dev/null 2>&1')
                elif(hour >= 4 and hour <= 10):
                    print('早安1號')
                    tts = gTTS(text='早安一號', lang='zh-TW')
                    tts.save('weather_tw.mp3')
                    os.system('omxplayer -o local -p weather_tw.mp3 > /dev/null 2>&1')
                else:
                    print('晚安1號')
                    tts = gTTS(text='晚安一號', lang='zh-TW')
                    tts.save('weather_tw.mp3')
                    os.system('omxplayer -o local -p weather_tw.mp3 > /dev/null 2>&1')
            if flag == 2:        
                hour = int(time.strftime('%H', time.localtime()))
                if(hour >= 11 and hour <= 16):
                    print('午安2號')
                    tts = gTTS(text='午安二號', lang='zh-TW')
                    tts.save('weather_tw.mp3')
                    os.system('omxplayer -o local -p weather_tw.mp3 > /dev/null 2>&1')
                elif(hour >= 4 and hour <= 10):
                    print('早安2號')
                    tts = gTTS(text='早安二號', lang='zh-TW')
                    tts.save('weather_tw.mp3')
                    os.system('omxplayer -o local -p weather_tw.mp3 > /dev/null 2>&1')
                else:
                    print('晚安2號')
                    tts = gTTS(text='晚安二號', lang='zh-TW')
                    tts.save('weather_tw.mp3')
                    os.system('omxplayer -o local -p weather_tw.mp3 > /dev/null 2>&1')
            
            #-----------------------------------gui
            top = tkinter.Tk()
            top.title('Wardrobe assistant')
            align_mode='nswe'
            pad=5

            div_size=200
            img_size=div_size*2
            div1 = tkinter.Frame(top, width=div_size, height=div_size, bg='blue')
            div2 = tkinter.Frame(top, width=div_size, height=div_size, bg='white')
            div3 = tkinter.Frame(top, width=img_size, height=img_size, bg='orange')

            top.update()
            win_size = min( top.winfo_width(), top.winfo_height())
            #print(win_size)

            div1.grid(column=0, row=0,padx=pad, pady=pad, sticky=align_mode)
            div2.grid(column=0, row=1,padx=pad, pady=pad, sticky=align_mode)
            div3.grid(column=1, row=0, rowspan=2,padx=pad, pady=pad, sticky=align_mode)

            define_layout(top, cols=2,rows=2)
            define_layout([div1, div2, div3])
            define_layout(div1,rows=4)
            define_layout(div2, rows=3)
            define_layout(div3)

                
            text2_label=tkinter.Label(div2, text='提醒', bg='black', fg='white')
            text2_label.grid(column=0, row=0, sticky=align_mode)

            if temperature_c > 25:
                tts = gTTS(text='現在溫度偏熱', lang='zh-TW')
                tts.save('weather_tw.mp3')
                os.system('omxplayer -o local -p weather_tw.mp3 > /dev/null 2>&1')
                text1_label=tkinter.Label(div2, text='現在溫度偏熱，請記得補充水分')
                text1_label.grid(column=0, row=1, sticky=align_mode)

            elif temperature_c > 20 and temperature_c <= 25:
                tts = gTTS(text='現在溫度舒適', lang='zh-TW')
                tts.save('weather_tw.mp3')
                os.system('omxplayer -o local -p weather_tw.mp3 > /dev/null 2>&1')
                text1_label = tkinter.Label(div2, text='現在溫度舒適，請注意防曬')
                text1_label.grid(column=0, row=1, sticky=align_mode)

            elif temperature_c > 15 and temperature_c <= 20:
                tts = gTTS(text='現在溫度偏冷', lang='zh-TW')
                tts.save('weather_tw.mp3')
                os.system('omxplayer -o local -p weather_tw.mp3 > /dev/null 2>&1')
                text1_label=tkinter.Label(div2, text='現在溫度偏冷，請注意保暖')
                text1_label.grid(column=0, row=1, sticky=align_mode)

            elif temperature_c <= 15:
                tts = gTTS(text='現在溫度寒冷', lang='zh-TW')
                tts.save('weather2_tw.mp3')
                os.system('omxplayer -o local -p weather2_tw.mp3 > /dev/null 2>&1')
                text1_label=tkinter.Label(div2, text='現在溫度寒冷，請注意保暖')
                text1_label.grid(column=0, row=1, sticky=align_mode)
                

            if humidity > 70:
                text2_label=tkinter.Label(div2, text='今日濕度高，可能會降雨')
                text2_label.grid(column=0, row=2, sticky=align_mode)
            else:
                text2_label=tkinter.Label(div2, text='降雨率低，請安心出門')
                text2_label.grid(column=0, row=2, sticky=align_mode)

                

            date_label=tkinter.Label(div1, text=time.strftime('日期： %Y-%m-%d', time.localtime()))
            date_label.grid(column=0, row=0, sticky=align_mode)

            time_label=tkinter.Label(div1, text=time.strftime('時間： %H:%M', time.localtime()))
            time_label.grid(column=0, row=1, sticky=align_mode)

            temp_label = tkinter.Label(div1, text='現在溫度：{: .1f}'.format(temperature_c), fg='#263238')
            temp_label.grid(column=0, row=2, sticky=align_mode)

            h_label = tkinter.Label(div1, text='現在濕度：{}%'.format (humidity), fg='#263238')
            h_label.grid(column=0, row=3, sticky=align_mode)

            #---------------------------------------------------------------------user1
            if flag == 1:
                if temperature_c > 25:
                    create_image('9.jpg',0,0)
                    create_image('7.jpg',1,0)
                    create_image('10.jpg',0,1)
                    if humidity > 70:     
                        create_image('12.jpg',1,1)
                    if humidity < 70:
                        create_image('2.jpg',1,1)

                if temperature_c > 20 and temperature_c <= 25:
                    create_image('9.jpg',0,0)
                    create_image('6.jpg',1,0)
                    create_image('5.jpg',0,1)
                    if humidity > 70:             
                        create_image('12.jpg',1,1)
                    if humidity < 70:
                        create_image('2.jpg',1,1)

                if temperature_c > 15 and temperature_c <= 20:
                    if humidity > 70:
                        create_image('6.jpg',0,0)
                        create_image('3.jpg',1,0)
                        create_image('5.jpg',0,1)
                        create_image('12.jpg',1,1)
                    if humidity < 70:
                        create_image('11.jpg',0,0)
                        create_image('8.jpg',1,0)
                        create_image('5.jpg',0,1)
                        create_image('13.jpg',1,1)

                if temperature_c <= 15:
                    create_image('4.jpg',0,0)
                    create_image('11.jpg',1,0)
                    create_image('5.jpg',0,1)
                    if humidity > 70:
                        create_image('12.jpg',1,1)
                    if humidity < 70:
                        create_image('8.jpg',1,1)
            #--------------------------------------------------------------------------------------user2
            if flag == 2: 
                if humidity < 70:
                    if temperature_c > 25:
                        create_image('6.jpg',0,0)
                        create_image('5.jpg',1,0)
                        create_image('1.jpg',0,1)
                        create_image('2.jpg', 1, 1)
                    if temperature_c > 20 and temperature_c <= 25:
                        create_image('3.jpg',0,0)
                        create_image('7.jpg',1,0)
                        create_image('10.jpg',0,1)
                        create_image('2.jpg', 1, 1)
                    if  temperature_c > 15 and temperature_c <= 20 :
                        create_image('3.jpg',0,0)
                        create_image('4.jpg',1,0)
                        create_image('5.jpg',0,1)
                        create_image('1.jpg', 1, 1)
                    if temperature_c <= 15:
                        create_image('6.jpg',0,0)
                        create_image('10.jpg',1,0)
                        create_image('8.jpg',0,1)
                        create_image('13.jpg', 1, 1)
                else:
                    create_image('12.jpg',1,1)
                    if temperature_c > 25:
                        create_image('2.jpg',0,0)
                        create_image('11.jpg',1,0)
                        create_image('10.jpg',0,1)
                    if temperature_c > 20 and temperature_c <= 25:
                        create_image('9.jpg',0,0)
                        create_image('5.jpg',1,0)
                        create_image('1.jpg',0,1)
                    if  temperature_c > 15 and temperature_c <= 20 :
                        create_image('6.jpg',0,0)
                        create_image('5.jpg',1,0)
                        create_image('8.jpg',0,1)
                    if temperature_c <= 15:
                        create_image('9.jpg',0,0)
                        create_image('7.jpg',1,0)
                        create_image('8.jpg',0,1)
            #---------------------------------------------------------------------------------------------
            top.mainloop()
        
            cap.release()
            cv2.destroyAllWindows() 
            print("門已關閉")
        


except KeyboardInterrupt:
    print("Ctrl+C Break")
    spi.close()
    GPIO.cleanup()
