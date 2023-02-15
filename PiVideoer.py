#!/usr/bin/env python3
import time
import cv2
import numpy as np
import pygame
from pygame.locals import *
from PIL import Image
import os, subprocess, glob
import signal
import datetime
import shutil
import glob
import RPi.GPIO as GPIO
from gpiozero import CPUTemperature
from PIL import Image

# v1.1

# set screen size
scr_width  = 800
scr_height = 480

# use GPIO for optional FAN, LED, external camera trigger
use_gpio = 1

# led gpio (if use_gpio = 1)
led      = 12

# ext_camera trigger gpios (if use_gpio = 1)
s_focus  = 16
s_trig   = 20

# fan ctrl (if use_gpio = 1)
fan      = 21 

# save MP4 to SD / USB, 0 = SD Card, 1 = USB 
movtousb = 0

if use_gpio == 1:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(s_trig,GPIO.OUT)
    GPIO.setup(s_focus,GPIO.OUT)
    GPIO.output(s_trig, GPIO.LOW)
    GPIO.output(s_focus, GPIO.LOW)
    GPIO.setup(led,GPIO.OUT)
    GPIO.output(led, GPIO.LOW)
    GPIO.setup(fan, GPIO.OUT)
    pwm = GPIO.PWM(fan, 100)
    pwm.start(0)

# set default config parameters
v_crop        = 130     # size of vert detection window *
h_crop        = 90      # size of hor detection window *
threshold     = 20      # minm change in pixel luminance
threshold2    = 255     # maxm change in pixel luminance
cap_width     = 1920
cap_height    = 1080
fps           = 25      # set camera fps *
mode          = 1       # set camera mode ['off','normal','sport'] *
speed         = 80000   # mS x 1000 *
gain          = 0       # set gain *
brightness    = 0       # set camera brightness*
contrast      = 70      # set camera contrast *
Capture       = 0       # 0 = off, 1 = ON *
preview       = 0       # show detected changed pixels *
noframe       = 0       # set to 1 for no window frame
detection     = 10      # % of pixels detected *
det_high      = 100     # max pixels detected to trigger in %*
awb           = 1       # auto white balance, 1 = ON, 0 = OFF *
red           = 3.5     # red balance *
blue          = 1.5     # blue balance *
meter         = 0       # metering *
ev            = 0       # eV *
interval      = 0       # wait between capturing Pictures *
v_length      = 20000   # video length in mS *
vid_pic       = 0       # video = 0, Pictures = 1*
ES            = 0       # trigger external camera, 0 = OFF, 1 = SHORT, 2 = LONG *
denoise       = 0       # denoise level *
quality       = 75      # video quality
sharpness     = 14      # sharpness *
saturation    = 12      # saturation *
storage_limit = 90      # SD card in %, copy to USB if available
auto_save     = 1       # set to 1 to automatically copy to SD card
auto_time     = 10      # time after which auto save actioned
auto_limit    = 2       # No of Videos in RAM before auto save actioned
ram_limit     = 250     # MBytes, copy from RAM to SD card when reached
fan_time      = 10      # sampling time in seconds *
fan_low       = 50      # fan OFF below this, 25% to 100% pwm above this*
fan_high      = 70      # fan 100% pwm above this*
sd_hour       = 20      # Shutdown Hour, 1 - 23, 0 will NOT SHUTDOWN*
vformat       = 1       # 4 = 1920 X 1080, SEE VWIDTHS/VHEIGHTS
col_filter    = 3       # 3 = FULL, SEE COL_FILTERS
col_filterp   = 0
nr            = 0
pre_frames    = fps * 2
scientific    = 0
v3_f_mode     = 0
v3_focus      = 500
# * adjustable whilst running

# initialise
synced        = 0
show          = 0
reboot        = 0
stopped       = 0
record        = 0
timer         = 0
zoom          = 0
trace         = 0
timer10       = 0
config_file   = "Vid_config28.txt"
ram_snaps     = 0
a             = int(scr_width/2)
b             = int(scr_height/2)


modes    = ['off','normal','sport']
meters   = ['centre','spot','average']
awbs     = ['off','auto','incandescent','tungsten','fluorescent','indoor','daylight','cloudy']
denoises = ['off','cdn_off','cdn_fast','cdn_hq']
vwidths  = [640,720,1280,1296,1920,2592]
vheights = [480,540, 720, 972,1080,1944]
col_filters = ['RED','GREEN','BLUE','FULL']
noise_filters = ['OFF','LOW','HIGH']
v3_f_modes   = ['auto','manual','continuous']

# check Vid_configXX.txt exists, if not then write default values
if not os.path.exists(config_file):
    points = [h_crop,threshold,fps,mode,speed,gain,brightness,contrast,Capture,preview,awb,detection,int(red*10),int(blue*10),interval,v_crop,v_length,ev,meter,ES,a,b,sharpness,saturation,denoise,fan_low,fan_high,vid_pic,det_high,quality,fan_time,sd_hour,vformat,threshold2,col_filter,nr,pre_frames,auto_limit,ram_limit,v3_f_mode,v3_focus]
    with open(config_file, 'w') as f:
        for item in points:
            f.write("%s\n" % item)

# read config file
config = []
with open(config_file, "r") as file:
   line = file.readline()
   while line:
      config.append(line.strip())
      line = file.readline()
config = list(map(int,config))

h_crop      = config[0]
threshold   = config[1]
fps         = config[2]
mode        = config[3]
speed       = config[4]
gain        = config[5]
brightness  = config[6]
contrast    = config[7]
Capture     = config[8]
preview     = config[9]
awb         = config[10]
detection   = config[11]
red         = config[12]/10
blue        = config[13]/10
interval    = config[14]
v_crop      = config[15]
v_length    = config[16]
ev          = config[17]
meter       = config[18]
ES          = config[19]
a           = config[20]
b           = config[21]
sharpness   = config[22]
saturation  = config[23]
denoise     = config[24]
fan_low     = config[25]
fan_high    = config[26]
vid_pic     = config[27]
det_high    = config[28]
quality     = config[29]
fan_time    = config[30]
sd_hour     = config[31]
vformat     = config[32]
threshold2  = config[33]
col_filter  = config[34]
nr          = config[35]
pre_frames  = config[36]
auto_limit  = config[37]
ram_limit   = config[38]
v3_f_mode   = config[39]
v3_focus    = config[40]


if vid_pic == 0:
    cap_width  = vwidths[vformat]
    cap_height = vheights[vformat]
    #pre_frames = fps * 2 
else:
    cap_width  = 2592
    cap_height = 1944
    pre_frames = 2 

#set screen image width
bw = int(scr_width/8)
cwidth = scr_width - bw
cheight = scr_height

if vid_pic == 0:
   xheight = int(cwidth * 0.5625)
else:
   xheight = int(cwidth * 0.75)
if xheight > scr_height:
    xheight = scr_height
if a > cwidth - v_crop:
    a = int(cwidth/2)
if b > xheight - h_crop:
    b = int(xheight/2)

bh = int(scr_height/12)
font_size = int(min(bh, bw)/3)
a2 = int(a * (cap_width/cwidth))
b2 = int(b * (cap_height/xheight))
h_crop2  = int(h_crop * (cap_width/cwidth))
v_crop2  = int(v_crop * (cap_height/xheight))
start_up = time.monotonic()
col_timer = 0
pygame.init()

# Check for Pi Camera version
if os.path.exists('test.jpg'):
   os.rename('test.jpg', 'oldtest.jpg')
rpistr = "libcamera-jpeg -n -t 1000 -e jpg -o test.jpg "
os.system(rpistr)
rpistr = ""
time.sleep(1)
if os.path.exists('test.jpg'):
   imagefile = 'test.jpg'
   image = pygame.image.load(imagefile)
   igw = image.get_width()
   igh = image.get_height()
   if igw == 2592:
      Pi_Cam = 1
   elif igw == 3280:
      Pi_Cam = 2
   elif igw == 4608:
      Pi_Cam = 3
   elif igw == 4056:
      Pi_Cam = 4
   elif igw == 4656:
      Pi_Cam = 5
   elif igw == 9152 or igw == 4624:
      Pi_Cam = 6
else:
   Pi_Cam = 0
print(Pi_Cam)

# start Pi Camera subprocess 
def Camera_start(wx,hx,zoom,vid_pic):
    global Pi_Cam,v3_f_modes,v3_f_mode,scientific,used_storage,trace,p,red,blue,contrast,brightness,gain,speed,modes,mode,ev,ES,cap_width,cap_height,pre_frames,awbs,awb,meters,meter,sharpness,saturation,denoise,cwidth,xheight
    if trace == 1:
        print ("Step 1 START SUB PROC")
    # clear ram
    zpics = glob.glob('/run/shm/test*.jpg')
    for tt in range(0,len(zpics)):
        os.remove(zpics[tt])
    st = os.statvfs("/run/shm/")
    freeram = (st.f_bavail * st.f_frsize)/1100000
    ss = str(int(sfreeram)) + " - " + str(int(used_storage))
    text(0,10,3,1,1,ss,15,7)
    rpistr = "libcamera-vid -t 0 --segment 1 --codec mjpeg -q " + str(quality)
    rpistr += " -n -o /run/shm/test%06d.jpg --width " + str(wx) + " --height " + str(hx) + " --contrast " + str(contrast/100) + " --brightness " + str(brightness/100)
    if awb > 0:
        rpistr += " --awb " + awbs[awb]
    else:
        rpistr += " --awbgains " + str(red) + "," + str(blue)
    if mode == 0:
        rpistr +=" --shutter " + str(speed) + " --framerate " + str(1000000/speed)
    else:
        rpistr +=" --exposure " + str(modes[mode]) + " --framerate " + str(fps)
    rpistr += " --ev " + str(ev) +  " --gain " + str(gain)
    rpistr += " --metering "   + meters[meter]
    rpistr += " --saturation " + str(saturation/10)
    rpistr += " --sharpness "  + str(sharpness/10)
    rpistr += " --denoise "    + denoises[denoise]
    if Pi_Cam == 3 and v3_f_mode > 0 :
        rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode]
    #if Pi_Cam == 3 and v3_hdr == 1:
    #    rpistr += " --hdr"
    if scientific == 1:
        rpistr += " --tuning-file imx477_scientific2.json"
    #print (rpistr)
    p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
    st = time.monotonic()
    poll = p.poll()
    if poll != None and time.monotonic() - st < 5:
        poll = p.poll()
    if poll != None:
        print ("Failed to start sub-process")

# find username
h_user  = []
h_user  = (os.listdir("/home"))
l_len = len(h_user[0])
print(l_len)

# check for usb_stick
USB_Files  = []
USB_Files  = (os.listdir("/media/" + h_user[0] + "/"))
   
old_cap = Capture

# read list of todays existing Video Files
outvids = []
z = ""
y = ""
frames = 0
ram_frames = 0
Sideos = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
Sideos.sort()
for x in range(0,len(Sideos)):
   if len(Sideos[x]) > 32:
      if Sideos[x][16+(l_len-2):28+(l_len-2)] != z:
         z = Sideos[x][16+(l_len-2):28+(l_len-2)]
         outvids.append(z)
         frames +=1
   else:
      if Sideos[x][9:21] != y:
         y = Sideos[x][9:21]
         outvids.append(y)
         ram_frames +=1
vf = str(ram_frames) + " - " + str(frames)
# read list of todays existing Still Files
snaps = 0
pic_dir = "/home/" + h_user[0] + "/Pictures/"
pics  = []
pics = glob.glob(pic_dir + "*.jpg")
pics.sort
snaps = len(pics)
pf = str(ram_snaps) + " - " + str(snaps)

# read list of existing MP4 files
Mideos = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')

restart = 0
menu    = -1
zoom    = 0
ram_frames = 0

st = os.statvfs("/run/shm/")
sfreeram = (st.f_bavail * st.f_frsize)/1100000
                            
os.system("timedatectl >> sync.txt")
# read sync.txt file
sync = []
with open("sync.txt", "r") as file:
    line = file.readline()
    while line:
        sync.append(line.strip())
        line = file.readline()
if sync[4] == "System clock synchronized: yes":
    synced = 1
else:
    synced = 0

if noframe == 0:
   windowSurfaceObj = pygame.display.set_mode((scr_width,scr_height), 0, 24)
else:
   windowSurfaceObj = pygame.display.set_mode((scr_width,scr_height), pygame.NOFRAME, 24)
   
pygame.display.set_caption('Action')

global greyColor, redColor, greenColor, blueColor, dgryColor, lgryColor, blackColor, whiteColor, purpleColor, yellowColor
bredColor =   pygame.Color(255,   0,   0)
lgryColor =   pygame.Color(192, 192, 192)
blackColor =  pygame.Color(  0,   0,   0)
whiteColor =  pygame.Color(250, 250, 250)
greyColor =   pygame.Color(128, 128, 128)
dgryColor =   pygame.Color( 64,  64,  64)
greenColor =  pygame.Color(  0, 255,   0)
purpleColor = pygame.Color(255,   0, 255)
yellowColor = pygame.Color(255, 255,   0)
blueColor =   pygame.Color(  0,   0, 255)
redColor =    pygame.Color(200,   0,   0)

def button(col,row, bColor):
   colors = [greyColor, dgryColor, whiteColor, redColor, greenColor]
   Color = colors[bColor]
   bx = cwidth + (col * bw) + 2
   by = row * bh
   pygame.draw.rect(windowSurfaceObj,Color,Rect(bx+1,by,bw-2,bh))
   pygame.draw.line(windowSurfaceObj,whiteColor,(bx+1,by),(bx+bw,by))
   pygame.draw.line(windowSurfaceObj,greyColor,(bx+bw-1,by),(bx+bw-1,by+bh))
   pygame.draw.line(windowSurfaceObj,whiteColor,(bx,by),(bx,by+bh-1))
   pygame.draw.line(windowSurfaceObj,dgryColor,(bx+1,by+bh-1),(bx+bw-1,by+bh-1))
   pygame.display.update(bx, by, bw-1, bh)
   return

def text(col,row,fColor,top,upd,msg,fsize,bcolor):
   global font_size, fontObj, bh, bw, cwidth
   fsize = int(bh/3)
   if os.path.exists ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf'): 
       fontObj = pygame.font.Font('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', int(fsize))
   else:
       fontObj = pygame.font.Font(None, int(fsize))
   colors =  [dgryColor, greenColor, yellowColor, redColor, greenColor, blueColor, whiteColor, greyColor, blackColor, purpleColor]
   Color  =  colors[fColor]
   bColor =  colors[bcolor]
   bx = cwidth + (col * bw)
   by = row * bh
   msgSurfaceObj = fontObj.render(msg, False, Color)
   msgRectobj = msgSurfaceObj.get_rect()
   if top == 0:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+3,by+1,bw-2,int(bh/2)))
       msgRectobj.topleft = (bx + 7, by + 3)
   else:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+int(bw/4),by+int(bh/2),int(bw/1.5),int(bh/2)-1))
       msgRectobj.topleft = (bx+int(bw/4), by + int(bh/2))
   windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
   if upd == 1:
      pygame.display.update(bx, by, bw, bh)

