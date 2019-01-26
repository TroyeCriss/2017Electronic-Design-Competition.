#Camera control - By:Simon  - V1.0 1.17 2019  - V1.1 1.20 2019 -V1.2 1.25 2019 添加模式转换
'''
2017国赛飞行器摄像头代码
实现功能：
1.当启动时，仅有初始场地上的圆时，锁定场地上的圆。
2.当检测到小车的圆时，锁定小车。
'''
import sensor,image,time,struct,math
from pyb import UART,LED,Timer
threshold_black=[(0,100)]
#锁定圆
def lock_place_circle(circles):
    global front_circle,current_circle
    current_circle.x=500
    current_circle.y=500
    for c in circles:
        if abs(c.x()-front_circle.x)**2+abs(c.y()-front_circle.y)**2<abs(current_circle.x-front_circle.x)**2+abs(current_circle.y-front_circle.y)**2:
            current_circle.x=c.x()
            current_circle.y=c.y()
            current_circle.r=c.r()
    front_circle.x=current_circle.x
    front_circle.y=current_circle.y
    front_circle.r=current_circle.r
#锁定小车
def lock_car(circles):
    global front_circle,current_circle,g_find_car,g_find_place_circle,g_find_flag
    if g_find_car==0:
        #print("寻找小车")
        i=0
        for c in circles:
            i+=1
            g_find_place_circle=1
            current_circle.x=c.x()
            current_circle.y=c.y()
            current_circle.r=c.r()
        if i == 2:
            offset=0
            for c in circles:
                if abs(front_circle.y-c.y())>offset:
                    offset=abs(front_circle.y-c.y())
                    g_find_car=1
                    current_circle.x=c.x()
                    current_circle.y=c.y()
                    current_circle.r=c.r()
        elif abs(front_circle.y-current_circle.y)>20 and g_find_flag:
            g_find_car=1
        if(g_find_place_circle):
            g_find_flag=1

        front_circle.x=current_circle.x
        front_circle.y=current_circle.y
        front_circle.r=current_circle.r
    elif g_find_car==1:
        #print("锁定小车")
        current_circle.x=500
        current_circle.y=500
        for c in circles:
            if abs(c.x()-front_circle.x)**2+abs(c.y()-front_circle.y)**2<abs(current_circle.x-front_circle.x)**2+abs(current_circle.y-front_circle.y)**2:
                current_circle.x=c.x()
                current_circle.y=c.y()
                current_circle.r=c.r()
        front_circle.x=current_circle.x
        front_circle.y=current_circle.y
        front_circle.r=current_circle.r
#打包数据
def pack_data():
    global current_circle,g_mode,g_find_car
    #锁定场地圆
    if g_mode==0:
        x_high=(current_circle.x&0xff00)>>8
        x_low=current_circle.x&0xff
        y_high=(current_circle.y&0xff00)>>8
        y_low=current_circle.y&0xff
        SUM=(0xBB+0x60+0x06+0xBF+0x04+x_high+x_low+y_high+y_low)&0xff
        temp=struct.pack("<BBBBBBBBBB",
                            0xBB,       #帧头
                            0x06,       #源地址
                            0x60,       #目标地址
                            0xBF,       #功能号
                            0x04,       #数据长度
                            x_high,
                            x_low,
                            y_high,
                            y_low,
                            SUM)        #校验和
        uart.write(temp)
    #寻找小车，控制场地圆的x坐标不变，控制y坐标，使飞机向前飞
    elif g_mode==1 and g_find_car==0:
        x_high=(current_circle.x&0xff00)>>8
        x_low=current_circle.x&0xff
        y_high=0
        y_low=25
        SUM=(0xBB+0x60+0x06+0xBF+0x04+x_high+x_low+y_high+y_low)&0xff
        temp=struct.pack("<BBBBBBBBBB",
                            0xBB,       #帧头
                            0x06,       #源地址
                            0x60,       #目标地址
                            0xBF,       #功能号
                            0x04,       #数据长度
                            x_high,
                            x_low,
                            y_high,
                            y_low,
                            SUM)        #校验和
        uart.write(temp)
    #锁定小车
    elif g_mode==1 and g_find_car==1:
        x_high=(current_circle.x&0xff00)>>8
        x_low=current_circle.x&0xff
        y_high=(current_circle.y&0xff00)>>8
        y_low=current_circle.y&0xff
        SUM=(0xBB+0x60+0x06+0xBF+0x04+x_high+x_low+y_high+y_low)&0xff
        temp=struct.pack("<BBBBBBBBBB",
                            0xBB,       #帧头
                            0x06,       #源地址
                            0x60,       #目标地址
                            0xBF,       #功能号
                            0x04,       #数据长度
                            x_high,
                            x_low,
                            y_high,
                            y_low,
                            SUM)        #校验和
        uart.write(temp)
#确认收到数据
def confirm_data():
    SUM=(0xBB+0x60+0x06+0xBC+0x01+0x01)&0xff
    temp=struct.pack("<BBBBBBB",
                        0xBB,
                        0x06,
                        0x60,
                        0xBC,
                        0x01,
                        0x01,
                        SUM)
    uart.write(temp)
#接受数据
def receive_data():
    global g_mode,g_find_car,g_find_place_circle,g_find_flag
    if uart.any():
        a=uart.read()
        '''检验数据帧头'''
        if a[0]==0xBB and a[1]==0x60 and a[2]==0x06:
            mode=a[5]
            SUM=a[0]+a[1]+a[2]+a[3]+a[4]+a[5]
            if SUM==a[6]:
                #confirm_data()
                if mode==1:
                    g_mode=0
                elif mode==2:
                    g_mode=1
                    g_find_car=0
                    g_find_place_circle=0
                    g_find_flag=0

#时钟回调
def over_time(timer):
    global flag
    flag=True
#圆类
class CIRCLE(object):
    x=0
    y=0
    r=0

g_mode=0        #0模式时，为锁定场地上的圆  1模式时，寻找小车，并锁定
front_circle=CIRCLE()
current_circle=CIRCLE()
flag=True
g_find_car=0    #寻找小车，0时未找到，1时找到
g_find_place_circle=0
g_find_flag=0
#摄像头传感器设置
sensor.reset()
sensor.set_pixformat(sensor.GRAYSCALE)
sensor.set_framesize(sensor.QQQVGA)     #QQQVG:80*60
sensor.skip_frames(time=2000)           #略过前两秒的数据
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)
#串口设置
uart=UART(3,115200)
uart.init(115200,bits=8,parity=None,stop=1)
#时钟设置
timer=Timer(4,freq=20)
timer.callback(over_time)
led2=LED(2)
led2.on()
led3=LED(3)
led3.off()
clock=time.clock()

while True:
    clock.tick()
    #修正镜头畸变
    img=sensor.snapshot().lens_corr(1.8)
    #img.binary(threshold_black)
    c=img.find_circles(threshold=4000,x_margin=10,y_margin=10,r_margin=10)
    find_circle=False
    if c:
        find_circle=True
        if g_mode==0:
            led2.on()
            led3.off()
            #print("锁定场地圆")
            lock_place_circle(c)
            #pack_data()
            #img.draw_circle(current_circle.x,current_circle.y,current_circle.r,color=(255,0,0))
        elif g_mode==1:
            led2.off()
            led3.on()
            lock_car(c)
            #img.draw_circle(current_circle.x,current_circle.y,current_circle.r,color=(255,0,0))
    if flag:
        flag=False
        receive_data()
        print(g_mode)
        if find_circle:
            find_circle=False
            pack_data()
    #print(flag)
    #print(clock.fps())