def main_menu():
    global ram_frames,frames,vid_pic,menu,ram_snaps,snaps,sd_hour,pf,vf,synced,Capture
    menu = -1
    Capture = old_cap
    for d in range(0,11):
         button(0,d,0)
    button(0,1,3)
    if Capture == 0:
        button(0,0,0)
        text(0,0,9,0,1,"CAPTURE",20,7)
    else:
        button(0,0,4)
        text(0,0,6,0,1,"CAPTURE",20,4)
    text(0,1,6,0,1,"RECORD",20,3)
    text(0,2,1,0,1,"DETECTION",14,7)
    text(0,2,1,1,1,"Settings",14,7)
    text(0,3,1,0,1,"CAMERA",14,7)
    text(0,3,1,1,1,"Settings 1",14,7)
    text(0,4,1,0,1,"CAMERA",14,7)
    text(0,4,1,1,1,"Settings 2",14,7)
    text(0,5,1,0,1,"OTHER",14,7)
    text(0,5,1,1,1,"Settings ",14,7)
    if ((ram_frames > 0 or frames > 0) and vid_pic == 0 and menu == -1) or ((ram_snaps > 0 or snaps > 0) and vid_pic == 1 and menu == -1):
        text(0,6,1,0,1,"SHOW and",14,7)
        text(0,6,1,1,1,"DELETE",14,7)
    else:
        text(0,6,0,0,1,"SHOW and",14,7)
        text(0,6,0,1,1,"DELETE",14,7)
    if (ram_frames > 0 or frames > 0) and vid_pic == 0:
        text(0,7,1,0,1,"MAKE",14,7)
        text(0,7,1,1,1,"MP4",14,7)
    else:
        text(0,7,0,0,1,"MAKE",14,7)
        text(0,7,0,1,1,"MP4",14,7)
    if vid_pic == 0:
        text(0,8,2,0,1,"VIDEOS",14,7)
        vf = str(ram_frames) + " - " + str(frames)
        text(0,8,3,1,1,vf,18,7)
    else:
        text(0,8,2,0,1,"PICTURES",14,7)
        pf = str(ram_snaps) + " - " + str(snaps)
        text(0,8,3,1,1,pf,18,7)
    text(0,9,1,0,1,"SD Hour",14,7)
    if synced == 1:
        text(0,9,3,1,1,str(sd_hour) + ":00",14,7)
    else:
        text(0,9,0,1,1,str(sd_hour)+":00",14,7)
    text(0,10,0,0,1,"Copy    EXIT",14,7)
    st = os.statvfs("/run/shm/")
    freeram = (st.f_bavail * st.f_frsize)/1100000
    free = (os.statvfs('/'))
    used_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
    ss = str(int(freeram)) + " - " + str(int(used_storage))
    text(0,10,3,1,1,ss,15,7)
    
main_menu()
oldimg = []
show = 0
vidjr = 0
Videos = []
last = time.monotonic()

# clear ram
zpics = glob.glob('/run/shm/*.jpg')
for tt in range(0,len(zpics)):
    os.remove(zpics[tt])

# check sd card space
free = (os.statvfs('/'))
used_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
ss = str(int(sfreeram)) + " - " + str(int(used_storage))
text(0,10,3,1,1,ss,15,7)

# start Pi Camera subprocess
Camera_start(cap_width,cap_height,zoom,vid_pic)
fan_timer = time.monotonic()

while True:
    time.sleep(0.1)
    # fan ctrl
    if time.monotonic() - fan_timer > fan_time:
        if os.path.exists("sync.txt"):
            os.rename('sync.txt', 'oldsync.txt')
        os.system("timedatectl >> sync.txt")
        # read sync.txt file
        sync = []
        with open("sync.txt", "r") as file:
            line = file.readline()
            while line:
                sync.append(line.strip())
                line = file.readline()
        if sync[4] == "System clock synchronized: yes":
            synced = 1
            if menu == -1:
                text(0,9,3,1,1,str(sd_hour) + ":00",14,7)
        else:
            synced = 0
            if menu == -1:
                text(0,9,0,1,1,str(sd_hour)+":00",14,7)
        # check current hour
        now = datetime.datetime.now()
        hour = int(now.strftime("%H"))
        # shutdown if shutdown hour reached and clocked synced
        if hour > sd_hour - 1 and sd_hour != 0 and time.monotonic() - start_up > 600 and synced == 1:
            # EXIT
            if trace == 1:
                 print ("Step 13 TIMED EXIT")
            # move any videos to SD Card
            if ram_frames > 0:
                if menu !=1 :
                    button(0,0,1)
                    text(0,0,5,0,1,"CAPTURE",20,0)
                zpics = glob.glob('/run/shm/2*.jpg')
                zpics.sort()
                for xx in range(0,len(zpics)):
                    shutil.copy(zpics[xx], '/home/' + h_user[0] + '/Videos/')
            if ram_snaps > 0:
                if menu !=1 :
                    button(0,0,1)
                    text(0,0,5,0,1,"CAPTURE",20,0)
                zpics = glob.glob('/run/shm/P*.jpg')
                zpics.sort()
                for xx in range(0,len(zpics)):
                    shutil.copy(zpics[xx], '/home/' + h_user[0] + '/Pictures/')
            # move MP4 to USB if present
            USB_Files  = []
            USB_Files  = (os.listdir("/media/" + h_user[0]))
            if len(USB_Files) > 0:
                spics = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                spics.sort()
                for xx in range(0,len(spics)):
                    movi = spics[xx].split("/")
                    if not os.path.exists('/media/' + h_user[0] + "/" + USB_Files[0] + "/" + movi[4]):
                        shutil.move(spics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/")
            if use_gpio == 1:
                pwm.stop()
            pygame.quit()
            os.killpg(p.pid, signal.SIGTERM)
            time.sleep(5)
            os.system("sudo shutdown -h now")
            
        fan_timer = time.monotonic()
        cpu_temp = str(CPUTemperature()).split("=")
        temp = float(str(cpu_temp[1])[:-1])
        dc = int(((temp - fan_low)/(fan_high - fan_low)) * 100)
        dc = max(dc,25)
        dc = min(dc,100)
        if temp > fan_low and use_gpio == 1:
            pwm.ChangeDutyCycle(dc)
            if menu ==4 :
               text(0,7,1,0,1,"Fan High  " + str(dc) + "%",14,7)
        elif temp < fan_low and use_gpio == 1:
            pwm.ChangeDutyCycle(0)
            if menu == 4: 
                text(0,7,2,0,1,"Fan High",14,7)
        st = os.statvfs("/run/shm/")
        freeram = (st.f_bavail * st.f_frsize)/1100000
        poll = p.poll()
        if poll != None and trace == 1:
            print ("Step 2 P STOPPED " + str(int(freeram)))
        apics = glob.glob('/run/shm/test*.jpg')
        time.sleep(0.25)
        bpics = glob.glob('/run/shm/test*.jpg')
        if apics == bpics:
            if trace == 1:
                print ("Step 2 SUB PROC STOPPED")
            #if ram_frames > 0:
                #if menu !=1 :
                #    text(0,0,8,0,1,"CAPTURE",20,0)
                #zpics = glob.glob('/run/shm/2*.jpg')
                #zpics.sort()
                #for xx in range(0,len(zpics)):
                #    shutil.copy(zpics[xx],'/home/' + h_user[0] + '/Videos/')
            restart = 1
        
    zpics = glob.glob('/run/shm/test*.jpg')
    while len(zpics) < pre_frames:
        zpics = glob.glob('/run/shm/test*.jpg')
    zpics.sort(reverse=True)
    image = pygame.image.load(zpics[1])
    w = len(zpics)
    for tt in range(pre_frames,w):
        os.remove(zpics[tt])
    for tt in range(pre_frames,w):
        del zpics[pre_frames]

    if show == 0:
        if col_timer > 0 and time.monotonic() - col_timer > 3:
            col_timer = 0
        image2 = pygame.surfarray.pixels3d(image)
        crop2 = image2[a2-h_crop2:a2+h_crop2,(b2)-v_crop2:(b2)+v_crop2]
        if col_filter < 3:
            gray = crop2[:,:,col_filter]
        else:
            gray = cv2.cvtColor(crop2,cv2.COLOR_RGB2GRAY)
        if col_filter < 3 and (preview == 1 or col_timer > 0) and zoom == 0:
            im = Image.fromarray(gray)
            im.save("/run/shm/qw.jpg")
        gray = gray.astype(np.int16)
        detect = 0
           
        if np.shape(gray) == np.shape(oldimg):
            if menu == 0 or menu == 4:
                foc = cv2.Laplacian(gray, cv2.CV_64F).var()
                if zoom == 0 and menu == 0:
                    text(0,8,6,1,1,str(int(foc)),14,7)
                elif menu == 4:
                    text(0,0,6,1,1,str(int(foc)),14,7)
                #else:
                #    text(0,8,6,1,1,str(int(foc)),14,0)

            diff = h_crop2 * v_crop2 * 4
            diff = max(diff,1)
            ar5 = abs(np.subtract(np.array(gray),np.array(oldimg)))
            ar5[ar5 <  threshold] = 0
            ar5[ar5 >= threshold2] = 0
            ar5[ar5 >= threshold] = 1
            # NOISE REDUCTION
            if nr > 0:
                pr = np.diff(np.diff(ar5))
                pr[pr < -2 ] = 0
                if nr > 1:
                    pr[pr > -1] = 0
                else:
                    pr[pr > -2] = 0
                pr[pr < 0 ] = -1
                mt = np.zeros((h_crop2*2,1),dtype = 'int')
                pr = np.c_[mt,pr,mt]
  
                qc = np.swapaxes(ar5,0,1)
                qr = np.diff(np.diff(qc))
                qr[qr < -2 ] = 0
                if nr > 1:
                    qr[qr > -1] = 0
                else:
                    qr[qr > -2] = 0
                qr[qr < 0] = -1
                mt = np.zeros((v_crop2*2,1),dtype = 'int')
                qr = np.c_[mt,qr,mt]
   
                qr = np.swapaxes(qr,0,1)
                qt = pr + qr
                qt[qt < -2] = 0
                if nr > 1:
                    qt[qt > -1] = 0
                else:
                    qt[qt > -2] = 0 
                qt[qt < 0] = -1
                ar5 = ar5 + qt
            sar5 = np.sum(ar5)
            
            if menu == 0:
                text(0,1,2,0,1,"Low Detect " + str(int((sar5/diff) * 100)) + "%",14,7)
            if preview == 1:
                imagep = pygame.surfarray.make_surface(ar5 * 201)
                imagep.set_colorkey(0, pygame.RLEACCEL)
            # copy 1 set of video files to sd card if auto_save = 1 after 10 seconds of no activity   
            if ram_frames > auto_limit and time.monotonic() - last > auto_time and auto_save == 1:
              try:
                if trace == 1:
                    print ("Step 4 AUTO SAVE")
                text(0,0,5,0,1,"CAPTURE",20,0)
                # read list of existing RAM Video Files
                Videos = glob.glob('/run/shm/2*.jpg')
                Videos.sort()
                outvids = []
                z = ""
                for x in range(0,len(Videos)):
                    if Videos[x][9:21] != z:
                        z = Videos[x][9:21]
                        outvids.append(z)
                # copy jpgs to sd card
                zspics = glob.glob('/run/shm/' +  str(outvids[0]) + '*.jpg')
                zspics.sort()
                for xx in range(0,len(zspics)):
                    shutil.move(zspics[xx], '/home/'  + h_user[0] + '/Videos/')
               
                ram_frames -=1
                frames +=1
                vf = str(ram_frames) + " - " + str(frames)
                if menu == -1 and vid_pic == 0:
                    text(0,8,3,1,1,vf,18,7)
                # if sd card space low copy to USB if present
                free = (os.statvfs('/'))
                used_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
                if used_storage > storage_limit :
                    if trace == 1:
                        print ("Step 5 USED > LIMIT")
                    USB_Files  = []
                    USB_Files  = (os.listdir("/media/" + h_user[0] ))
                    if len(USB_Files) > 0:
                        zupics = glob.glob('/home/' + h_user[0] + '/*.jpg')
                        zupics.sort()
                        for xx in range(0,len(zupics)):
                            shutil.move(zupics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/Videos/")
                            if menu == -1:
                                text(0,8,3,1,1,str(len(zupics)-xx),18,7)
                        frames = 0
                        vf = str(ram_frames) + " - " + str(frames)
                        if menu == -1:
                            text(0,8,3,1,1,vf,18,7)
                if Capture == 0:
                    button(0,0,0)
                    text(0,0,9,0,1,"CAPTURE",20,7)
                else:
                    button(0,0,4)
                    text(0,0,6,0,1,"CAPTURE",20,4)
                last = time.monotonic()
              except:
                  pass

            # detection of motion or interval timed out
            if ((sar5/diff) * 100 > detection and (sar5/diff) * 100 < det_high) or (time.monotonic() - timer10 > interval and timer10 != 0 and threshold == 0) or record == 1 :
                now = datetime.datetime.now()
                timestamp = now.strftime("%y%m%d%H%M%S")
                if trace == 1:
                    print ("Step 6 DETECTED " + str(int((sar5/diff) * 100)))
                if timer10 != 0:
                   timer10 = time.monotonic()
                if menu == 0:
                    text(0,1,1,0,1,"Low Detect "  + str(int((sar5/diff) * 100)) + "%",14,7)
                if Capture == 1 or record == 1:
                    detect = 1
                    record = 0
                    if ES > 0 and use_gpio == 1: # trigger external camera
                        GPIO.output(s_focus, GPIO.HIGH)
                        time.sleep(0.25)
                        GPIO.output(s_trig, GPIO.HIGH)
                        if ES == 1:
                            time.sleep(0.25)
                            GPIO.output(s_trig, GPIO.LOW)
                            GPIO.output(s_focus, GPIO.LOW)
                    # capture video frames
                    if vid_pic == 0:
                        vid = 1
                        if use_gpio == 1:
                            GPIO.output(led, GPIO.HIGH)
                        button(0,0,1)
                        text(0,0,3,0,1,"CAPTURE",20,0)
                        text(0,0,1,1,1," ",15,0)
                        start = time.monotonic()
                        fx = 1
                        st = os.statvfs("/run/shm/")
                        freeram = (st.f_bavail * st.f_frsize)/1100000
                        while time.monotonic() - start < v_length/1000 and freeram > ram_limit:
                            time.sleep(0.1)
                            st = os.statvfs("/run/shm/")
                            freeram = (st.f_bavail * st.f_frsize)/1100000
                            ss = str(int(freeram)) + " - " + str(int(used_storage))
                            text(0,10,3,1,1,ss,15,7)
                        # rename pre-frames
                        if trace == 1:
                            print ("Step 7 RENAME PRE")
                        zpics.sort()
                        for x in range(0,pre_frames): 
                            fxx = "00000" + str(fx)
                            if os.path.exists(zpics[x]):
                                os.rename(zpics[x],zpics[x][0:9] + timestamp + "_" + str(fxx[-5:]) + '.jpg')
                                fx +=1
                        # rename new frames
                        if trace == 1:
                            print ("Step 8 RENAME NEW")
                        zpics = glob.glob('/run/shm/test*.jpg')
                        zpics.sort()
                        #print (len(zpics))
                        for x in range(0,len(zpics)):
                            fxx = "00000" + str(fx)
                            if os.path.exists(zpics[x]):
                                os.rename(zpics[x],zpics[x][0:9] + timestamp + "_" + str(fxx[-5:]) + '.jpg')
                                fx +=1
                        ram_frames +=1
                        vf = str(ram_frames) + " - " + str(frames)
                        if menu == -1:
                            text(0,8,3,1,1,vf,18,7)
                        pygame.image.save(image,"/run/shm/" + str(timestamp) + "_99999.jpg")
                        
                        st = os.statvfs("/run/shm/")
                        freeram = (st.f_bavail * st.f_frsize)/1100000
                        free = (os.statvfs('/'))
                        used_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
                        ss = str(int(freeram)) + " - " + str(int(used_storage))
                        text(0,10,3,1,1,ss,15,7)
                        #if menu == -1:
                        #    text(0,0,3,1,1,str(int(used_storage)),15,0)
                        if ram_frames > 0 and freeram < ram_limit:
                            if trace == 1:
                                print ("Step 10 COPY TO SD")
                            text(0,0,5,0,1,"CAPTURE",20,0)
                            text(0,0,5,1,1," ",15,0)
                            Videos = glob.glob('/run/shm/2*.jpg')
                            Videos.sort()
                            outvids = []
                            z = ""
                            for x in range(0,len(Videos)):
                                if Videos[x][9:21] != z:
                                    z = Videos[x][9:21]
                                    outvids.append(z)
                            zvpics = glob.glob('/run/shm/' +  str(outvids[0]) + '*.jpg')
                            zvpics.sort()
                            # move RAM Files to SD card
                            for xx in range(0,len(zvpics)):
                                if not os.path.exists('/home/' + h_user[0] + "/" + '/Videos/' + zvpics[xx][9:]):
                                    shutil.move(zvpics[xx], '/home/' + h_user[0] + '/Videos/')
                            # read list of existing RAM Video Files
                            Videos = glob.glob('/run/shm/2*.jpg')
                            Videos.sort()
                            outvids = []
                            z = ""
                            for x in range(0,len(Videos)):
                                if Videos[x][9:21] != z:
                                    z = Videos[x][9:21]
                                    outvids.append(z)
                            ram_frames = len(outvids)
                            #print("x" + str(ram_frames))
                            # read list of existing SD Card Video Files
                            if trace == 1:
                                print ("Step 11 READ SD FILES")
                            Videos = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                            Videos.sort()
                            outvids = []
                            z = ""
                            for x in range(0,len(Videos)):
                                if Videos[x][16+(l_len-2):28+(l_len-2)] != z:
                                    z = Videos[x][16+(l_len-2):28+(l_len-2)]
                                    outvids.append(z)
                            frames = len(outvids)
                            vf = str(ram_frames) + " - " + str(frames)
                            if menu == 3:
                                if ram_frames + frames > 0:
                                    text(0,4,3,1,1,str(ram_frames + frames),18,7)
                                else:
                                    text(0,4,3,1,1," ",18,7)
                        # check free SD storage space
                        free = (os.statvfs('/'))
                        used_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
                        if used_storage > storage_limit and menu == -1:
                            text(0,0,3,1,1,str(int(used_storage)),15,0)
                        else:
                            text(0,0,1,1,1,str(int(used_storage)),15,0)
                        if menu == -1:
                            text(0,8,3,1,1,vf,18,7)
                        timer10 = time.monotonic()
                        oldimg = []
                        vidjr = 1
                        # clear LONG EXT trigger
                        if ES == 2 and use_gpio == 1:
                            GPIO.output(s_trig, GPIO.LOW)
                            GPIO.output(s_focus, GPIO.LOW)
                            GPIO.output(led, GPIO.LOW)
                    else:
                        # take a snap
                        if use_gpio == 1:
                            GPIO.output(led, GPIO.HIGH)
                        button(0,0,1)
                        text(0,0,3,0,1,"CAPTURE",20,0)
                        text(0,0,1,1,1," ",15,0)
                        pygame.image.save(image,"/run/shm/P" + str(timestamp) + "_" + str(snaps) + ".jpg")
                        free = (os.statvfs('/'))
                        used_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
                        if used_storage > storage_limit:
                            text(0,0,3,1,1,str(int(used_storage)),15,0)
                        else:
                            text(0,0,1,1,1,str(int(used_storage)),15,0)
                        while not os.path.exists("/run/shm/P" + str(timestamp) + "_" + str(snaps) + ".jpg"):
                            time.sleep(0.1)
                        pics.append("/run/shm/P" + str(timestamp) + "_" + str(snaps) + ".jpg")
                        ram_snaps +=1
                        if menu == -1:
                            vf = str(ram_snaps) + " - " + str(snaps)
                            text(0,8,3,1,1,vf,18,7)
                        timer10 = time.monotonic()
                        if ES == 2 and use_gpio == 1:
                            GPIO.output(s_trig, GPIO.LOW)
                            GPIO.output(s_focus, GPIO.LOW)
                            GPIO.output(led, GPIO.LOW)
                        st = os.statvfs("/run/shm/")
                        freeram = (st.f_bavail * st.f_frsize)/1100000
                        free = (os.statvfs('/'))
                        used_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
                        ss = str(int(freeram)) + " - " + str(int(used_storage))
                        text(0,10,3,1,1,ss,15,7)
                        if snaps > 0 and freeram < ram_limit:
                            if trace == 1:
                                print ("Step 10 COPY snaps TO SD")
                            text(0,0,5,0,1,"CAPTURE",20,0)
                            text(0,0,5,1,1," ",15,0)
                            # copy snap jpgs to sd card
                            # read list of existing RAM Picture Files
                            ram_snaps = glob.glob('/run/shm/P*.jpg')
                            ram_snaps.sort()
                            # move RAM picture Files to SD card
                            for xx in range(0,len(ram_snaps)):
                                if not os.path.exists('/home/' + h_user[0] + "/" + '/Pictures/' + ram_snaps[xx][9:]):
                                    shutil.move(ram_snaps[xx], '/home/' + h_user[0] + '/Pictures/')
                            # read list of existing RAM Picture Files
                            ram_snaps = glob.glob('/run/shm/P*.jpg')
                            ram_snaps.sort()

                            # read list of existing SD Card Video Files
                            if trace == 1:
                                print ("Step 11 READ SD PICTURE FILES")
                            snaps = glob.glob('/home/' + h_user[0] + '/Pictures/*.jpg')
                            snaps.sort()
                           
                            pf = str(ram_snaps) + " - " + str(snaps)
                            if menu == 3:
                                if ram_snaps + snaps > 0:
                                    text(0,4,3,1,1,str(ram_snaps + snaps),18,7)
                                else:
                                    text(0,4,3,1,1," ",18,7)
                    if ((ram_frames > 0 or frames > 0) and vid_pic == 0 and menu == -1) or ((ram_snaps > 0 or snaps > 0) and vid_pic ==1 and menu == -1):
                        text(0,6,1,0,1,"SHOW and",14,7)
                        text(0,6,1,1,1,"DELETE",14,7)
                    elif menu == -1:
                        text(0,6,0,0,1,"SHOW and",14,7)
                        text(0,6,0,1,1,"DELETE",14,7)
                    if (ram_frames > 0 or frames > 0) and vid_pic == 0 and menu == -1:
                        text(0,7,1,0,1,"MAKE",14,7)
                        text(0,7,1,1,1,"MP4",14,7)
                    elif menu == -1:
                        text(0,7,0,0,1,"MAKE",14,7)
                        text(0,7,0,1,1,"MP4",14,7)
                    if vid_pic == 0 and menu == -1:
                        text(0,8,2,0,1,"VIDEOS",14,7)
                        vf = str(ram_frames) + " - " + str(frames)
                        text(0,8,3,1,1,vf,18,7)
                    elif menu == -1:
                        text(0,8,2,0,1,"PICTURES",14,7)
                        pf = str(ram_snaps) + " - " + str(snaps)
                        text(0,8,3,1,1,pf,18,7)
                    USB_Files  = []
                    USB_Files  = (os.listdir("/media/" + h_user[0]))   
                    # check storage space for jpg files ,move to usb stick (if available)
                    if used_storage > storage_limit and len(USB_Files) > 0 :
                        if trace == 1:
                            print ("Step 12 USED > LIMIT")
                        os.killpg(p.pid, signal.SIGTERM)
                        if not os.path.exists('/media/' + h_user[0] + "/" + USB_Files[0] + "/Videos/") :
                            os.system('mkdir /media/' + h_user[0] + "/" + USB_Files[0] + "/Videos/")
                        if not os.path.exists('/media/' + h_user[0] + "/" + USB_Files[0] + "/Pictures/") :
                            os.system('mkdir /media/' + h_user[0] + "/" + USB_Files[0] + "/Pictures/")
                        if len(USB_Files) > 0:
                            zpics = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                            zpics.sort()
                            for xx in range(len(zpics)-1,-1,-1):
                                shutil.move(zpics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/Videos/")
                            ram_frames = 0
                            frames = 0
                            vf = str(ram_frames) + " - " + str(frames)
                            if menu == -1 and vid_pic == 0:
                                text(0,8,3,1,1,vf,18,7)
                            spics = glob.glob(pic_dir + '*.jpg')
                            spics.sort()
                            for xx in range(0,len(zpics)):
                                shutil.move(spics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/Pictures/")
                            snaps = 0
                            if (menu == 0 or menu == -1) and vid_pic == 1:
                                if menu == 0:
                                    text(0,6,3,1,1,str(snaps),18,7)
                                else:
                                    text(0,8,3,1,1,str(snaps),18,7)
                    if used_storage > storage_limit and len(USB_Files) == 0 :
                        #STOP CAPTURE IF NO MORE SD CARD SPACE AND NO USB STICK
                        if trace == 1:
                            print ("Step 12a sd card limit exceeded")
                        Capture = 0
                        button(0,0,0)
                        text(0,0,7,0,1,"STOPPED",20,7)
                        
                    if use_gpio == 1:
                        GPIO.output(led, GPIO.LOW)
                    if Capture == 0:
                        button(0,0,0)
                        text(0,0,9,0,1,"CAPTURE",20,7)
                        text(0,0,1,1,1," ",15,7)
                    else:
                        button(0,0,4)
                        text(0,0,6,0,1,"CAPTURE",20,4)
                        text(0,0,6,1,1," ",15,4)
                    if menu == -1:
                        button(0,1,3)
                        text(0,1,6,0,1,"RECORD",20,3)
                    
                else:
                    if Capture == 1:
                        text(0,0,3,1,1,str(interval - (int(time.monotonic() - timer10))),15,0)
            elif menu == 0:
                text(0,1,2,0,1,"Low Detect " + str(int((sar5/diff) * 100)) + "%",14,7)
        # show frame
        if vid_pic == 0:
            xheight = int(cwidth * 0.5625)
        else:
            xheight = int(cwidth * 0.75)
        if xheight > scr_height:
            xheight = scr_height
        if zoom == 0:
            cropped = pygame.transform.scale(image, (cwidth,xheight))
        else:
            ta = int(a * (cap_width/cwidth)) - (h_crop * (cap_width/cwidth))
            if ta + cwidth > cap_width:
                ta = int(cap_width - cwidth)
            tb = int(b * (cap_height/xheight)) - (v_crop * (cap_height/xheight))
            if tb + xheight > cap_height:
                tb = int(cap_height - xheight)
            cropped_region = (int(ta),int(tb), int(cwidth), int(xheight))
            cropped = image.subsurface(cropped_region)
        windowSurfaceObj.blit(cropped, (0, 0))
        # show colour filtering
        if col_filter < 3 and (preview == 1 or col_timer > 0) and zoom == 0:
            imageqw = pygame.image.load('/run/shm/qw.jpg')
            imagegray = pygame.transform.scale(imageqw, (v_crop*2,h_crop*2))
            imagegray = pygame.transform.flip(imagegray, True, False)
            imagegray = pygame.transform.rotate(imagegray, 90)
            windowSurfaceObj.blit(imagegray, (a-h_crop,b-v_crop))
        # show detected pixels if required
        if preview == 1 and np.shape(gray) == np.shape(oldimg):
            imagep = pygame.transform.scale(imagep, (h_crop*2,v_crop*2))
            windowSurfaceObj.blit(imagep, (a-h_crop,b-v_crop))
            if vid_pic == 0:
                pygame.draw.rect(windowSurfaceObj, (255,255,0), Rect(int(cwidth/2) - int(xheight/2) ,0 ,int(xheight),int(xheight)), 1)
            pygame.draw.line(windowSurfaceObj, (255,255,0), (int(cwidth/2) - 50,int(xheight/2)),(int(cwidth/2) + 50, int(xheight/2)))
            pygame.draw.line(windowSurfaceObj, (255,255,0), (int(cwidth/2),int(xheight/2)-50),(int(cwidth/2), int(xheight/2)+50))
        if zoom == 0:
            pygame.draw.rect(windowSurfaceObj, (0,255,0), Rect(a - h_crop,b - v_crop ,h_crop*2,v_crop*2), 2)
        if preview == 1 and detect == 1:
            now = datetime.datetime.now()
            timestamp = now.strftime("%y%m%d%H%M%S")
            pygame.image.save(windowSurfaceObj, '/home/' + h_user[0] + '/scr' + str(timestamp) + '.jpg')
        pygame.display.update(0,0,cwidth,xheight)
        if vidjr != 1:
           oldimg[:] = gray[:]
        vidjr = 0
    save_config = 0
    #check for any mouse button presses
    for event in pygame.event.get():
        if (event.type == MOUSEBUTTONUP):
            timer = time.monotonic()
            mousex, mousey = event.pos
            if mousex < cwidth and zoom == 0:
               a = mousex
               b = mousey
               if a + h_crop > cwidth:
                   a = cwidth - h_crop
               if b + v_crop > xheight:
                   b = xheight - v_crop
               if a - h_crop < 0:
                   a = h_crop
               if b - v_crop < 0:
                   b = v_crop
               a2 = int(a * (cap_width/cwidth))
               b2 = int(b * (cap_height/xheight))
               save_config = 1
               
            elif mousex > cwidth:
                g = int(mousey/bh)
                h = 0
                if mousex > scr_width - (bw/2):
                    h = 1
                if g == 0 and menu == -1 :
                    # CAPTURE
                    if use_gpio == 1:
                        GPIO.output(led, GPIO.LOW)
                    Capture +=1
                    if zoom > 0:
                        restart = 1
                    zoom = 0
                    if Capture > 1:
                        Capture = 0
                        button(0,0,0)
                        text(0,0,9,0,1,"CAPTURE",20,7)
                        timer10 = 0
                    else:
                        num = 0
                        button(0,0,4)
                        text(0,0,6,0,1,"CAPTURE",20,4)
                    old_cap = Capture
                    save_config = 1

                elif g == 10 and h == 1 and menu == -1:
                    # EXIT
                    if trace == 1:
                         print ("Step 13 EXIT")
                    if ram_frames > 0:
                        if menu !=1 :
                            button(0,0,1)
                            text(0,0,5,0,1,"CAPTURE",20,0)
                        zpics = glob.glob('/run/shm/2*.jpg')
                        zpics.sort()
                        for xx in range(0,len(zpics)):
                            shutil.copy(zpics[xx], '/home/' + h_user[0] + '/Videos/')
                    if ram_snaps > 0:
                        if menu !=1 :
                            button(0,0,1)
                            text(0,0,5,0,1,"CAPTURE",20,0)
                        zpics = glob.glob('/run/shm/P*.jpg')
                        zpics.sort()
                        for xx in range(0,len(zpics)):
                            shutil.copy(zpics[xx], '/home/' + h_user[0] + '/Pictures/')
                    #move MP4 to usb if present
                    USB_Files  = []
                    USB_Files  = (os.listdir("/media/" + h_user[0]))
                    if len(USB_Files) > 0:
                        spics = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                        spics.sort()
                        for xx in range(0,len(spics)):
                            movi = spics[xx].split("/")
                            if not os.path.exists('/media/' + h_user[0] + "/" + USB_Files[0] + "/" + movi[4]):
                                shutil.move(spics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/")
                    if use_gpio == 1:
                        pwm.stop()
                    pygame.quit()
                    os.killpg(p.pid, signal.SIGTERM)

                elif g == 10 and h == 0 and menu == -1:
                    # check for usb_stick and copy Videos and Pictures to it
                    Capture = 0
                    button(0,0,0)
                    text(0,0,5,0,1,"CAPTURE",20,7)
                    if use_gpio == 1:
                        GPIO.output(led, GPIO.HIGH)
                    USB_Files  = []
                    USB_Files  = (os.listdir("/media/" + h_user[0]))
                    if len(USB_Files) > 0 and ((frames + ram_frames > 0) or (ram_snaps + snaps) > 0) and menu != 5:
                        if not os.path.exists('/media/' + h_user[0] + "/" + USB_Files[0] + "/Videos/") :
                            os.system('mkdir /media/' + h_user[0] + "/" + USB_Files[0] + "/Videos/")
                        if not os.path.exists('/media/' + h_user[0] + "/" + USB_Files[0] + "/Pictures/") :
                            os.system('mkdir /media/' + h_user[0] + "/" + USB_Files[0] + "/Pictures/")
                        zpics = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                        zpics.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(zpics)-1):
                            if zpics[x][16+(l_len-2):28+(l_len-2)] != z:
                                z = zpics[x][16+(l_len-2):28+(l_len-2)]
                                outvids.append(z)
                        for xz in range(0,len(outvids)):
                            if menu == -1:
                                text(0,8,3,1,1,str(len(outvids) - xz),18,7)
                            xzpics = glob.glob('/home/' + h_user[0] + '/Videos/' + outvids[xz] + '*.jpg')
                            xzpics.sort()
                            for xx in range(0,len(xzpics)):
                                shutil.move(xzpics[xx],'/media/' + h_user[0] + '/' + USB_Files[0] + "/Videos/")
                        frames = 0
    
                        zpics = glob.glob('/run/shm/2*.jpg')
                        zpics.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(zpics)-1):
                            if zpics[x][9:21] != z:
                                z = zpics[x][9:21]
                                outvids.append(z)
                        for xz in range(0,len(outvids)):
                            if menu == -1:
                                text(0,8,3,1,1,str(len(outvids) - xz),18,7)
                            xzpics = glob.glob('/run/shm/' + outvids[xz] + '*.jpg')
                            xzpics.sort()
                            for xx in range(0,len(xzpics)):
                                shutil.move(xzpics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/Videos/")
                        ram_frames = 0

                        vf = str(ram_frames) + " - " + str(frames)
                        if menu == -1 and vid_pic == 0:
                            text(0,8,3,1,1,vf,18,7)
                        #move Pictures to usb    
                        spics = glob.glob(pic_dir + '*.jpg')
                        spics.sort()
                        for xx in range(0,len(spics)):
                            shutil.move(spics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/Pictures/")
                        snaps = 0
                        spics = glob.glob('/run/shm/P*.jpg')
                        spics.sort()
                        for xx in range(0,len(spics)):
                            shutil.move(spics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/Pictures/")
                        ram_snaps = 0
                        pf = str(ram_snaps) + " - " + str(snaps)
                        if menu == -1:
                            text(0,6,0,0,1,"SHOW and",14,7)
                            text(0,6,0,1,1,"DELETE",14,7)
                    if menu == 5:
                        #move MP4 to usb    
                        spics = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                        spics.sort()
                        for xx in range(0,len(spics)):
                            shutil.move(spics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/Videos/")
                    
                    if reboot == 1:
                        os.system('reboot')
                   
                    Capture = 1
                    button(0,0,4)
                    text(0,0,6,0,1,"CAPTURE",20,4)
                    text(0,0,1,1,1," ",15,4)
                    if vid_pic == 0:
                        if menu == -1:
                            text(0,8,2,0,1,"VIDEOS",14,7)
                            text(0,8,3,1,1,vf,18,7)
                    else:
                        if menu == -1:
                            text(0,8,2,0,1,"PICTURES",14,7)
                            text(0,8,3,1,1,pf,18,7)
                    if use_gpio == 1:
                        GPIO.output(led, GPIO.LOW)
                    restart = 1

                    
                elif g == 0 and menu == 0:
                    # PREVIEW
                    preview +=1
                    if preview > 1:
                        preview = 0
                        button(0,0,0)
                        text(0,0,2,0,1,"Preview",14,7)
                        text(0,0,2,1,1,"Threshold",13,7)
                    else:
                        button(0,0,1)
                        text(0,0,1,0,1,"Preview",14,0)
                        text(0,0,1,1,1,"Threshold",13,0)
                    save_config = 1
                    
                elif g == 1 and menu == 0:
                    # Low Detection
                    if (h == 1 and event.button == 1) or event.button == 4:
                        detection +=1
                        detection = min(detection,100)
                    else:
                        detection -=1
                        detection = max(detection,0)
                    text(0,1,3,1,1,str(detection),18,7)
                    save_config = 1
                    
                elif g == 3 and menu == 0:
                    # Threshold
                    if (h == 1 and event.button == 1) or event.button == 4:
                        threshold +=1
                        threshold = min(threshold,threshold2 - 1)
                        text(0,3,2,0,1,"Lo Threshold",14,7)
                        text(0,3,3,1,1,str(threshold),18,7)
                        timer10 = 0
                        if threshold == 1:
                           if Capture == 1:
                               text(0,0,4,1,1," ",15,0)
                           else:
                               text(0,0,4,1,1," ",15,7)
                           
                    else:
                        threshold -=1
                        threshold = max(threshold,0)
                        if threshold > 0:
                            text(0,3,2,0,1,"Lo Threshold",14,7)
                            text(0,3,3,1,1,str(threshold),18,7)
                            timer10 = 0
                        else:
                            text(0,3,3,0,1,"Timelapse",14,7)
                            text(0,3,3,1,1," ",18,7)
                            timer10 = time.monotonic()
                    save_config = 1

                elif g == 4 and menu == 0:
                    # Hi Threshold
                    if (h == 1 and event.button == 1) or event.button == 4:
                        threshold2 +=1
                        threshold2 = min(threshold2,255)
                        text(0,4,2,0,1,"Hi Threshold",14,7)
                        text(0,4,3,1,1,str(threshold2),18,7)
                        timer10 = 0
                          
                    else:
                        threshold2 -=1
                        threshold2 = max(threshold2,threshold + 1)
                        text(0,4,2,0,1,"Hi Threshold",14,7)
                        text(0,4,3,1,1,str(threshold2),18,7)
                        timer10 = 0
                    save_config = 1

                elif g == 2 and menu == 0:
                    # High Detection
                    if (h == 1 and event.button == 1) or event.button == 4:
                        det_high +=1
                        det_high = min(det_high,100)
                        text(0,2,3,1,1,str(det_high),18,7)
                    else:
                        det_high -=1
                        det_high = max(det_high,detection)
                        text(0,2,3,1,1,str(det_high),18,7)
                    save_config = 1
                    
                elif g == 1 and menu == -1:
                    # RECORD
                    record = 1
                    button(0,1,1)
                    text(0,1,3,0,1,"RECORD",20,0)
                    
                elif g == 8 and menu == 4 and use_gpio == 1:
                    # EXT Trigger
                    ES +=1
                    if ES > 2:
                        ES = 0
                    if ES == 0:
                        text(0,8,3,1,1,"OFF",18,7)
                    elif ES == 1:
                        text(0,8,3,1,1,"Short",18,7)
                    else:
                        text(0,8,3,1,1,"Long",18,7)
                    save_config = 1

                elif g == 8 and menu == -1:
                    # Videos or Pictures
                    zoom = 0
                    vid_pic +=1
                    if vid_pic > 1:
                        vid_pic = 0
                    if vid_pic == 0:
                        text(0,8,2,0,1,"VIDEOS",14,7)
                        vf = str(ram_frames) + " - " + str(frames)
                        text(0,8,3,1,1,vf,18,7)
                    else:
                        text(0,8,2,0,1,"PICTURES",14,7)
                        pf = str(ram_snaps) + " - " + str(snaps)
                        text(0,8,3,1,1,pf,18,7)
                    if vid_pic == 0:
                        cap_width = 1920
                        cap_height = 1080
                    else:
                        cap_width = 2592
                        cap_height = 1944
                    if vid_pic == 0:
                        xheight = int(cwidth * 0.5625)
                    else:
                        xheight = int(cwidth * 0.75)
                    if xheight > scr_height:
                        xheight = scr_height
                    if a + h_crop > cwidth:
                        a = cwidth - h_crop
                    if b + v_crop > xheight:
                        b = xheight - v_crop
                    if a - h_crop < 0:
                        a = h_crop
                    if b - v_crop < 0:
                        b = v_crop
                    a2 = int(a * (cap_width/cwidth))
                    b2 = int(b * (cap_height/xheight))
                    h_crop2 = int(h_crop * (cap_width/cwidth))
                    v_crop2 = int(v_crop * (cap_height/xheight))
                    main_menu()
                    if vid_pic == 0:
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,xheight,cwidth,scr_height))
                    pygame.display.update(0,xheight,cwidth,scr_height)
                    restart = 1
                    save_config = 1

                elif g == 9 and menu == -1:
                    # SHUTDOWN HOUR
                    if h == 1:
                        sd_hour +=1
                        if sd_hour > 23:
                            sd_hour = 0
                    if h == 0:
                        sd_hour -=1
                        if sd_hour  < 0:
                            sd_hour = 23
                    text(0,9,1,0,1,"SD Hour",14,7)
                    text(0,9,3,1,1,str(sd_hour) + ":00",14,7)
                    save_config = 1
                    
                elif g == 8 and menu == 0:
                    # ZOOM
                    zoom +=1
                    if zoom == 1:
                        button(0,8,1)
                        text(0,8,1,0,1,"Zoom",14,0)
                        preview = 0
                        button(0,0,0)
                        text(0,0,2,0,1,"Preview",14,7)
                        text(0,0,2,1,1,"Threshold",13,7)
                    else:
                        zoom = 0
                        button(0,8,0)
                        text(0,8,2,0,1,"Zoom",14,7)
                    restart = 1
                    
                elif g == 1 and menu == 1:
                    # MODE
                    restart = 1
                    if h == 1 :
                        mode +=1
                        mode = min(mode,2)
                    else:
                        mode -=1
                        mode = max(mode,0)
                    if mode == 0:
                        text(0,2,3,1,1,str(int(speed/1000)),18,7)
                    else:
                        text(0,2,0,1,1,str(int(speed/1000)),18,7)
                    text(0,1,3,1,1,modes[mode],18,7)
                    save_config = 1
                    
                elif g == 2 and menu == 1:
                    # Shutter Speed
                    if mode == 0:
                        restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        speed +=1000
                        if speed > 50000:
                            speed +=9000
                        speed = min(speed,1000000)
                    else:
                        speed -=1000
                        if speed > 50000:
                            speed -=9000
                        speed = max(speed,1)
                    if mode != 0:
                        text(0,2,0,1,1,str(int(speed/1000)),18,7)
                    else:
                        text(0,2,3,1,1,str(int(speed/1000)),18,7)
                    save_config = 1
                    
                elif g == 3 and menu == 1:
                    # GAIN
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        gain +=1
                        gain = min(gain,20)
                    else:
                        gain -=1
                        gain = max(gain,0)
                    text(0,3,3,1,1,str(gain),18,7)
                    save_config = 1
                    
                elif g == 4 and menu == 1:
                    # BRIGHTNESS
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        brightness +=1
                        brightness = min(brightness,100)
                    else:
                        brightness -=1
                        brightness = max(brightness,0)
                    text(0,4,3,1,1,str(brightness),18,7)
                    save_config = 1
                    
                elif g == 5 and menu == 1:
                    # CONTRAST
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        contrast +=1
                        contrast = min(contrast,100)
                    else:
                        contrast -=1
                        contrast = max(contrast,-100)
                    text(0,5,3,1,1,str(contrast),18,7)
                    save_config = 1

                elif g == 6 and menu == 1:
                    # EV
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        ev +=1
                        ev = min(ev,12)
                    else:
                        ev -=1
                        ev = max(ev,-12)
                    text(0,6,5,0,1,"eV",14,7)
                    text(0,6,3,1,1,str(ev),18,7)
                    save_config = 1
                    
                elif g == 7 and menu == 1:
                    # Metering
                    if h == 1:
                        meter +=1
                        meter = min(meter,len(meters)-1)
                    else:
                        meter -=1
                        meter = max(meter,0)
                    text(0,7,3,1,1,str(meters[meter]),18,7)
                    restart = 1
                    save_config = 1

                elif g == 3 and menu == 2:
                    # PRE FRAMES
                    if h == 1:
                        pre_frames +=1
                        pre_frames = min(pre_frames,100)
                    else:
                        pre_frames -=1
                        pre_frames = max(pre_frames,10)
                    text(0,3,3,1,1,str(pre_frames),18,7)
                    save_config = 1
                    
                elif g == 8 and menu == 1:
                    # SATURATION
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        saturation +=1
                        saturation = min(saturation,20)
                    else:
                        saturation -=1
                        saturation = max(saturation,0)
                    text(0,8,3,1,1,str(saturation),18,7)
                    save_config = 1
                elif g == 9 and menu == 1:
                    # SCIENTIFIC
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        scientific +=1
                        scientific = min(scientific,1)
                    else:
                        scientific -=1
                        scientific = max(scientific,0)
                    text(0,9,3,1,1,str(scientific),18,7)
                    #save_config = 1

                elif g == 2 and menu == 2:
                    # FPS
                    if (h == 1 and event.button == 1) or event.button == 4:
                        fps +=1
                        fps = min(fps,30)
                    else:
                        fps -=1
                        fps = max(fps,5)
                    pre_frames = 2 * fps
                    text(0,3,3,1,1,str(pre_frames),18,7)
                    if mode != 0:
                        text(0,2,3,1,1,str(fps),18,7)
                    else:
                        text(0,2,0,1,1,str(fps),18,7)
                    restart = 1
                    save_config = 1

                elif g == 4 and menu == 2:
                    # AWB setting
                    if (h == 1 and event.button == 1) or event.button == 4:
                        awb +=1
                        awb = min(awb,len(awbs)-1)
                    else:
                        awb -=1
                        awb = max(awb,0)
                    text(0,4,3,1,1,str(awbs[awb]),18,7)
                    if awb == 0:
                        text(0,5,3,1,1,str(red)[0:3],18,7)
                        text(0,6,3,1,1,str(blue)[0:3],18,7)
                    else:
                        text(0,5,0,1,1,str(red)[0:3],18,7)
                        text(0,6,0,1,1,str(blue)[0:3],18,7)
                    restart = 1
                    save_config = 1
                    
                elif g == 5 and menu == 2 and awb == 0:
                    # RED
                    restart = 1
                    if h == 0 or event.button == 5:
                        red -=0.1
                        red = max(red,0.1)
                    else:
                        red +=0.1
                        red = min(red,8)
                    text(0,5,3,1,1,str(red)[0:3],18,7)
                    save_config = 1
                    
                elif g == 6 and menu == 2  and awb == 0:
                    # BLUE
                    restart = 1
                    if h == 0 or event.button == 5:
                        blue -=0.1
                        blue = max(blue,0.1)
                    else:
                        blue +=0.1
                        blue = min(blue,8)
                    text(0,6,3,1,1,str(blue)[0:3],18,7)
                    save_config = 1

                elif g == 7 and menu == 2:
                    # SHARPNESS
                    restart = 1
                    if(h == 1 and event.button == 1) or event.button == 4:
                        sharpness +=1
                        sharpness = min(sharpness,40)
                    else:
                        sharpness -=1
                        sharpness = max(sharpness,0)
                    text(0,7,3,1,1,str(sharpness),18,7)
                    save_config = 1
                    
                   
                elif g == 8 and menu == 2:
                    # DENOISE
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        denoise +=1
                        denoise = min(denoise,3)
                    else:
                        denoise -=1
                        denoise = max(denoise,0)
                    text(0,8,3,1,1,str(denoises[denoise]),18,7)
                    save_config = 1

                elif g == 9 and menu == 2:
                    # QUALITY
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        quality +=1
                        quality = min(quality,100)
                    else:
                        quality -=1
                        quality = max(quality,0)
                    text(0,9,3,1,1,str(quality),18,7)
                    save_config = 1
                        
                elif g == 1 and (menu == 3 or menu == 5) and show == 1 and len(zzpics) > 0:
                    # SHOW next video / picture
                    frame = 0
                    if vid_pic == 0 and menu == 3:
                        text(0,5,0,0,1,"DEL to END",14,7)
                        text(0,4,0,0,1,"DELETE ",14,7)
                        text(0,4,0,1,1,"FRAME ",18,7)
                    if vid_pic == 0 and menu == 5:
                        text(0,4,0,0,1,"DEL to END",14,7)
                    if (h == 1 and event.button == 1) or event.button == 4:
                        q +=1
                        if q > len(zzpics)-1:
                            q = 0
                    else:
                        q -=1
                        if q < 0:
                            q = len(zzpics)-1
                    if os.path.getsize(zzpics[q]) > 0:
                        if vid_pic == 0:
                            text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),18,7)
                        else:
                            text(0,1,3,1,1,str(q+1) + " / " + str(ram_snaps + snaps),18,7)
                        if len(zzpics) > 0:
                            play = glob.glob(zzpics[q][:-10] + "*.jpg")
                            play.sort()
                            image = pygame.image.load(zzpics[q])
                            if vid_pic == 0 :
                                cropped = pygame.transform.scale(image, (cwidth,xheight))
                            else:
                                igw = image.get_width()
                                igh = image.get_height()
                                cropped = pygame.transform.scale(image, (cwidth,int(igh*(cwidth/igw))))
                            windowSurfaceObj.blit(cropped, (0, 0))
                            fontObj = pygame.font.Font(None, 30)
                            if vid_pic == 0:
                                msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,0,0))
                            else:
                                msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(ram_snaps + snaps)), False, (255,0,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,10)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            pygame.display.update()

                elif g == 6 and menu == 3 and show == 1 and (frames + ram_frames > 0 or ram_snaps > 0 or snaps > 0) and len(zzpics) > 0:
                    # delete a video or picture
                    try:
                      fontObj = pygame.font.Font(None, 70)
                      msgSurfaceObj = fontObj.render("DELETING....", False, (255,0,0))
                      msgRectobj = msgSurfaceObj.get_rect()
                      msgRectobj.topleft = (10,100)
                      windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                      pygame.display.update()
                      if zzpics[q][len(zzpics[q])-9:len(zzpics[q])-4] == "99999":
                        if os.path.getsize(zzpics[q]) > 0:
                            remove = glob.glob(zzpics[q][0:len(zzpics[q])-10] + "*.jpg")
                        for tt in range(0,len(remove)):
                            os.remove(remove[tt])
                      else:
                        if os.path.getsize(zzpics[q]) > 0:
                            os.remove(zzpics[q])
                            if zzpics[q][0:4] == "/run":
                                ram_snaps -=1
                            else:
                                snaps -=1
                    except:
                        pass
                    zzpics = []
                    rpics = []
                    if vid_pic == 0:
                        zzpics = glob.glob('/home/' + h_user[0] + '/Videos/*99999.jpg')
                        rpics = glob.glob('/run/shm/*99999.jpg')
                        frames = 0
                        ram_frames = 0
                    else:
                        zzpics = glob.glob('/home/' + h_user[0] + '/Pictures/*.jpg')
                        rpics = glob.glob('/run/shm/P*.jpg')
                        snaps = len(zzpics)
                        ram_snaps = len(rpics)
                    rpics.sort()
                    for x in range(0,len(rpics)):
                         zzpics.append(rpics[x])
                    zzpics.sort()
                    if vid_pic == 0:
                        z = ""
                        y = ""
                        for x in range(0,len(zzpics)):
                            if len(zzpics[x]) > 32:
                                if zzpics[x][16+(l_len-2):28+(l_len-2)] != z:
                                    z = zzpics[x][16+(l_len-2):28+(l_len-2)]
                                    frames +=1
                            else:
                                if zzpics[x][9:21] != y:
                                    y = zzpics[x][9:21]
                                    ram_frames +=1
                    if q > len(zzpics)-1:
                        q -=1
                    if len(zzpics) > 0:
                      try:
                        image = pygame.image.load(zzpics[q])
                        cropped = pygame.transform.scale(image, (cwidth,xheight))
                        windowSurfaceObj.blit(cropped, (0, 0))
                        fontObj = pygame.font.Font(None, 30)
                        msgSurfaceObj = fontObj.render(str(zzpics[q]), False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (10,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                      except:
                          pass
                    else:
                        show = 0
                        main_menu()
                        q = 0
                        ram_frames = 0
                        frames = 0
                        snaps = 0
                        restart = 1
                    if vid_pic == 0 and ram_frames + frames > 0 and (menu == 3 or menu == 5):
                        text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),18,7)
                    elif vid_pic == 1 and ram_snaps + snaps > 0 and (menu == 3 or menu == 5):
                        text(0,1,3,1,1,str(q+1) + " / " + str(ram_snaps + snaps),18,7)
                    elif (menu == 3 or menu == 5):
                        text(0,1,3,1,1," ",18,7)
                    vf = str(ram_frames) + " - " + str(frames)
                    pf = str(ram_snaps) + " - " + str(snaps)
                    pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,cwidth,scr_height))
                   
                        
                elif g == 7 and menu == 3:
                    # DELETE ALL
                    if event.button == 3:
                        button(0,0,0)
                        text(0,0,5,0,1,"CAPTURE",20,7)
                        fontObj = pygame.font.Font(None, 70)
                        msgSurfaceObj = fontObj.render("DELETING....", False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (10,100)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                        if vid_pic == 0:
                          try:
                            zpics = glob.glob('/run/shm/2*.jpg')
                            for xx in range(0,len(zpics)):
                                os.remove(zpics[xx])
                            ram_frames = 0
                            zpics = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                            for xx in range(0,len(zpics)):
                                os.remove(zpics[xx])
                            frames = 0
                            vf = str(ram_frames) + " - " + str(frames)
                            #zpics = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                            #for xx in range(0,len(zpics)):
                            #    os.remove(zpics[xx])
                          except:
                             pass
                        else:
                            zpics = glob.glob('/run/shm/P*.jpg')
                            for xx in range(0,len(zpics)):
                                os.remove(zpics[xx])
                            ram_snaps = 0
                            zpics = glob.glob(pic_dir + "*.jpg")
                            for xx in range(0,len(zpics)):
                                os.remove(zpics[xx])
                            snaps = 0
                            pf = str(ram_snaps) + " - " + str(snaps)
                        text(0,1,3,1,1," ",18,7)
                        menu = -1
                        Capture = old_cap
                        main_menu()
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,cwidth,scr_height))
                        show = 0
                        restart = 1

                elif g == 2 and (menu == 3 or menu == 5) and show == 1 and vid_pic == 0:
                    # PLAY VIDEO
                    text(0,2,3,0,1,"STOP",14,7)
                    text(0,2,3,1,1,"Video",14,7)
                    if menu == 3:
                        text(0,4,3,0,1,"DELETE ",14,7)
                        text(0,4,3,1,1,"FRAME ",18,7)
                        text(0,5,3,0,1,"DEL to END ",14,7)
                    else:
                        text(0,4,3,0,1,"DEL to END",14,7)
                    step = 1
                    if h == 0:
                        step = 1
                    elif h == 1:
                        step = 10
                    play = glob.glob(zzpics[q][:-10] + "*.jpg")
                    play.sort()
                    frame = 0
                    st = 0
                    while frame < len(play) - 1 and st == 0:
                        image = pygame.image.load(play[frame])
                        image = pygame.transform.scale(image, (cwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 30)
                        msgSurfaceObj = fontObj.render(str(play[int(frame)] + " : " + str(q+1) + "/" + str(len(zzpics)) + " - " + str(frame+1) + "/" + str(len(play)-1)), False, (0,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                        for event in pygame.event.get():
                            if (event.type == MOUSEBUTTONUP):
                                mousex, mousey = event.pos
                                if mousex > cwidth:
                                   buttonx = int(mousey/bh)
                                   if buttonx == 2:
                                       st = 1
                        if st == 0:
                            frame +=step
                            if frame > len(play) - 1:
                                frame = len(play) - 1
                    if st == 0:   
                      if os.path.exists(zzpics[q][:-10] + "_99999.jpg"):
                        image = pygame.image.load(zzpics[q][:-10] + "_99999.jpg")
                      elif os.path.exists(zzpics[q][:-10] + "_00001.jpg"):
                        image = pygame.image.load(zzpics[q][:-10] + "_00001.jpg")
                      else:
                        image = pygame.image.load(zzpics[q])
                      image = pygame.transform.scale(image, (cwidth,xheight))
                      windowSurfaceObj.blit(image, (0, 0))
                      fontObj = pygame.font.Font(None, 30)
                      msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(len(zzpics))), False, (255,0,0))
                      msgRectobj = msgSurfaceObj.get_rect()
                      msgRectobj.topleft = (0,10)
                      windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                      frame = 0
                    text(0,2,2,0,1,"PLAY",14,7)
                    text(0,2,2,1,1,"Video",14,7)
                    pygame.display.update()
                    
                elif g == 3 and (menu == 3 or menu == 5) and show == 1 and vid_pic == 0:
                    # NEXT / PREVIOUS FRAME
                    play = glob.glob(zzpics[q][:-10] + "*.jpg")
                    play.sort()
                    if menu == 3:
                        text(0,5,3,0,1,"DEL to END",14,7)
                        text(0,4,3,0,1,"DELETE ",14,7)
                        text(0,4,3,1,1,"FRAME ",18,7)
                    else:
                        text(0,4,3,0,1,"DEL to END",14,7)
                    if (h == 1 and event.button == 1) or event.button == 4:
                        frame +=1
                        frame = min(frame,len(play)-2)
                        image = pygame.image.load(play[int(frame)])
                        image = pygame.transform.scale(image, (cwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 30)
                        msgSurfaceObj = fontObj.render(str(play[int(frame)] + " : " + str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame+1)) + "/" + str(len(play)-1)), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                    else:
                        frame -=1
                        frame = max(frame,0)
                        image = pygame.image.load(play[int(frame)])
                        image = pygame.transform.scale(image, (cwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 30)
                        msgSurfaceObj = fontObj.render(str(play[int(frame)] + " : " + str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame+1)) + "/" + str(len(play)-1)), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                     
                elif ((g == 5 and menu == 3) or (g == 4 and menu == 5)) and show == 1 and vid_pic == 0 and frame > 0:
                    # DELETE to End
                    if menu == 3:
                        text(0,5,3,0,1,"DELETING",14,7)
                    else:
                        text(0,4,3,0,1,"DELETING",14,7)
                    remove = glob.glob(zzpics[q][:-10] + "*.jpg")
                    remove.sort()
                    for tt in range(int(frame),len(remove)-1):
                       if remove[tt][40:45] != "99999":
                            os.remove(remove[tt])
                    play = glob.glob(zzpics[q][:-10] + "*.jpg")
                    play.sort()
                    frame = len(play)-2
                    image = pygame.image.load(play[int(frame)])
                    image = pygame.transform.scale(image, (cwidth,xheight))
                    windowSurfaceObj.blit(image, (0, 0))
                    fontObj = pygame.font.Font(None, 30)
                    msgSurfaceObj = fontObj.render(str(play[int(frame)] + " : " + str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame)+1) + "/" + str(len(play)-1)), False, (255,255,0))
                    #msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame+1)) + "/" + str(len(play))), False, (255,255,0))
                    msgRectobj = msgSurfaceObj.get_rect()
                    msgRectobj.topleft = (0,10)
                    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    if menu == 3:
                        text(0,5,0,0,1,"DEL to END",14,7)
                    else:
                        text(0,4,0,0,1,"DEL to END",14,7)
                    pygame.display.update()

                elif g == 4 and menu == 3 and show == 1 and vid_pic == 0:
                    # DELETE FRAME
                    remove = glob.glob(zzpics[q][:-10] + "*.jpg")
                    remove.sort()
                    if remove[int(frame)][40:45] != "99999":
                        os.remove(remove[int(frame)])
                    play = glob.glob(zzpics[q][:-10] + "*.jpg")
                    play.sort()
                    if len(play) > 1:
                        if frame > len(play) - 2:
                            frame = len(play) - 2
                        image = pygame.image.load(play[int(frame)])
                        image = pygame.transform.scale(image, (cwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 30)
                        msgSurfaceObj = fontObj.render(str(play[int(frame)] + " : " + str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame+1)) + "/" + str(len(play)-1)), False, (255,255,0))
                        #msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame+1)) + "/" + str(len(play))), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                    else:
                        os.remove(play[0])
                        # read list of existing RAM Video Files
                        Videos = glob.glob('/run/shm/2*.jpg')
                        Videos.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(Videos)):
                            if Videos[x][9 + (l_len-2):21 + (l_len-2)] != z:
                                z = Videos[x][9:21]
                                outvids.append(z)
                        ram_frames = len(outvids)
                        # read list of existing SD Card Video Files
                        if trace == 1:
                            print ("Step 11 READ SD FILES")
                        Videos = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                        Videos.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(Videos)):
                            if Videos[x][16+(l_len-2):28+(l_len-2)] != z:
                                z = Videos[x][16+(l_len-2):28+(l_len-2)]
                                outvids.append(z)
                        frames = len(outvids)
                        vf = str(ram_frames) + " - " + str(frames)
                        main_menu()
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,cwidth,scr_height))
                        show = 0
                        restart = 1

                elif g == 8 and menu == 3 and len(zzpics) > 0:
                    # SHOW ALL videos / pictures
                    frame = 0
                    if vid_pic == 0 and menu == 3:
                        text(0,5,0,0,1,"DEL to END",14,7)
                        text(0,4,0,0,1,"DELETE ",14,7)
                        text(0,4,0,1,1,"FRAME ",18,7)
                    if vid_pic == 0 and menu == 5:
                        text(0,4,0,0,1,"DEL to END",14,7)
                    text(0,8,2,0,1,"STOP",14,7)
                    text(0,8,2,1,1,"     ",14,7)
                    st = 0
                    while st == 0:
                        for q in range (0,len(zzpics)):
                            for event in pygame.event.get():
                                if (event.type == MOUSEBUTTONUP):
                                    mousex, mousey = event.pos
                                    if mousex > cwidth:
                                        buttonx = int(mousey/bh)
                                        if buttonx == 8:
                                            st = 1
                            
                            if os.path.getsize(zzpics[q]) > 0 and st == 0:
                                if vid_pic == 0:
                                    text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),18,7)
                                else:
                                   text(0,1,3,1,1,str(q+1) + " / " + str(ram_snaps + snaps),18,7)
                                if len(zzpics) > 0:
                                    image = pygame.image.load(zzpics[q])
                                    if vid_pic == 0 :
                                        cropped = pygame.transform.scale(image, (cwidth,xheight))
                                    else:
                                        igw = image.get_width()
                                        igh = image.get_height()
                                        cropped = pygame.transform.scale(image, (cwidth,int(igh*(cwidth/igw))))
                                    windowSurfaceObj.blit(cropped, (0, 0))
                                    fontObj = pygame.font.Font(None, 30)
                                    if vid_pic == 0:
                                        msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,0,0))
                                    else:
                                        msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(ram_snaps + snaps)), False, (255,0,0))
                                    msgRectobj = msgSurfaceObj.get_rect()
                                    msgRectobj.topleft = (10,10)
                                    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                                    pygame.display.update()
                                    time.sleep(0.5)
                    text(0,8,2,0,1,"SHOW ALL",14,7)
                    if vid_pic == 0:
                        text(0,8,2,1,1,"Videos",14,7)
                    else:
                        text(0,8,2,1,1,"Pictures",14,7)

                    
                elif g == 5 and menu == 0:
                    # H CROP
                    if (h == 1 and event.button == 1) or event.button == 4:
                        h_crop +=10
                        h_crop = min(h_crop,180)
                        h_crop2 = int(h_crop * (cap_width/cwidth))
                        if a-h_crop < 1 or b-v_crop < 1 or a+h_crop > cwidth or b+v_crop > int(cwidth/(cap_width/cap_height)):
                            h_crop -=10
                            new_crop = 0
                            new_mask = 0
                        text(0,5,3,1,1,str(h_crop),18,7)
                    else:
                        h_crop -=10
                        h_crop = max(h_crop,3)
                        h_crop2 = int(h_crop * (cap_width/cwidth))
                        text(0,5,3,1,1,str(h_crop),18,7)
                    save_config = 1
                    
                elif g == 6 and menu == 0:
                    # V CROP
                    if (h == 1 and event.button == 1) or event.button == 4:
                        v_crop +=10
                        v_crop = min(v_crop,180)
                        if a-h_crop < 1 or b-v_crop < 1 or a+h_crop > cwidth or b+v_crop > int(cwidth/(cap_width/cap_height)):
                            v_crop -=10
                        v_crop2 = int(v_crop * (cap_height/cheight))
                        text(0,6,3,1,1,str(v_crop),18,7)
                    else:
                        v_crop -=10
                        v_crop = max(v_crop,3)
                        v_crop2 = int(v_crop * (cap_height/cheight))
                        text(0,6,3,1,1,str(v_crop),18,7)
                    save_config = 1
                    
                elif g == 7 and menu == 0:
                    # INTERVAL
                    if (h == 1 and event.button == 1) or event.button == 4:
                        interval +=1
                        interval = min(interval,180)
                    else:
                        interval -=1
                        interval = max(interval,0)
                    text(0,7,3,1,1,str(interval),18,7)
                    save_config = 1
                    
                elif g == 1 and menu == 2:
                    # VIDEO LENGTH
                    if (h == 0 and event.button == 1) or event.button == 5:
                        v_length -=1000
                        v_length = max(v_length,3000)
                    else:
                        v_length +=1000
                        v_length = min(v_length,100000)
                    text(0,1,3,1,1,str(v_length/1000),18,7)
                    save_config = 1

                elif g == 0 and menu == 2:
                    # VIDEO FORMAT
                    restart = 1
                    if (h == 0 and event.button == 1) or event.button == 5:
                        vformat -=1
                        vformat = max(vformat,0)
                    else:
                        vformat += 1
                        vformat = min(vformat,len(vwidths)-1)
                    cap_width = vwidths[vformat]
                    cap_height = vheights[vformat]
                    text(0,0,3,1,1,str(vwidths[vformat]) + "x" + str(vheights[vformat]),18,7)
                    save_config = 1
                    restart = 1
                    
                elif g == 0 and menu == 1:
                    # COLOUR FILTER
                    if (h == 0 and event.button == 1) or event.button == 5:
                        col_filter -=1
                        col_filter = max(col_filter,0)
                    else:
                        col_filter +=1
                        col_filter = min(col_filter,3)
                    text(0,0,3,1,1,str(col_filters[col_filter]),18,7)
                    save_config = 1
                    if col_filter < 3:
                        col_timer = time.monotonic()
                    else:
                        col_timer = 0

                elif g == 9 and menu == 0:
                    # NOISE REDUCTION
                    if (h == 0 and event.button == 1) or event.button == 5:
                        nr -=1
                        nr = max(nr,0)
                    else:
                        nr += 1
                        nr = min(nr,2)
                    text(0,9,3,1,1,str(noise_filters[nr]),18,7)
                    save_config = 1

                elif g == 1 and menu == 4 :
                    # AUTO LIMIT
                    if (h == 0 and event.button == 1) or event.button == 5:
                        auto_limit -=1
                        auto_limit = max(auto_limit,0)
                    else:
                        auto_limit += 1
                        auto_limit = min(auto_limit,60)
                    text(0,1,3,1,1,str(auto_limit),18,7)
                    save_config = 1
                    
                elif g == 2 and menu == 4 :
                    # RAM LIMIT
                    if (h == 0 and event.button == 1) or event.button == 5:
                        ram_limit -=10
                        ram_limit = max(ram_limit,10)
                    else:
                        ram_limit += 10
                        ram_limit = min(ram_limit,int(sfreeram) - 100)
                    text(0,2,3,1,1,str(int(ram_limit)),18,7)
                    save_config = 1
                    
                elif g == 5 and menu == 4 and use_gpio == 1:
                    # FAN TIME
                    if (h == 0 and event.button == 1) or event.button == 5:
                        fan_time -=1
                        fan_time = max(fan_time,2)
                    else:
                        fan_time += 1
                        fan_time = min(fan_time,60)
                    text(0,5,3,1,1,str(fan_time),18,7)
                    save_config = 1
                    
                elif g == 6 and menu == 4 and use_gpio == 1:
                    # FAN LOW
                    if (h == 0 and event.button == 1) or event.button == 5:
                        fan_low -=1
                        fan_low = max(fan_low,30)
                    else:
                        fan_low += 1
                        fan_low = min(fan_low,fan_high - 1)
                    text(0,6,3,1,1,str(fan_low),18,7)
                    save_config = 1

                elif g == 7 and menu == 4 and use_gpio == 1:
                    # FAN HIGH
                    if (h == 0 and event.button == 1) or event.button == 5:
                        fan_high -=1
                        fan_high = max(fan_high,fan_low + 1)
                    else:
                        fan_high +=1
                        fan_high = min(fan_high,80)
                    text(0,7,3,1,1,str(fan_high),18,7)
                    save_config = 1

                elif g == 3 and menu == 4:
                    # v3 camera focus mode
                    if (h == 0 and event.button == 1) or event.button == 5:
                        v3_f_mode -=1
                        v3_f_mode = max(v3_f_mode,0)
                    else:
                        v3_f_mode +=1
                        v3_f_mode = min(v3_f_mode,2)
                    text(0,3,3,1,1,v3_f_modes[v3_f_mode],18,7)
                    if v3_f_mode == 1:
                                    if os.path.exists("ctrls.txt"):
                                        os.remove("ctrls.txt")
                                    os.system("v4l2-ctl -d /dev/v4l-subdev1 --list-ctrls >> ctrls.txt")
                                    restart = 1
                                    time.sleep(0.25)
                                    ctrlstxt = []
                                    with open("ctrls.txt", "r") as file:
                                        line = file.readline()
                                        while line:
                                            ctrlstxt.append(line.strip())
                                            line = file.readline()
                                    foc_ctrl = ctrlstxt[3].split('value=')
                                    v3_focus = int(foc_ctrl[1])
                                    text(0,4,2,0,1,"Focus Manual",14,7)
                                    text(0,4,3,1,1,str(v3_focus),18,7)
                    else:
                        text(0,4,2,0,1," ",14,7)
                        text(0,4,3,1,1," ",18,7)
                    restart = 1
                    save_config = 1

                elif g == 4 and menu == 4 and v3_f_mode == 1:
                    # v3 camera focus manual
                    if (h == 0 and event.button == 1) or event.button == 5:
                        v3_focus -=1
                        v3_focus = max(v3_focus,100)
                    else:
                        v3_focus +=1
                        v3_focus = min(v3_focus,1000)
                    os.system("v4l2-ctl -d /dev/v4l-subdev1 -c focus_absolute=" + str(int(v3_focus)))
                    text(0,4,3,1,1,str(v3_focus),18,7)
                    
                elif g == 5 and menu == 5 and show == 1 and ((len(USB_Files) > 0 and movtousb == 1) or movtousb == 0):
                  # MAKE A MP4
                  Sideos = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                  Rideos = glob.glob('/run/shm/2*.jpg')
                  for x in range(0,len(Rideos)-1):
                      Sideos.append(Rideos[x])
                  Sideos.sort()
                  if len(Sideos) > 0:
                    os.killpg(p.pid, signal.SIGTERM)
                    restart = 1
                    frame = 0
                    text(0,5,3,0,1,"MAKING",14,7)
                    text(0,5,3,1,1,"MP4",14,7)
                    pygame.display.update()
                    z = ""
                    y = ""
                    outvids = []
                    for x in range(0,len(Sideos)):
                        if len(Sideos[x]) > 32:
                            if Sideos[x][16+(l_len-2):28+(l_len-2)] != z:
                                z = Sideos[x][16+(l_len-2):28+(l_len-2)]
                                outvids.append(z)
                        else:
                            if Sideos[x][9:21] != y:
                                y = Sideos[x][9:21]
                                outvids.append(y)
                    year = 2000 + int(outvids[q][0:2])
                    mths = int(outvids[q][2:4])
                    days = int(outvids[q][4:6])
                    hour = int(outvids[q][6:8])
                    mins = int(outvids[q][8:10])
                    secs = int(outvids[q][10:12])
                    if movtousb == 1:
                        new_dir = '/media/' + h_user[0] + "/" + USB_Files[0] + "/Videos"
                    else:
                        new_dir = '/home/' + h_user[0] + "/Videos"
                    if not os.path.exists(new_dir):
                        os.system('mkdir ' + "/" + new_dir)
                    logfile = new_dir + "/" + str(outvids[q]) + ".mp4"
                    out = cv2.VideoWriter(logfile,cv2.VideoWriter_fourcc(*'H264'),fps, (cap_width,cap_height))
                    zpics = glob.glob('/home/' + h_user[0] + '/Videos/' + outvids[q] + "*.jpg")
                    rpics = glob.glob('/run/shm/' + outvids[q] +  '*.jpg')
                    for x in range(0,len(rpics)-1):
                        zpics.append(rpics[x])
                    zpics.sort()
                    for xx in range(0,len(zpics)-1):
                        secs += 1/fps
                        if secs >= 60:
                            secs = 0
                            mins += 1
                            if mins >= 60:
                                mins = 0
                                hour +=1
                                if hour >= 24:
                                    hour = 0
                                    days +=1
                                    max_d = max_days[mths]
                                    if (year/4) - int(year/4) == 0 and mths == 2:
                                        max_d == 29
                                    if days > max_d:
                                        days = 1
                                        mths +=1
                                        if mths > 12:
                                            mths = 1
                                            year +=1
                        show_time = ("0" + str(days))[-2:] + "/" + ("0" + str(mths))[-2:] + "/" + str(year) + " " + ("0" + str(hour))[-2:] + ":" + ("0" + str(mins))[-2:] + ":" + ("0" + str(int(secs)))[-2:]
                        img = cv2.imread(zpics[xx])
                        if zpics[xx][40:45] != "99999":
                            cv2.putText(img,show_time,(int(cap_width/2.5),1020),cv2.FONT_HERSHEY_COMPLEX_SMALL,2,(255,255,255))
                            out.write(img)
                        #os.remove(zpics[xx])
                    out.release()
                    if len(outvids) > 0:
                        if os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_99999.jpg"):
                            image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_99999.jpg")
                        elif os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_00001.jpg"):
                            image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_00001.jpg")
                        elif os.path.exists('/run/shm/' + outvids[q] + "_99999.jpg"):
                            image = pygame.image.load('/run/shm/' + outvids[q] + "_99999.jpg")
                        elif os.path.exists('/run/shm/' + outvids[q] + "_00001.jpg"):
                            image = pygame.image.load('/run/shm/' + outvids[q] + "_00001.jpg")
                        image = pygame.transform.scale(image, (cwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 30)
                        msgSurfaceObj = fontObj.render(str(outvids[q] + " " + str(q+1) + "/" + str(ram_frames + frames)), False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    else:
                        msgSurfaceObj = fontObj.render("No Videos Found", False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (100,cheight/2)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    text(0,5,2,0,1,"MAKE A",14,7)
                    text(0,5,2,1,1,"MP4",14,7)
                    USB_Files  = (os.listdir("/media/" + h_user[0]))
                    Mideos = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                    if len(USB_Files) > 0 and movtousb == 0 and len(Mideos) > 0:
                        text(0,8,2,0,1,"MOVE MP4s",14,7)
                        text(0,8,2,1,1,"to USB",14,7)
                    else:
                        text(0,8,0,0,1,"MOVE MP4s",14,7)
                        text(0,8,0,1,1,"to USB",14,7)
                    pygame.display.update()

               
                elif g == 6 and menu == 5 and show == 1 and ((len(USB_Files) > 0 and movtousb == 1) or movtousb == 0):
                 # MAKE ALL MP4
                 Sideos = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                 Rideos = glob.glob('/run/shm/2*.jpg')
                 for x in range(0,len(Rideos)-1):
                     Sideos.append(Rideos[x])
                 Sideos.sort()    
                 if len(Sideos) > 0:
                  os.killpg(p.pid, signal.SIGTERM)
                  restart = 1
                  frame = 0
                  text(0,6,3,0,1,"MAKING",14,7)
                  text(0,6,3,1,1,"MP4s",14,7)
                  pygame.display.update()
                  outvids = []
                  z = ""
                  y = ""
                  for x in range(0,len(Sideos)):
                      if len(Sideos[x]) > 32:
                          if Sideos[x][16+(l_len-2):28+(l_len-2)] != z:
                              z = Sideos[x][16+(l_len-2):28+(l_len-2)]
                              outvids.append(z)
                      else:
                          if Sideos[x][9:21] != y:
                              y = Sideos[x][9:21]
                              outvids.append(y)
                  for w in range(0,len(outvids)):
                    if os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[w] + "_99999.jpg"):
                        image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[w] + "_99999.jpg")
                    elif os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[w] + "_00001.jpg"):
                        image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[w] + "_00001.jpg")
                    elif os.path.exists('/run/shm/' + outvids[w] + "_99999.jpg"):
                        image = pygame.image.load('/run/shm/' + outvids[w] + "_99999.jpg")
                    elif os.path.exists('/run/shm/' + outvids[w] + "_00001.jpg"):
                        image = pygame.image.load('/run/shm/' + outvids[w] + "_00001.jpg")
                    image = pygame.transform.scale(image, (cwidth,xheight))
                    windowSurfaceObj.blit(image, (0, 0))
                    fontObj = pygame.font.Font(None, 30)
                    msgSurfaceObj = fontObj.render(str(outvids[w] + " " + str(w+1) + "/" + str(len(outvids))), False, (255,0,0))
                    msgRectobj = msgSurfaceObj.get_rect()
                    msgRectobj.topleft = (0,10)
                    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    text(0,1,3,1,1,str(w+1) + " / " + str(ram_frames + frames),18,7)
                    pygame.display.update()
                    year = 2000 + int(outvids[w][0:2])
                    mths = int(outvids[w][2:4])
                    days = int(outvids[w][4:6])
                    hour = int(outvids[w][6:8])
                    mins = int(outvids[w][8:10])
                    secs = int(outvids[w][10:12])
                    if movtousb == 1:
                        new_dir = '/media/' + h_user[0] + "/" + USB_Files[0] + "/Videos"
                    else:
                        new_dir = '/home/' + h_user[0] + "/Videos"
                    if not os.path.exists(new_dir):
                        os.system('mkdir ' + "/" + new_dir)
                    logfile = new_dir + "/" + str(outvids[w]) + ".mp4"
                    out = cv2.VideoWriter(logfile,cv2.VideoWriter_fourcc(*'H264'),fps, (1920,1080))
                    zpics = glob.glob('/home/' + h_user[0] + '/Videos/' + outvids[w] + "*.jpg")
                    rpics = glob.glob('/run/shm/' + outvids[w] +  '*.jpg')
                    for x in range(0,len(rpics)-1):
                        zpics.append(rpics[x])
                    zpics.sort()
                    for xx in range(0,len(zpics)-1):
                        secs += 1/fps
                        if secs >= 60:
                            secs = 0
                            mins += 1
                            if mins >= 60:
                                mins = 0
                                hour +=1
                                if hour >= 24:
                                    hour = 0
                                    days +=1
                                    max_d = max_days[mths]
                                    if (year/4) - int(year/4) == 0 and mths == 2:
                                        max_d == 29
                                    if days > max_d:
                                        days = 1
                                        mths +=1
                                        if mths > 12:
                                            mths = 1
                                            year +=1
                        show_time = ("0" + str(days))[-2:] + "/" + ("0" + str(mths))[-2:] + "/" + str(year) + " " + ("0" + str(hour))[-2:] + ":" + ("0" + str(mins))[-2:] + ":" + ("0" + str(int(secs)))[-2:]
                        img = cv2.imread(zpics[xx])
                        if zpics[xx][40:45] != "99999":
                            cv2.putText(img,show_time,(int(cap_width/2.5),1020),cv2.FONT_HERSHEY_COMPLEX_SMALL,2,(255,255,255))
                            out.write(img)
                        #os.remove(zpics[xx])
                    out.release()
                    #if os.path.exists('/home/pi/Videos/' + outvids[w] + "_99999.jpg"):
                    #    os.remove('/home/pi/Videos/' + outvids[w] + "_99999.jpg")
                  Videos = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                  Videos.sort()
                  outvids = []
                  z = ""
                  for x in range(0,len(Videos)):
                      if Videos[x][16+(l_len-2):28+(l_len-2)] != z:
                          z = Videos[x][16+(l_len-2):28+(l_len-2)]
                          outvids.append(z)
                  w = 0
                  if len(outvids) > 0:
                        if os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_99999.jpg"):
                            image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_99999.jpg")
                        elif os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_00001.jpg"):
                            image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_00001.jpg")
                        elif os.path.exists('/run/shm/' + outvids[q] + "_99999.jpg"):
                            image = pygame.image.load('/run/shm/' + outvids[q] + "_99999.jpg")
                        elif os.path.exists('/run/shm/' + outvids[q] + "_00001.jpg"):
                            image = pygame.image.load('/run/shm/' + outvids[q] + "_00001.jpg")
                        image = pygame.transform.scale(image, (cwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 30)
                        msgSurfaceObj = fontObj.render(str(outvids[q] + " " + str(q+1) + "/" + str(ram_frames + frames)), False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                  else:
                        msgSurfaceObj = fontObj.render("No Videos Found", False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (100,cheight/2)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                  text(0,6,2,0,1,"MAKE ALL",14,7)
                  text(0,6,2,1,1,"MP4",14,7)
                  text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),18,7)
                  USB_Files  = (os.listdir("/media/" + h_user[0]))
                  Mideos = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                  if len(USB_Files) > 0 and movtousb == 0 and len(Mideos) > 0:
                      text(0,8,2,0,1,"MOVE MP4s",14,7)
                      text(0,8,2,1,1,"to USB",14,7)
                  else:
                      text(0,8,0,0,1,"MOVE MP4s",14,7)
                      text(0,8,0,1,1,"to USB",14,7)
                  pygame.display.update()

                elif g == 7 and menu == 5 and show == 1 and ((len(USB_Files) > 0 and movtousb == 1) or movtousb == 0):
                 # MAKE FULL MP4
                 Sideos = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                 Rideos = glob.glob('/run/shm/2*.jpg')
                 for x in range(0,len(Rideos)-1):
                     Sideos.append(Rideos[x])
                 Sideos.sort()    
                 if len(Sideos) > 0:
                  os.killpg(p.pid, signal.SIGTERM)
                  restart = 1
                  frame = 0
                  text(0,7,3,0,1,"MAKING FULL",14,7)
                  text(0,7,3,1,1,"MP4",14,7)
                  pygame.display.update()
                  outvids = []
                  z = ""
                  y = ""
                  for x in range(0,len(Sideos)):
                      if len(Sideos[x]) > 32:
                          if Sideos[x][16+(l_len-2):28+(l_len-2)] != z:
                              z = Sideos[x][16+(l_len-2):28+(l_len-2)]
                              outvids.append(z)
                      else:
                          if Sideos[x][9:21] != y:
                              y = Sideos[x][9:21]
                              outvids.append(y)
                  if movtousb == 1:
                      new_dir = '/media/' + h_user[0] + "/" + USB_Files[0] + "/Videos"
                  else:
                      new_dir = '/home/' + h_user[0] + "/Videos"
                  if not os.path.exists(new_dir):
                      os.system('mkdir ' + "/" + new_dir)
                  logfile = new_dir + "/" + str(outvids[0]) + ".mp4"
                  out = cv2.VideoWriter(logfile,cv2.VideoWriter_fourcc(*'H264'),fps, (1920,1080))
                  for w in range(0,len(outvids)):
                    if os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[w] + "_99999.jpg"):
                        image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[w] + "_99999.jpg")
                    elif os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[w] + "_00001.jpg"):
                        image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[w] + "_00001.jpg")
                    elif os.path.exists('/run/shm/' + outvids[w] + "_99999.jpg"):
                        image = pygame.image.load('/run/shm/' + outvids[w] + "_99999.jpg")
                    elif os.path.exists('/run/shm/' + outvids[w] + "_00001.jpg"):
                        image = pygame.image.load('/run/shm/' + outvids[w] + "_00001.jpg")
                    image = pygame.transform.scale(image, (cwidth,xheight))
                    windowSurfaceObj.blit(image, (0, 0))
                    fontObj = pygame.font.Font(None, 30)
                    msgSurfaceObj = fontObj.render(str(outvids[w] + " " + str(w+1) + "/" + str(len(outvids))), False, (255,0,0))
                    msgRectobj = msgSurfaceObj.get_rect()
                    msgRectobj.topleft = (0,10)
                    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    text(0,1,3,1,1,str(w+1) + " / " + str(ram_frames + frames),18,7)
                    pygame.display.update()
                    year = 2000 + int(outvids[w][0:2])
                    mths = int(outvids[w][2:4])
                    days = int(outvids[w][4:6])
                    hour = int(outvids[w][6:8])
                    mins = int(outvids[w][8:10])
                    secs = int(outvids[w][10:12])
                    zpics = glob.glob('/home/' + h_user[0] + '/Videos/' + outvids[w] + "*.jpg")
                    rpics = glob.glob('/run/shm/' + outvids[w] +  '*.jpg')
                    for x in range(0,len(rpics)-1):
                        zpics.append(rpics[x])
                    zpics.sort()
                    for xx in range(0,len(zpics)-1):
                        secs += 1/fps
                        if secs >= 60:
                            secs = 0
                            mins += 1
                            if mins >= 60:
                                mins = 0
                                hour +=1
                                if hour >= 24:
                                    hour = 0
                                    days +=1
                                    max_d = max_days[mths]
                                    if (year/4) - int(year/4) == 0 and mths == 2:
                                        max_d == 29
                                    if days > max_d:
                                        days = 1
                                        mths +=1
                                        if mths > 12:
                                            mths = 1
                                            year +=1
                        show_time = ("0" + str(days))[-2:] + "/" + ("0" + str(mths))[-2:] + "/" + str(year) + " " + ("0" + str(hour))[-2:] + ":" + ("0" + str(mins))[-2:] + ":" + ("0" + str(int(secs)))[-2:]
                        img = cv2.imread(zpics[xx])
                        if zpics[xx][40:45] != "99999":
                            cv2.putText(img,show_time,(int(cap_width/2.5),1020),cv2.FONT_HERSHEY_COMPLEX_SMALL,2,(255,255,255))
                            out.write(img)
                        #os.remove(zpics[xx])
                    if movtousb == 1 and os.path.exists('/media/' + h_user[0] + '/' + USB_Files[0] + "/Videos/" + outvids[w] + "_99999.jpg"):
                        os.remove('/media/' + h_user[0] + '/' + USB_Files[0] + "/Videos/" + outvids[w] + "_99999.jpg")
                  out.release()
                  #if os.path.exists('/home/pi/Videos/' + outvids[w] + "_99999.jpg"):
                  #      os.remove('/home/pi/Videos/' + outvids[w] + "_99999.jpg")
                  #if os.path.exists('/run/shm/' + outvids[w] + "_99999.jpg"):
                  #      os.remove('/run/shm/Videos/' + outvids[w] + "_99999.jpg")
                  Videos = glob.glob('/home/' + h_user[0] + '/Videos/*.jpg')
                  Videos.sort()
                  outvids = []
                  z = ""
                  for x in range(0,len(Videos)):
                      if Videos[x][16+(l_len-2):28+(l_len-2)] != z:
                          z = Videos[x][16+(l_len-2):28+(l_len-2)]
                          outvids.append(z)
                  w = 0
                  if len(outvids) > 0:
                        if os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_99999.jpg"):
                           image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_99999.jpg")
                        elif os.path.exists('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_00001.jpg"):
                           image = pygame.image.load('/home/' + h_user[0] + '/Videos/' + outvids[q] + "_00001.jpg")
                        elif os.path.exists('/run/shm/' + outvids[q] + "_99999.jpg"):
                           image = pygame.image.load('/run/shm/' + outvids[q] + "_99999.jpg")
                        elif os.path.exists('/run/shm/' + outvids[q] + "_00001.jpg"):
                           image = pygame.image.load('/run/shm/' + outvids[q] + "_00001.jpg")
                        image = pygame.transform.scale(image, (cwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 30)
                        msgSurfaceObj = fontObj.render(str(outvids[0] + " " + str(q+1) + "/" + str(ram_frames + frames)), False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                  else:
                        msgSurfaceObj = fontObj.render("No Videos Found", False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (100,cheight/2)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                  text(0,7,2,0,1,"MAKE FULL",14,7)
                  text(0,7,2,1,1,"MP4",14,7)
                  text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),18,7)
                  Capture = old_cap
                  main_menu()
                  pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,cwidth,scr_height))
                  show = 0
                  restart = 1
                  USB_Files  = (os.listdir("/media/" + h_user[0]))
                  Mideos = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                  #if len(USB_Files) > 0 and movtousb == 0 and len(Mideos) > 0:
                  #    text(0,8,2,0,1,"MOVE MP4s",14,7)
                  #    text(0,8,2,1,1,"to USB",14,7)
                  #else:
                  #    text(0,8,0,0,1,"MOVE MP4s",14,7)
                  #    text(0,8,0,1,1,"to USB",14,7)
                  pygame.display.update()

                elif menu == 5 and g == 8:
                    #move MP4 to usb
                    USB_Files  = []
                    USB_Files  = (os.listdir("/media/" + h_user[0]))
                    if len(USB_Files) > 0:
                        text(0,8,3,0,1,"MOVING",14,7)
                        text(0,8,3,1,1,"MP4s",14,7)
                        spics = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                        spics.sort()
                        for xx in range(0,len(spics)):
                            movi = spics[xx].split("/")
                            if not os.path.exists('/media/' + h_user[0] + "/" + USB_Files[0] + "/" + movi[4]):
                                shutil.move(spics[xx],'/media/' + h_user[0] + "/" + USB_Files[0] + "/")
                        spics = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                        text(0,8,0,0,1,"MOVE MP4s",14,7)
                        text(0,8,0,1,1,"to USB",14,7)
                  
                elif (menu == -1 and g > 1 and g < 9) or (menu == -1 and g == 10) or (menu != -1 and g == 10):
                    # MENUS
                    # check for usb_stick
                    USB_Files  = []
                    USB_Files  = (os.listdir("/media/" + h_user[0] + "/"))
                    if show == 1:
                        show = 0
                        restart = 1
                    pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,cwidth,scr_height))
                    
                    if g == 2:
                        menu = 0
                        old_capture = Capture
                        Capture = 0
                        for d in range(0,10):
                            button(0,d,0)
                        if threshold > 0:
                            text(0,3,2,0,1,"Lo Threshold",14,7)
                            text(0,3,3,1,1,str(threshold),18,7)
                        else:
                            text(0,3,3,0,1,"Timelapse",14,7)
                        text(0,2,2,0,1,"Hi Detect %",14,7)
                        text(0,2,3,1,1,str(det_high),18,7)
                        text(0,1,2,0,1,"Low Detect %",14,7)
                        text(0,1,3,1,1,str(detection),18,7)
                        if preview == 1:
                            button(0,0,1)
                            text(0,0,1,0,1,"Preview",14,0)
                            text(0,0,1,1,1,"Threshold",13,0)
                        else:
                            button(0,0,0)
                            text(0,0,2,0,1,"Preview",14,7)
                            text(0,0,2,1,1,"Threshold",13,7)
                        text(0,4,2,0,1,"Hi Threshold",14,7)
                        text(0,4,3,1,1,str(threshold2),18,7)
                        text(0,5,2,0,1,"H_Crop",14,7)
                        text(0,5,3,1,1,str(h_crop),18,7)
                        text(0,6,2,0,1,"V_Crop",14,7)
                        text(0,6,3,1,1,str(v_crop),18,7)
                        text(0,7,2,0,1,"Interval",14,7)
                        text(0,7,3,1,1,str(interval),18,7)
                        if zoom == 0:
                            button(0,8,0)
                            text(0,8,2,0,1,"Zoom",14,7)
                        else:
                            button(0,8,1)
                            text(0,8,1,0,1,"Zoom",14,0)
                        text(0,9,2,0,1,"Noise Red'n",14,7)
                        text(0,9,3,1,1,str(noise_filters[nr]),18,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)

                    if g == 3:
                        menu = 1
                        old_capture = Capture
                        Capture = 0
                        for d in range(0,10):
                            button(0,d,0)
                        text(0,0,2,0,1,"C Filter",14,7)
                        text(0,0,3,1,1,str(col_filters[col_filter]),18,7)
                        text(0,7,5,0,1,"Meter",15,7)
                        text(0,7,3,1,1,meters[meter],18,7)
                        text(0,1,5,0,1,"Mode",14,7)
                        text(0,1,3,1,1,modes[mode],18,7)
                        text(0,2,5,0,1,"Shutter mS",14,7)
                        if mode == 0:
                            text(0,2,3,1,1,str(int(speed/1000)),18,7)
                        else:
                            text(0,2,0,1,1,str(int(speed/1000)),18,7)
                        text(0,3,5,0,1,"gain",14,7)
                        text(0,3,3,1,1,str(gain),18,7)
                        text(0,4,5,0,1,"Brightness",14,7)
                        text(0,4,3,1,1,str(brightness),18,7)
                        text(0,5,5,0,1,"Contrast",14,7)
                        text(0,5,3,1,1,str(contrast),18,7)
                        text(0,6,5,0,1,"eV",14,7)
                        text(0,6,3,1,1,str(ev),18,7)
                        text(0,7,5,0,1,"Metering",14,7)
                        text(0,7,3,1,1,str(meters[meter]),18,7)
                        text(0,8,5,0,1,"Saturation",14,7)
                        text(0,8,3,1,1,str(saturation),18,7)
                        text(0,9,5,0,1,"Scientific",14,7)
                        text(0,9,3,1,1,str(scientific),18,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)

                    if g == 4:
                        menu = 2
                        for d in range(0,10):
                            button(0,d,0)
                        text(0,0,2,0,1,"V Format",14,7)
                        text(0,0,3,1,1,str(vwidths[vformat]) + "x" + str(vheights[vformat]),18,7)
                        text(0,4,5,0,1,"AWB",14,7)
                        text(0,4,3,1,1,str(awbs[awb]),18,7)
                        text(0,2,5,0,1,"fps",14,7)
                        if mode == 0:
                            text(0,2,0,1,1,str(fps),18,7)
                        else:
                            text(0,2,3,1,1,str(fps),18,7)
                        text(0,5,5,0,1,"Red",14,7)
                        text(0,6,5,0,1,"Blue",14,7)
                        if awb == 0:
                            text(0,5,3,1,1,str(red)[0:3],18,7)
                            text(0,6,3,1,1,str(blue)[0:3],18,7)
                        else:
                            text(0,5,0,1,1,str(red)[0:3],18,7)
                            text(0,6,0,1,1,str(blue)[0:3],18,7)
                        text(0,7,5,0,1,"Sharpness",14,7)
                        text(0,7,3,1,1,str(sharpness),18,7)
                        text(0,3,2,0,1,"V Pre-Frames",14,7)
                        text(0,3,3,1,1,str(pre_frames),18,7)
                        text(0,8,5,0,1,"Denoise",14,7)
                        text(0,8,3,1,1,str(denoises[denoise]),18,7)
                        text(0,9,5,0,1,"Quality",14,7)
                        text(0,9,3,1,1,str(quality),18,7)
                        text(0,1,2,0,1,"V_length",14,7)
                        text(0,1,3,1,1,str(v_length/1000),18,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)
                        
                    if g == 6 and (((ram_frames > 0 or frames > 0) and vid_pic == 0) or ((ram_snaps > 0 or snaps > 0) and vid_pic == 1)):
                        menu = 3
                        for d in range(0,10):
                            button(0,d,0)
                        show = 1
                        frame = 0
                        old_cap = Capture
                        Capture = 0
                        zzpics = []
                        rpics = []
                        if vid_pic == 0:
                            zzpics = glob.glob('/home/' + h_user[0] + '/Videos/*99999.jpg')
                            rpics = glob.glob('/run/shm/*99999.jpg')
                            frames = 0
                            ram_frames = 0
                        if vid_pic == 1:
                            zzpics = glob.glob('/home/' + h_user[0] + '/Pictures/*.jpg')
                            rpics = glob.glob('/run/shm/P*.jpg')
                            snaps = len(zzpics)
                            ram_snaps = len(rpics)
                        rpics.sort()
                        for x in range(0,len(rpics)):
                             zzpics.append(rpics[x])
                        zzpics.sort()
                        if vid_pic == 0:
                            z = ""
                            y = ""
                            for x in range(0,len(zzpics)):
                                if len(zzpics[x]) > 32:
                                    if zzpics[x][16+(l_len-2):28+(l_len-2)] != z:
                                        z = zzpics[x][16+(l_len-2):28+(l_len-2)]
                                        frames +=1
                                else:
                                    if zzpics[x][9:21] != y:
                                        y = zzpics[x][9:21]
                                        ram_frames +=1
                        q = 0
                        if len(zzpics) > 0:
                            play = glob.glob(zzpics[q][:-10] + "*.jpg")
                            play.sort()
                            image = pygame.image.load(zzpics[q])
                            if vid_pic == 0 :
                                cropped = pygame.transform.scale(image, (cwidth,xheight))
                            else:
                                igw = image.get_width()
                                igh = image.get_height()
                                cropped = pygame.transform.scale(image, (cwidth,int(igh*(cwidth/igw))))
                            windowSurfaceObj.blit(cropped, (0, 0))
                            fontObj = pygame.font.Font(None, 30)
                            if vid_pic == 0:
                                msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,0,0))
                            else:
                                msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(ram_snaps + snaps)), False, (255,0,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,10)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            if vid_pic == 0:
                                pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,xheight,cwidth,scr_height))
                            pygame.display.update()
                            if vid_pic == 0:
                                text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),18,7)
                            else:
                                text(0,1,3,1,1,str(q+1) + " / " + str(ram_snaps + snaps),18,7)
                        text(0,7,3,0,1,"DELETE",14,7)
                        if vid_pic == 0:
                            text(0,1,2,0,1,"Video",14,7)
                            text(0,2,2,0,1,"PLAY",14,7)
                            text(0,2,2,1,1,"Video",14,7)
                            text(0,3,2,0,1,"Frame",14,7)
                            text(0,4,0,0,1,"DELETE ",14,7)
                            text(0,4,0,1,1,"FRAME ",18,7)
                            text(0,5,0,0,1,"DEL to END",14,7)
                            text(0,6,3,1,1,"VIDEO ",18,7)
                            text(0,7,3,1,1,"ALL VIDS  ",14,7)
                            text(0,8,2,0,1,"SHOW ALL",14,7)
                            text(0,8,2,1,1,"Videos",14,7)
                        else:
                            text(0,1,2,0,1,"Picture",14,7)
                            text(0,6,3,1,1,"PICTURE ",18,7)
                            text(0,7,3,1,1,"ALL PICS  ",14,7)
                            text(0,8,2,0,1,"SHOW ALL",14,7)
                            text(0,8,2,1,1,"Pictures",14,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)
                        text(0,6,3,0,1,"DELETE ",14,7)
                        
                    if g == 5:
                        menu = 4
                        old_capture = Capture
                        Capture = 0
                        for d in range(0,10):
                            button(0,d,0)
                        text(0,1,2,0,1,"Auto Limit",14,7)
                        text(0,1,3,1,1,str(auto_limit),18,7)
                        text(0,2,2,0,1,"RAM Limit",14,7)
                        text(0,2,3,1,1,str(int(ram_limit)),18,7)
                        if use_gpio == 1:
                            text(0,5,2,0,1,"Fan Time",14,7)
                            text(0,5,3,1,1,str(fan_time),18,7)
                            text(0,6,2,0,1,"Fan Low",14,7)
                            text(0,6,3,1,1,str(fan_low),18,7)
                            text(0,7,2,0,1,"Fan High",14,7)
                            text(0,7,3,1,1,str(fan_high),18,7)
                            text(0,8,2,0,1,"Ext. Trigger",14,7)
                            if ES == 0:
                                text(0,8,3,1,1,"OFF",18,7)
                            elif ES == 1:
                                text(0,8,3,1,1,"Short",18,7)
                            else:
                                text(0,8,3,1,1,"Long",18,7)
                            if Pi_Cam == 3:
                                text(0,3,2,0,1,"Focus",14,7)
                                text(0,3,3,1,1,v3_f_modes[v3_f_mode],18,7)
                                if v3_f_mode == 1:
                                    if os.path.exists("ctrls.txt"):
                                        os.remove("ctrls.txt")
                                    os.system("v4l2-ctl -d /dev/v4l-subdev1 --list-ctrls >> ctrls.txt")
                                    restart = 1
                                    time.sleep(0.25)
                                    ctrlstxt = []
                                    with open("ctrls.txt", "r") as file:
                                        line = file.readline()
                                        while line:
                                            ctrlstxt.append(line.strip())
                                            line = file.readline()
                                    foc_ctrl = ctrlstxt[3].split('value=')
                                    v3_focus = int(foc_ctrl[1])
                                    text(0,4,2,0,1,"Focus Manual",14,7)
                                    text(0,4,3,1,1,str(v3_focus),18,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)
                        
                    if g == 7 and (ram_frames > 0 or frames > 0) and vid_pic == 0:
                        menu = 5
                        for d in range(0,10):
                            button(0,d,0)
                        show = 1
                        frame = 0
                        old_cap = Capture
                        Capture = 0
                        if vid_pic == 0:
                            text(0,1,2,0,1,"Video",14,7)
                        else:
                            text(0,1,2,0,1,"Picture",14,7)
                        zzpics = []
                        rpics = []
                        zzpics = glob.glob('/home/' + h_user[0] + '/Videos/*99999.jpg')
                        rpics = glob.glob('/run/shm/*99999.jpg')
                        frames = 0
                        ram_frames = 0
                        rpics.sort()
                        for x in range(0,len(rpics)):
                             zzpics.append(rpics[x])
                        zzpics.sort()
                        z = ""
                        y = ""
                        for x in range(0,len(zzpics)):
                            if len(zzpics[x]) > 32:
                                if zzpics[x][16+(l_len-2):28+(l_len-2)] != z:
                                    z = zzpics[x][16+(l_len-2):28+(l_len-2)]
                                    frames +=1
                            else:
                                if zzpics[x][9:21] != y:
                                    y = zzpics[x][9:21]
                                    ram_frames +=1
                        q = 0
                        if len(zzpics) > 0:
                            play = glob.glob(zzpics[q][:-10] + "*.jpg")
                            play.sort()
                            image = pygame.image.load(zzpics[q])
                            if vid_pic == 0 :
                                cropped = pygame.transform.scale(image, (cwidth,xheight))
                            else:
                                igw = image.get_width()
                                igh = image.get_height()
                                cropped = pygame.transform.scale(image, (cwidth,int(igh*(cwidth/igw))))
                            windowSurfaceObj.blit(cropped, (0, 0))
                            fontObj = pygame.font.Font(None, 30)
                            msgSurfaceObj = fontObj.render(str(zzpics[q] + " : " + str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1) ), False, (255,0,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,10)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,cwidth,scr_height))
                            pygame.display.update()
                        text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),18,7)
                        text(0,2,2,0,1,"PLAY",14,7)
                        text(0,2,2,1,1,"Video",14,7)
                        text(0,3,2,0,1,"Frame",14,7)
                        text(0,5,2,0,1,"MAKE A",14,7)
                        text(0,5,2,1,1,"MP4",14,7)
                        text(0,6,2,0,1,"MAKE ALL",14,7)
                        text(0,6,2,1,1,"MP4s",14,7)
                        text(0,7,2,0,1,"MAKE FULL",14,7)
                        text(0,7,2,1,1,"MP4",14,7)
                        USB_Files  = []
                        USB_Files  = (os.listdir("/media/" + h_user[0]))
                        Mideos = glob.glob('/home/' + h_user[0] + '/Videos/*.mp4')
                        if len(USB_Files) > 0 and movtousb == 0 and len(Mideos) > 0:
                             text(0,8,2,0,1,"MOVE MP4s",14,7)
                             text(0,8,2,1,1,"to USB",14,7)
                        else:
                             text(0,8,0,0,1,"MOVE MP4s",14,7)
                             text(0,8,0,1,1,"to USB",14,7)
                        text(0,4,0,0,1,"DEL to END",14,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)

                    if g == 10 and menu != -1:
                        main_menu()
                        
            # save config if changed
            if save_config == 1:
                config[0]  = h_crop
                config[1]  = threshold
                config[2]  = fps
                config[3]  = mode
                config[4]  = speed
                config[5]  = gain
                config[6]  = brightness
                config[7]  = contrast
                config[8]  = Capture
                config[9]  = preview
                config[10] = awb
                config[11] = detection
                config[12] = int(red*10)
                config[13] = int(blue*10)
                config[14] = interval
                config[15] = v_crop
                config[16] = v_length
                config[17] = ev
                config[18] = meter
                config[19] = ES
                config[20] = a
                config[21] = b
                config[22] = sharpness
                config[23] = saturation
                config[24] = denoise
                config[25] = fan_low
                config[26] = fan_high
                config[27] = vid_pic
                config[28] = det_high
                config[29] = quality
                config[30] = fan_time
                config[31] = sd_hour
                config[32] = vformat
                config[33] = threshold2
                config[34] = col_filter
                config[35] = nr
                config[36] = pre_frames
                config[37] = auto_limit
                config[38] = ram_limit
                config[39] = v3_f_mode
                config[40] = v3_focus

                with open(config_file, 'w') as f:
                    for item in config:
                        f.write("%s\n" % item)
    if restart == 1 and time.monotonic() - timer > 1:
        if trace == 1:
            print ("Step 14 RESTART")
        timer = time.monotonic()
        restart = 0
        poll = p.poll()
        if poll == None:
            os.killpg(p.pid, signal.SIGTERM)
        Camera_start(cap_width,cap_height,zoom,vid_pic)

            





                  





                      

