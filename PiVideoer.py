#!/usr/bin/env python3

"""Copyright (c) 2025
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

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
from gpiozero import Button
from gpiozero import LED
#from gpiozero import CPUTemperature
from gpiozero import PWMLED
import sys
import random

version = "1.16"

# set screen size
scr_width  = 800
scr_height = 480

# use GPIO for external camera triggers and optional FAN.
# DISABLE Pi FAN CONTROL in Preferences > Performance to GPIO 14 !!
use_gpio = 0

# ext camera trigger output gpios (if use_gpio = 1)
s_focus  = 16
s_trig   = 12

# ext trigger input gpios (if use_gpio = 1)
e_trig1   = 21
e_trig2   = 20

# fan ctrl gpio (if use_gpio = 1) This is not the Pi5 active cooler !!
# DISABLE Pi FAN CONTROL in Preferences > Performance to GPIO 14 !!
fan      = 14
fan_ctrl = 0  # 0 for OFF. 

# save MP4 to SD / USB, 0 = SD Card, 1 = USB 
movtousb = 0

# USB cameras
auto_detect = 1
    

# set default config parameters
v_crop        = 80      # size of vertical detection window *
h_crop        = 80      # size of horizontal detection window *
threshold     = 20      # minm change in pixel luminance *
threshold2    = 255     # maxm change in pixel luminance *
detection     = 10      # % of pixels detected to trigger, in % *
det_high      = 100     # max % of pixels detected to trigger, in %  *
fps           = 25      # set camera fps *
mp4_fps       = 25      # set MP4 fps *
mode          = 1       # set camera mode ['off','normal','sport'] *
speed         = 80000   # set manual shutter speed in mS x 1000 *
gain          = 0       # set gain , 0 = AUTO *
brightness    = 0       # set camera brightness *
contrast      = 70      # set camera contrast *
Capture       = 1       # 0 = off, 1 = ON *
preview       = 0       # show detected changed pixels *
noframe       = 0       # set to 1 for no window frame
awb           = 1       # auto white balance, 1 = ON, 0 = OFF *
red           = 3.5     # red balance *
blue          = 1.5     # blue balance *
meter         = 0       # metering *
ev            = 0       # eV *
interval      = 0       # wait between capturing Pictures *
v_length      = 10000   # video length in mS *
ES            = 1       # trigger external camera, 0 = OFF, 1 = SHORT, 2 = LONG *
denoise       = 0       # denoise level *
quality       = 90      # video quality *
sharpness     = 14      # sharpness *
saturation    = 12      # saturation *
SD_limit      = 90      # max SD card filled in % before copy to USB if available or STOP *
auto_save     = 1       # set to 1 to automatically copy to SD card
auto_time     = 10      # time after which auto save actioned, 0 = OFF
ram_limit     = 150     # MBytes, copy from RAM to SD card when reached *
fan_time      = 10      # fan sampling time in seconds *
fan_low       = 65      # fan OFF below this, 25% to 100% pwm above this *
fan_high      = 78      # fan 100% pwm above this *
sd_hour       = 22      # Shutdown Hour, 1 - 23, 0 will NOT SHUTDOWN *
vformat       = 0       # SEE VWIDTHS/VHEIGHTS *
col_filter    = 3       # 3 = FULL, SEE COL_FILTERS *
nr            = 0       # Noise reduction *
pre_frames    = fps * 2 # 2 x fps = 2 seconds *
scientific    = 0       # scientific for HQ camera * 
v3_f_mode     = 0       # v3 camera focus mode *
v3_focus      = 0       # v3 camera manual focus default *
dspeed        = 10      # detection speed 1-100, 1 = slowest *
square        = 0       # 0 = normal format , 1 = square format *
sqpos         = .15     # square format position *
anno          = 1       # annotate MP4s with date and time , 1 = yes, 0 = no *
SD_F_Act      = 0       # Action on SD FULL, 0 = STOP, 1 = DELETE OLDEST VIDEO, 2 = COPY TO USB (if fitted) *
alp           = 255     # alpha, used for stop animations, shows current and last frame *
m_alpha       = 130     # MASK ALPHA *
photo_timer   = 0.2     # time between photos (2 camera setup ONLY) *
mode2         = 1       # set camera2 mode ['off','normal','sport'] *
speed2        = 80000   # set manual shutter speed2 in mS x 1000 *
gain2         = 0       # set gain2 , 0 = AUTO *
brightness2   = 0       # set camera2 brightness *
contrast2     = 70      # set camera2 contrast *
ev2           = 0       # eV2 *
meter2        = 0       # meter2 *
sharpness2    = 14      # sharpness2 
saturation2   = 12      # saturation2 
framerate2    = 25      # framerate2 *
# * adjustable whilst running

# initialise parameters
camera        = 0
synced        = 0
show          = 0
reboot        = 0
stopped       = 0
record        = 0
timer         = 0
zoom          = 0
trace         = 0
timer10       = 0
col_filterp   = 0
config_file   = "PiVideoconfig101.txt"
a             = int(scr_width/3)
b             = int(scr_height/2)
fcount        = 0
dc            = 0
q             = 0
of            = 0
txtvids       = []
en_photo      = 0
restart2      = 0
timer2        = time.monotonic()
res2          = 0
max_fcount    = 10
gcount        = 0
fstep         = 20
old_foc       = 0
min_foc       = 15
rep           = 0

# setup directories
Home_Files  = []
Home_Files.append(os.getlogin())
pic     = "Pictures"
pic_dir = "/home/" + Home_Files[0]+ "/" + pic + "/"

cameras       = ['', 'Pi v1', 'Pi v2', 'Pi v3', 'Pi HQ','Arducam 16MP','Arducam 64MP', 'Pi GS','Arducam Owlsight','imx290','imx500']
camids        = ['','ov5647','imx219','imx708','imx477',      'imx519',      'arduca','imx296',          'ov64a4','imx290','imx500']
max_gains     = [64,     255,      40,      64,      88,            64,            64,      64,                64,      64,      64]
modes         = ['off','normal','sport']
meters        = ['centre','spot','average']
awbs          = ['off','auto','incandescent','tungsten','fluorescent','indoor','daylight','cloudy']
denoises      = ['off','cdn_off','cdn_fast','cdn_hq']
vwidths       = []
vheights      = []
col_filters   = ['RED','GREEN','BLUE','FULL']
noise_filters = ['OFF','LOW','HIGH']
v3_f_modes    = ['auto','manual','continuous']

#check Pi model.
Pi = 0
if os.path.exists ('/run/shm/md.txt'): 
    os.remove("/run/shm/md.txt")
os.system("cat /proc/cpuinfo >> /run/shm/md.txt")
with open("/run/shm/md.txt", "r") as file:
        line = file.readline()
        while line:
           line = file.readline()
           if line[0:5] == "Model":
               model = line
mod = model.split(" ")
if mod[3] == "5":
    Pi = 5

# setup gpio if enabled
if use_gpio == 1:
    # external output triggers
    led_s_trig  = LED(s_trig)
    led_s_focus = LED(s_focus)
    led_s_trig.off()
    led_s_focus.off()
    # optional fan control
    if fan_ctrl == 1:
        led_fan = PWMLED(fan)
        led_fan.value = 0
    # external input triggers
    button_e_trig1 = Button(e_trig1,pull_up=False)
    button_e_trig2 = Button(e_trig2,pull_up=False)

# check Vid_configXX.txt exists, if not then write default values
if not os.path.exists(config_file):
    defaults = [h_crop,threshold,fps,mode,speed,gain,brightness,contrast,SD_limit,preview,awb,detection,int(red*10),int(blue*10),
              interval,v_crop,v_length,ev,meter,ES,a,b,sharpness,saturation,denoise,fan_low,fan_high,det_high,quality,
              fan_time,sd_hour,vformat,threshold2,col_filter,nr,pre_frames,auto_time,ram_limit,v3_f_mode,v3_focus,square,int(sqpos*100),
              mp4_fps,anno,SD_F_Act,dspeed,int(photo_timer*10),camera,mode2,speed2,gain2,brightness2,contrast2,ev2,meter2,sharpness2,saturation2,
              framerate2]
    with open(config_file, 'w') as f:
        for item in defaults:
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
SD_limit    = config[8]
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
det_high    = config[27]
quality     = config[28]
fan_time    = config[29]
sd_hour     = config[30]
vformat     = config[31]
threshold2  = config[32]
col_filter  = config[33]
nr          = config[34]
pre_frames  = config[35]
auto_time   = config[36]
ram_limit   = config[37]
square      = config[40]
sqpos       = config[41]/100
mp4_fps     = config[42]
anno        = config[43]
SD_F_Act    = config[44]
dspeed      = config[45]
photo_timer = config[46]/10
mode2       = config[48]
speed2      = config[49]
gain2       = config[50]
brightness2 = config[51]
contrast2   = config[52]
ev2         = config[53]
meter2      = config[54]
sharpness2  = config[55]
saturation2 = config[56]
framerate2  = config[57]

bw = int(scr_width/8)
cwidth  = scr_width - bw
cheight = scr_height
old_vf  = vformat
focus   = 0

def Camera_Version():
  global old_vf,bw,Pi_Cam,cam1,cam2,camera,camids,max_camera,same_cams,max_gain,max_vf,max_vfs,a,b,a2,b2,h_crop,v_crop,h_crop2,v_crop2,cap_width,cap_height,vformat,xheight,cwidth,vwidths,vheights,xwidth,scr_width,scr_height  # DETERMINE NUMBER OF CAMERAS (FOR Pi5)
  if os.path.exists('libcams.txt'):
   os.rename('libcams.txt', 'oldlibcams.txt')
  os.system("rpicam-vid --list-cameras >> libcams.txt")
  time.sleep(0.5)
  # read libcams.txt file
  camstxt = []
  with open("libcams.txt", "r") as file:
    line = file.readline()
    while line:
        camstxt.append(line.strip())
        line = file.readline()
  max_camera = 0
  same_cams  = 0
  cam1 = "1"
  cam2 = "2"
  vwidths  = []
  vheights = []
  cwidth = scr_width - bw
  cheight = scr_height
  for x in range(0,len(camstxt)):
    # Determine if both cameras are the same model
    if camstxt[x][0:4] == "0 : ":
        cam1 = camstxt[x][4:10]
    elif camstxt[x][0:4] == "1 : ":
        cam2 = camstxt[x][4:10]
    elif cam1 != "1" and cam2 == "2" and camera == 0:
        forms = camstxt[x].split(" ")
        for q in range(0,len(forms)):
           if "x" in forms[q] and "/" not in forms[q]:
              qwidth,qheight = forms[q].split("x")
              vwidths.append(int(qwidth))
              vheights.append(int(qheight))
    elif cam1 != "1" and cam2 != "2" and camera == 1:
        forms = camstxt[x].split(" ")
        for q in range(0,len(forms)):
           if "x" in forms[q] and "/" not in forms[q]:
              qwidth,qheight = forms[q].split("x")
              vwidths.append(int(qwidth))
              vheights.append(int(qheight))
        
    # Determine MAXIMUM number of cameras available 
    if camstxt[x][0:4] == "3 : " and max_camera < 3:
        max_camera = 3
    elif camstxt[x][0:4] == "2 : " and max_camera < 2:
        max_camera = 2
    elif camstxt[x][0:4] == "1 : " and max_camera < 1:
        max_camera = 1
        
  if max_camera == 1 and cam1 == cam2:
    same_cams = 1
  Pi_Cam = -1
  for x in range(0,len(camids)):
     if camera == 0:
        if cam1 == camids[x]:
            Pi_Cam = x
     elif camera == 1:
        if cam2 == camids[x]:
            Pi_Cam = x
  if Pi_Cam != 7:
      vwidths.insert(0, 1280)
      vheights.insert(0,720)
  else:
      vwidths.insert(0,1920)
      vheights.insert(0,1080)

  max_gain = max_gains[Pi_Cam]
  if vformat > len(vwidths) - 1 or camera == 1:
      vformat = len(vwidths) - 1
      old_vf = vformat
  if camera == 0:
      vformat = old_vf
  cap_width  = vwidths[vformat]
  cap_height = vheights[vformat]
  xheight = int(cwidth * (cap_height/cap_width))
  if xheight > scr_height:
      xheight = scr_height
      cwidth = int(xheight * (cap_width/cap_height))
  if square == 0:
      xwidth = cwidth
  else:
      xwidth = xheight
  if a > xwidth - v_crop:
      a = int(xwidth/2)
  if b > xheight - h_crop:
      b = int(xheight/2)
  a2 = int(a * (cap_width/cwidth))
  b2 = int(b * (cap_height/xheight))
  h_crop2  = int(h_crop * (cap_width/cwidth))
  v_crop2  = int(v_crop * (cap_height/xheight))

  if Pi_Cam != -1:
      print("Camera: ", camids[Pi_Cam])
  else:
      print("No Camera Found")
      pygame.display.quit()
      sys.exit()
            
Camera_Version()

print(Pi_Cam,cam1,cam2)

#set screen image width
if square == 1:
    apos = 100
else:
    apos = int(cap_width/4)

bh = int(scr_height/12)
font_size = int(min(bh, bw)/3)
start_up = time.monotonic()
col_timer = 0
pygame.init()

# find usb cameras
v1 = -1
v2 = -1
v3 = -1
v4 = -1
for x in range (0,42):
    txt = "v4l2-ctl -d " + str(x) + " --list-ctrls > cam_ctrls.txt"
    os.system(txt)
    ctrls = []
    with open("cam_ctrls.txt", "r") as file:
        line = file.readline()
        while line:
            ctrls.append(line)
            line = file.readline()
    if 'User Controls\n' in ctrls and ('Camera Controls\n' in ctrls or '               band_stop_filter 0x00980921 (bool)   : default=0 value=0\n' in ctrls):
        if v1 == -1:
            v1 = x
        elif v2 == -1:
            v2 = x
        elif v3 == -1:
            v3 = x
        elif v4 == -1:
            v4 = x

def camera_format(usb):
    # find formats, and set USB still width and height
    global width,height,preview_width,preview_height,still_width,still_height
    txt = "v4l2-ctl -d " + str(usb) + " --list-formats-ext > cam_fmts.txt"
    os.system(txt)
    w = 0
    h = 0
    with open("cam_fmts.txt", "r") as file:
        line = file.readline()
        while line:
            line = file.readline()
            count = line.count(":")
            if count == 1:
                a,b = line.split(":")
                if a[len(a)-4:len(a)] == "Size":
                    c,d = b.split("x")
                    e,f,g = c.split(" ")
                    if int(d) > h:
                        h = int(d)
                    if int(g) > w:
                        w = int(g)
    if w != 0 and h!= 0:
        width  = w
        height = h
    print ("USB " + str(usb) + " Still Format set: " ,width," x" ,height)

# start USB cameras
if v1 != -1:
    if auto_detect == 1:
        camera_format(v1)
    vid1 = cv2.VideoCapture(v1)
    vid1.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    vid1.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
if v2 != -1:
    if auto_detect == 1:
        camera_format(v2)
    vid2 = cv2.VideoCapture(v2)
    vid2.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    vid2.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
if v3 != -1:
    if auto_detect == 1:
        camera_format(v3)
    vid3 = cv2.VideoCapture(v3)
    vid3.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    vid3.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
if v4 != -1:
    if auto_detect == 1:
        camera_format(v4)
    vid4 = cv2.VideoCapture(v4)
    vid4.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    vid4.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
print(v1,v2,v3,v4)
            
fxx = 0
fxy = 0
fxz = 1
USB_storage = 100

# find username
h_user = "/home/" + os.getlogin( )
m_user = "/media/" + os.getlogin( )
l_len = len(h_user)

if os.path.exists('/usr/share/rpicam/ipa/rpi/vc4/imx477_scientific.json') and Pi_Cam == 4:
    scientif = 1
else:
    scientif = 0

if not os.path.exists(h_user + '/CMask.bmp'):
   pygame.init()
   bredColor =   pygame.Color(100,100,100)
   mwidth = 200
   mheight = 200
   windowSurfaceObj = pygame.display.set_mode((mwidth, mheight), pygame.NOFRAME, 24)
   pygame.draw.rect(windowSurfaceObj,bredColor,Rect(0,0,mwidth,mheight))
   pygame.display.update()
   pygame.image.save(windowSurfaceObj,h_user + '/CMask.bmp')
   pygame.display.quit()

def MaskChange(): # used for masked window resizing
   global v_crop2,h_crop2
   mask = cv2.imread(h_user + '/CMask.bmp')
   mask = cv2.resize(mask, dsize=(v_crop2 * 2, h_crop2 * 2), interpolation=cv2.INTER_CUBIC)
   mask = cv2.cvtColor(mask,cv2.COLOR_RGB2GRAY)
   mask = mask.astype(np.int16)
   mask[mask >= 1] = 1
   change = 1
   return (mask,change)

mask,change = MaskChange()

if os.path.exists('mylist.txt'):
    os.remove('mylist.txt')

# determine /dev/v4l-subdevX for Pi v3 and Arducam 16/64MP cameras
foc_sub3 = -1
foc_sub5 = -1
for x in range(0,10):
    if os.path.exists("ctrls.txt"):
        os.remove("ctrls.txt")
    os.system("v4l2-ctl -d /dev/v4l-subdev" + str(x) + " --list-ctrls >> ctrls.txt")
    time.sleep(0.25)
    ctrlstxt = []
    with open("ctrls.txt", "r") as file:
        line = file.readline()
        while line:
            ctrlstxt.append(line.strip())
            line = file.readline()
    for j in range(0,len(ctrlstxt)):
        if ctrlstxt[j][0:51] == "focus_absolute 0x009a090a (int)    : min=0 max=4095":
            foc_sub5 = x
        if ctrlstxt[j][0:51] == "focus_absolute 0x009a090a (int)    : min=0 max=1023":
            foc_sub3 = x
    
# start Pi Camera subprocess 
def Camera0_start(wx,hx,zoom):
    global camera,sqpos,square,scientif,fxx,fxy,fxz,Pi_Cam,v3_f_modes,v3_f_mode,scientific,SD_storage,trace,p,red,blue,contrast,brightness,gain,speed,modes,mode,ev,ES,cap_width,cap_height,pre_frames,awbs,awb,meters,meter,sharpness,saturation,denoise,cwidth,xheight
    if trace == 1:
        print ("Step 1 START SUB PROC")
    # clear ram
    zpics = glob.glob('/run/shm/test*.jpg')
    for tt in range(0,len(zpics)):
        os.remove(zpics[tt])
    st = os.statvfs("/run/shm/")
    freeram = (st.f_bavail * st.f_frsize)/1100000
    ss = str(int(sfreeram)) + "MB - " + str(int(SD_storage)) + "%"
    if camera == 0:
      rpistr = "rpicam-vid --camera " + str(camera) + " -t 0 --segment 1 --codec mjpeg -q " + str(quality)
      rpistr += " -n -o /run/shm/test%06d.jpg --contrast " + str(contrast/100) + " --brightness " + str(brightness/100)
      if square == 1:
        rpistr += " --width " + str(hx) + " --height " + str(hx)
      else:
        rpistr += " --width " + str(wx) + " --height " + str(hx)
      if awb > 0:
        rpistr += " --awb " + awbs[awb]
      else:
        rpistr += " --awbgains " + str(red) + "," + str(blue)
      if mode == 0:
        rpistr +=" --shutter " + str(speed) + " --framerate " + str(int((1/speed)*1000000))
      else:
        rpistr +=" --exposure " + str(modes[mode]) + " --framerate " + str(fps)
      rpistr += " --ev " + str(ev) +  " --gain " + str(gain)
      rpistr += " --metering "   + meters[meter]
      rpistr += " --saturation " + str(saturation/10)
      rpistr += " --sharpness "  + str(sharpness/10)
      rpistr += " --denoise "    + denoises[denoise]
      if square == 1:
        if Pi_Cam == 7 or Pi_Cam == 3:
            rpistr += " --roi " + str(sqpos) + ",0," + str(hx/wx) + ",1"
        elif Pi_Cam == 2:
            rpistr += " --roi " + str(sqpos) + ",0.28,0.325,0.44"
        else:
            rpistr += " --roi " + str(sqpos) + ",0.14,0.5625,0.7"
      if Pi_Cam == 3 and v3_f_mode > 0 :
        rpistr += " --autofocus-mode " + v3_f_modes[v3_f_mode]
        if v3_f_mode == 1:
            rpistr += " --lens-position " + str(v3_focus/100)
      if Pi_Cam == 3 and zoom == 0:
        rpistr += " --autofocus-window " + str(fxx) + "," + str(fxy) + "," + str(fxz) + "," + str(fxz)
      if scientific == 1 and Pi_Cam == 4:
        rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/vc4/imx477_scientific.json"
      if (Pi_Cam == 5 or Pi_Cam == 6) and v3_f_mode == 1 and Pi == 5:
        if os.path.exists('/usr/share/libcamera/ipa/rpi/pisp/imx519mf.json'):
            rpistr += " --tuning-file /usr/share/libcamera/ipa/rpi/pisp/imx519mf.json"
        
    if camera == 1:
      rpistr = 'rpicam-vid --camera 1 -n -t 0 --segment 1 --codec mjpeg -o /run/shm/test%06d.jpg --contrast ' + str(contrast2/100) + " --brightness " + str(brightness2/100)
      if mode2 == 0:
          rpistr +=" --shutter " + str(speed2) + " --framerate " + str(framerate2)
      else:
          rpistr +=" --exposure " + str(modes[mode2]) + " --framerate " + str(framerate2)
      rpistr += " --ev " + str(ev2) +  " --gain " + str(gain2)
      rpistr += " --width " + str(wx) + " --height " + str(hx)
      if Pi_Cam == 3 :
          rpistr += " --autofocus-mode continuous "
        
    #print (rpistr)
    p = subprocess.Popen(rpistr, shell=True, preexec_fn=os.setsid)
    st = time.monotonic()
    poll = p.poll()
    if poll != None and time.monotonic() - st < 5:
        poll = p.poll()
    if poll != None:
        print ("Failed to start sub-process")

# check for usb_stick
USB_Files  = []
USB_Files  = (os.listdir(m_user + "/"))
print(USB_Files)
if len(USB_Files) > 0:
    usedusb = os.statvfs(m_user + "/" + USB_Files[0] + "/")
    USB_storage = ((1 - (usedusb.f_bavail / usedusb.f_blocks)) * 100)
    if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Videos/") :
        os.system('mkdir ' + m_user + "/'" + USB_Files[0] + "'/Videos/")
    if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Pictures/") :
        os.system('mkdir ' + m_user + "/'" + USB_Files[0] + "'/Pictures/")
   
old_cap = Capture

# read list of existing Video Files
outvids = []
z = ""
y = ""
frames = 0
ram_frames = 0
sframe = -1
eframe = -1
trig = 1
# SD card
Sideos = glob.glob(h_user + '/Pictures/*.jpg')
Sideos.sort()
for x in range(0,len(Sideos)):
    Tideos = Sideos[x].split("/")
    if Tideos[len(Tideos) - 1][:-10] != z:
        z = Tideos[len(Tideos) - 1][:-10]
        outvids.append(z)
        frames +=1

# read list of existing Photo Files
photos = []
photos = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
photos.sort()

# USB stick
USB_Files  = []
USB_Files  = (os.listdir(m_user + "/"))
if len(USB_Files) > 0:
    Sideos = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/*.jpg")
    Sideos.sort()
    for x in range(0,len(Sideos)):
        Tideos = Sideos[x].split("/")
        if Tideos[len(Tideos) - 1][:-10] != z:
            z = Tideos[len(Tideos) - 1][:-10]
            outvids.append(z)
            frames +=1

vf = str(ram_frames) + " - " + str(frames)
if Pi == 5 and cam2 != "2":
    vf = vf + " - " + str(len(photos))

# read list of existing MP4 files
Mideos = glob.glob(h_user + '/Videos/*.mp4')

restart    = 0
menu       = -1
zoom       = 0

# get RAM free space
st = os.statvfs("/run/shm/")
sfreeram = (st.f_bavail * st.f_frsize)/1100000

# check if clock synchronised                           
os.system("timedatectl >> sync.txt")
# read sync.txt file
try:
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
except:
    pass

# setup pygame window
if noframe == 0:
   windowSurfaceObj = pygame.display.set_mode((scr_width,scr_height), 0, 24)
else:
   windowSurfaceObj = pygame.display.set_mode((scr_width,scr_height), pygame.NOFRAME, 24)
   
pygame.display.set_caption('Action ' + cameras[Pi_Cam])

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
   colors = [greyColor, dgryColor, whiteColor, redColor, greenColor,yellowColor]
   Color = colors[bColor]
   bx = scr_width - ((1-col) * bw) + 2
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
   if os.path.exists ('/usr/share/fonts/truetype/freefont/FreeSerif.ttf'): 
       fontObj = pygame.font.Font('/usr/share/fonts/truetype/freefont/FreeSerif.ttf', int(fsize))
   else:
       fontObj = pygame.font.Font(None, int(fsize))
   colors =  [dgryColor, greenColor, yellowColor, redColor, greenColor, blueColor, whiteColor, greyColor, blackColor, purpleColor]
   Color  =  colors[fColor]
   bColor =  colors[bcolor]
   bx = scr_width - ((1-col) * bw)
   by = row * bh
   msgSurfaceObj = fontObj.render(msg, False, Color)
   msgRectobj = msgSurfaceObj.get_rect()
   if top == 0:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+3,by+1,bw-2,int(bh/2)))
       msgRectobj.topleft = (bx + 7, by + 3)
   elif msg == "START - END" or msg == "<<   <    >   >>":
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+int(bw/4),by+int(bh/2),int(bw/1.5),int(bh/2)-1))
       msgRectobj.topleft = (bx+7, by + int(bh/2))
   else:
       pygame.draw.rect(windowSurfaceObj,bColor,Rect(bx+int(bw/4),by+int(bh/2),int(bw/1.5),int(bh/2)-1))
       msgRectobj.topleft = (bx+int(bw/4), by + int(bh/2))
   windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
   if upd == 1:
      pygame.display.update(bx, by, bw, bh)

def main_menu():
    global ram_frames,frames,menu,sd_hour,pf,vf,synced,Capture,show,zoom,preview,scr_height,cwidth,photos,old_cap
    menu = -1
    show = 0
    preview = 0
    Capture = old_cap
    zoom = 0
    for d in range(0,11):
         button(0,d,0)
    button(0,1,3)
    zzpics = glob.glob(h_user + '/Pictures/*99999.jpg')
    rpics = glob.glob('/run/shm/*99999.jpg')
    frames = 0
    ram_frames = 0
    for x in range(0,len(rpics)):
        zzpics.append(rpics[x])
    USB_Files  = (os.listdir(m_user))
    if len(USB_Files) > 0:
        upics = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/*99999.jpg")
        for x in range(0,len(upics)):
            zzpics.append(upics[x])
    zzpics.sort()
    z = ""
    y = ""
    for x in range(0,len(zzpics)):
        Tideos = zzpics[x].split("/")
        if len(Tideos) >= 5:
            if Tideos[len(Tideos) - 1][:-10] != z:
                z = Tideos[len(Tideos) - 1][:-10]
                outvids.append(z)
                frames +=1
        else:
            if Tideos[len(Tideos) - 1][:-10] != y:
                y = Tideos[len(Tideos) - 1][:-10]
                outvids.append(y)
                ram_frames +=1
    photos = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
    photos.sort()
    if Capture == 0 and menu == -1:
        button(0,0,0)
        text(0,0,0,0,1,"CAPTURE",16,7)
        vf = str(ram_frames) + " - " + str(frames)
        if Pi == 5 and cam2 != "2":
            vf = vf + " - " + str(len(photos))
        text(0,0,3,1,1,vf,14,7)
    elif menu == -1:
        button(0,0,4)
        text(0,0,6,0,1,"CAPTURE",16,4)
        vf = str(ram_frames) + " - " + str(frames)
        if Pi == 5 and cam2 != "2":
            vf = vf + " - " + str(len(photos))
        text(0,0,3,1,1,vf,14,4)
    text(0,1,6,0,1,"RECORD",16,3)
    text(0,2,1,0,1,"DETECTION",14,7)
    text(0,2,1,1,1,"Settings",14,7)
    text(0,3,1,0,1,"CAMERA",14,7)
    text(0,3,1,1,1,"Settings 1",14,7)
    text(0,4,1,0,1,"CAMERA",14,7)
    text(0,4,1,1,1,"Settings 2",14,7)
    text(0,5,1,0,1,"CAMERA",14,7)
    text(0,5,1,1,1,"Settings 3",14,7)
    text(0,7,1,0,1,"OTHER",14,7)
    text(0,7,1,1,1,"Settings ",14,7)
    if ((ram_frames > 0 or frames > 0 or len(photos) > 0) and menu == -1):
        text(0,6,1,0,1,"SHOW,EDIT or",13,7)
        text(0,6,1,1,1,"DELETE",13,7)
    else:
        text(0,6,0,0,1,"SHOW,EDIT or",13,7)
        text(0,6,0,1,1,"DELETE",13,7)
    if ram_frames > 0 or frames > 0:
        text(0,8,1,0,1,"MAKE",14,7)
        text(0,8,1,1,1,"MP4",14,7)
    else:
        text(0,8,0,0,1,"MAKE",14,7)
        text(0,8,0,1,1,"MP4",14,7)
    if Pi == 5 and cam2 != "2":
        text(0,9,1,0,1,"2nd Camera",14,7)
        text(0,9,1,1,1,"Settings",14,7)
    text(0,10,3,0,1,"EXIT",16,7)
    st = os.statvfs("/run/shm/")
    freeram = (st.f_bavail * st.f_frsize)/1100000
    free = (os.statvfs('/'))
    SD_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
    ss = str(int(freeram)) + "MB - " + str(int(SD_storage)) + "%"
    if record == 0:
        text(0,1,6,1,1,ss,12,3)
    else:
         text(0,1,6,1,1,ss,12,0)
    pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,0,scr_width - bw,scr_height))

# clear ram
zpics = glob.glob('/run/shm/*.jpg')
for tt in range(0,len(zpics)):
    os.remove(zpics[tt])
    
main_menu()
oldimg = []
show   = 0
vidjr  = 0
Videos = []
last   = time.monotonic()
fan_timer = time.monotonic()

# check sd card space
free = (os.statvfs('/'))
SD_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
ss = str(int(sfreeram)) + "MB - " + str(int(SD_storage)) + "%"

# start Pi Camera0 subprocess
Camera0_start(cap_width,cap_height,zoom)

if cam2 != "2":
    # start 2nd Pi camera
    now = datetime.datetime.now()
    timestamp = now.strftime("%y%m%d%H%M%S")
    fname =  pic_dir + 'CAM1_'  + str(timestamp) + '_%04d.jpg'
    rpistr2 = 'rpicam-still --camera 1 -s -n -t 0 -e jpg -o ' + fname + ' --contrast ' + str(contrast2/100) + " --brightness " + str(brightness2/100)
    if mode2 == 0:
        rpistr2 +=" --shutter " + str(speed2)
    else:
        rpistr2 +=" --exposure " + str(modes[mode2])
    rpistr2 += " --ev " + str(ev2) +  " --gain " + str(gain2)
    rpistr2 += " --metering "   + meters[meter2]
    rpistr2 += " --sharpness "  + str(sharpness2/10)
    #print(rpistr2)
    s = subprocess.Popen(rpistr2, shell=True, preexec_fn=os.setsid)
    poll = s.poll()
    while poll != None:
        print("waiting...")
        poll = s.poll()

temp = 0
#cpu_temp = str(CPUTemperature()).split("=")
#temp = float(str(cpu_temp[1])[:-1])

old_capture = Capture

while True:
    time.sleep(1/dspeed)
    if Pi == 5 and menu == 4:
        text(0,0,2,0,1,"CPU Temp/FAN",13,7)
        if os.path.exists ('fantxt.txt'): 
            os.remove("fantxt.txt")
        os.system("cat /sys/devices/platform/cooling_fan/hwmon/*/fan1_input >> fantxt.txt")
        time.sleep(0.25)
        with open("fantxt.txt", "r") as file:
            line = file.readline()
            if line == "":
                line = 0
            text(0,0,3,1,1,str(int(temp)) + " / " + str(int(line)),14,7)
    elif menu == 4:
        text(0,0,2,0,1,"CPU Temp",14,7)
        text(0,0,3,1,1,str(int(temp)),14,7)
    # fan (NOT Pi5 active cooler) and shutdown ctrl
    if time.monotonic() - fan_timer > fan_time:
        fan_timer = time.monotonic()
        if trace == 1:
              print ("Step  FAN TIME")
        try:
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
                if menu == 7:
                    text(0,9,3,1,1,str(sd_hour) + ":00",14,7)
            else:
                synced = 0
                if menu == 7:
                    text(0,9,0,1,1,str(sd_hour)+":00",14,7)
        except:
            pass
        # check current hour
        now = datetime.datetime.now()
        hour = int(now.strftime("%H"))
        # shutdown if shutdown hour reached and clocked synced
        if hour > sd_hour - 1 and sd_hour != 0 and time.monotonic() - start_up > 600 and synced == 1:
            # EXIT and SHUTDOWN
            if trace == 1:
                 print ("Step 13 TIMED EXIT")
            # move any videos to SD Card
            if ram_frames > 0:
                if menu == -1 :
                    button(0,0,1)
                    text(0,0,5,0,1,"CAPTURE",16,0)
                    vf = str(ram_frames) + " - " + str(frames)
                    if Pi == 5 and cam2 != "2":
                        vf = vf + " - " + str(len(photos))
                    text(0,0,3,1,1,vf,14,4)
                zpics = glob.glob('/run/shm/2*.jpg')
                zpics.sort()
                for xx in range(0,len(zpics)):
                    shutil.copy(zpics[xx], h_user + '/Pictures/')
            # move MP4s to USB if present
            USB_Files  = []
            USB_Files  = (os.listdir(m_user))
            if len(USB_Files) > 0:
                usedusb = os.statvfs(m_user + "/" + USB_Files[0] + "/")
                USB_storage = ((1 - (usedusb.f_bavail / usedusb.f_blocks)) * 100)
            if len(USB_Files) > 0 and USB_storage < 90:
                spics = glob.glob(h_user + '/Videos/*.mp4')
                spics.sort()
                for xx in range(0,len(spics)):
                    movi = spics[xx].split("/")
                    if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/" + movi[4]):
                        shutil.move(spics[xx],m_user[0] + "/'" + USB_Files[0] + "'/")
            if use_gpio == 1 and fan_ctrl == 1:
                led_fan.value = 0
            pygame.quit()
            poll = p.poll()
            if poll == None:
                os.killpg(p.pid, signal.SIGTERM)
            time.sleep(5)
            os.system("sudo shutdown -h now")

        # set fan speed
        if fan_ctrl == 1:
            fan_timer = time.monotonic()
            cpu_temp = str(CPUTemperature()).split("=")
            temp = float(str(cpu_temp[1])[:-1])
            dc = ((temp - fan_low)/(fan_high - fan_low))
            dc = max(dc,.25)
            dc = min(dc,1)
            if temp > fan_low and use_gpio == 1:
                led_fan.value = dc
                if menu ==4 :
                    text(0,7,1,0,1,"Fan High  " + str(int(dc*100)) + "%",14,7)
            elif temp < fan_low and use_gpio == 1:
                led_fan.value = 0
                if menu == 4: 
                    text(0,7,2,0,1,"Fan High degC",14,7)
                
        # get RAM free space
        st = os.statvfs("/run/shm/")
        freeram = (st.f_bavail * st.f_frsize)/1100000
        # check subprocess running
        poll = p.poll()
        if poll != None and trace == 1:
            print ("Step 2 P STOPPED " + str(int(freeram)))
        apics = glob.glob('/run/shm/test*.jpg')
        time.sleep(0.25)
        bpics = glob.glob('/run/shm/test*.jpg')
        if apics == bpics and menu == -1:
            if trace == 1:
                print ("Step 2 SUB PROC STOPPED")
            restart = 1
    if trace == 1:
        print ("GLOB FILES")
        
    # wait for enough images
    pre_frames2 = pre_frames
    pre_frames2 = max(pre_frames2,2)
    zpics = glob.glob('/run/shm/test*.jpg')
    while len(zpics) < pre_frames2:
        zpics = glob.glob('/run/shm/test*.jpg')
    zpics.sort(reverse = True)
    if trace == 1:
        print ("READ IMAGE")
    # GET AN IMAGE
    image = pygame.image.load(zpics[1])
    # DELETE OLD FRAMES
    w = len(zpics)
    for tt in range(pre_frames2,w):
        os.remove(zpics[tt])
    #del zpics[pre_frames2:w]
    # IF NOT IN SHOW MODE
    if show == 0 :
        if col_timer > 0 and time.monotonic() - col_timer > 3:
            col_timer = 0
        if camera == 0 or camera == 1:
          image2 = pygame.surfarray.pixels3d(image)
          # CROP DETECTION AREA
          crop2 = image2[a2-h_crop2:a2+h_crop2,b2-v_crop2:b2+v_crop2]
          if trace == 1:
            print ("CROP ", crop2.size)
          # COLOUR FILTER
          if col_filter < 3:
            gray = crop2[:,:,col_filter]
          else:
            gray = cv2.cvtColor(crop2,cv2.COLOR_RGB2GRAY)
          if col_filter < 3 and (preview == 1 or col_timer > 0):
            im = Image.fromarray(gray)
            im.save("/run/shm/qw.jpg")
          gray = gray.astype(np.int16)
          detect = 0
           
        if np.shape(gray) == np.shape(oldimg) and (camera == 0 or camera == 1):
            # SHOW FOCUS VALUE
            if menu == 0 or menu == 4 or menu == 7 or menu == 1 or menu == 8:
                foc = cv2.Laplacian(gray, cv2.CV_64F).var()
                if menu == 0 or menu == 8:
                    if zoom == 0:
                        text(0,10,6,1,1,str(int(foc)),14,7)
                    else:
                        text(0,10,6,1,1,str(int(foc)),14,0)
                elif menu == 7: 
                    text(0,2,3,1,1,str(int(foc)),14,7)
                    text(0,2,2,0,1,"Focus Value",14,7)
                elif menu == 1: 
                    if zoom == 0:
                        text(0,9,6,1,1,str(int(foc)),14,7)
                    else:
                        text(0,9,6,1,1,str(int(foc)),14,0)
            diff = np.sum(mask)
            diff = max(diff,1)
            # COMPARE NEW IMAGE WITH OLD IMAGE
            ar5 = abs(np.subtract(np.array(gray),np.array(oldimg)))
            # APPLY THRESHOLD VALUE
            ar5[ar5 <  threshold] = 0
            ar5[ar5 >= threshold2] = 0
            ar5[ar5 >= threshold] = 1
            # APPLY MASK
            if mask.shape == ar5.shape:
               ar5 = ar5 * mask
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
            if menu == -1 and preview == 1:
                text(0,2,2,1,1,str(int((sar5/diff) * 100)) + "%",14,7)
            # MAKE PREVIEW OF DETECTED PIXELS
            if preview == 1:
                imagep = pygame.surfarray.make_surface(ar5 * 201)
                imagep.set_colorkey(0, pygame.RLEACCEL)
            # copy 1 set of video files to sd card if auto_save = 1 or low RAM, after 10 seconds of no activity
            st = os.statvfs("/run/shm/")
            freeram = (st.f_bavail * st.f_frsize)/1100000
            if (ram_frames > 0 and auto_time > 0 and time.monotonic() - last > auto_time and auto_save == 1) or (ram_frames > 0 and freeram < ram_limit):
              try:
                if trace == 1:
                    print ("Step 4 AUTO SAVE")
                if menu == -1:
                    text(0,0,5,0,1,"CAPTURE",16,0)
                # read list of existing RAM Video Files
                Videos = glob.glob('/run/shm/2*.jpg')
                Videos.sort()
                outvids = []
                z = ""
                for x in range(0,len(Videos)):
                    Tideos = Videos[x].split("/")
                    if Tideos[len(Tideos) - 1][:-10] != z:
                        z = Tideos[len(Tideos) - 1][:-10]
                        outvids.append(z)
                # copy jpgs to sd card
                zspics = glob.glob('/run/shm/' +  str(outvids[0]) + '*.jpg')
                zspics.sort()
                for xx in range(0,len(zspics)):
                    shutil.move(zspics[xx], h_user + '/Pictures/')
                ram_frames -=1
                frames +=1
                vf = str(ram_frames) + " - " + str(frames)
                if Pi == 5 and cam2 != "2":
                    vf = vf + " - " + str(len(photos))
                if menu == -1 :
                    text(0,0,3,1,1,vf,14,7)
                if Capture == 0 and menu == -1:
                    button(0,0,0)
                    text(0,0,0,0,1,"CAPTURE",16,7)
                    vf = str(ram_frames) + " - " + str(frames)
                    if Pi == 5 and cam2 != "2":
                        vf = vf + " - " + str(len(photos))
                    text(0,0,3,1,1,vf,14,7)
                elif menu == -1 and frames + ram_frames == 0:
                    button(0,0,4)
                    text(0,0,6,0,1,"CAPTURE",16,4)
                    vf = str(ram_frames) + " - " + str(frames)
                    if Pi == 5 and cam2 != "2":
                        vf = vf + " - " + str(len(photos))
                    text(0,0,3,1,1,vf,14,4)
                elif menu == -1 :
                    button(0,0,5)
                    text(0,0,3,0,1,"CAPTURE",16,2)
                    vf = str(ram_frames) + " - " + str(frames)
                    if Pi == 5 and cam2 != "2":
                        vf = vf + " - " + str(len(photos))
                    text(0,0,3,1,1,vf,14,2)
                last = time.monotonic()
                st = os.statvfs("/run/shm/")
                freeram = (st.f_bavail * st.f_frsize)/1100000
                free = (os.statvfs('/'))
                SD_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
                ss = str(int(freeram)) + "MB - " + str(int(SD_storage)) + "%"
                if menu == -1:
                    if record == 0:
                        text(0,1,6,1,1,ss,12,3)
                    else:
                        text(0,1,6,1,1,ss,12,0)
              except:
                  pass

            pygame.draw.rect(windowSurfaceObj, (0,0,0), Rect(0,0,scr_width-bw,scr_height))

            # external input triggers to RECORD
            if use_gpio == 1:
                if button_e_trig1.is_pressed or button_e_trig2.is_pressed:
                    record = 1
                
            # detection of motion
            if (((sar5/diff) * 100 > detection and (sar5/diff) * 100 < det_high) or (time.monotonic() - timer10 > interval and timer10 != 0 and threshold == 0) or record == 1) and menu == -1:
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
                    #record = 0
                    if ES > 0 and use_gpio == 1: # trigger external camera
                        led_s_focus.on()
                        time.sleep(0.25)
                        led_s_trig.on()
                        if ES == 1:
                            time.sleep(0.25)
                            led_s_trig.off()
                            led_s_focus.off()
                    # capture video frames
                    vid = 1
                    if menu == -1:
                        button(0,0,1)
                        text(0,0,3,0,1,"CAPTURE",16,0)
                        text(0,0,1,1,1," ",15,0)
                        vf = str(ram_frames) + " - " + str(frames)
                        if Pi == 5 and cam2 != "2":
                            vf = vf + " - " + str(len(photos))
                        text(0,0,3,1,1,vf,14,0)
                    start = time.monotonic()
                    start2 = time.monotonic()
                    
                    fx = 1
                    st = os.statvfs("/run/shm/")
                    freeram = (st.f_bavail * st.f_frsize)/1100000
                    while time.monotonic() - start < v_length/1000 and freeram > ram_limit:
                        time.sleep(0.1)
                        if time.monotonic() - start2 > photo_timer and cam2 != "2":
                            os.system('pkill -SIGUSR1 rpicam-still')
                            start2 = time.monotonic()
                            
                        if menu == -1:
                            st = os.statvfs("/run/shm/")
                            freeram = (st.f_bavail * st.f_frsize)/1100000
                            ss = str(int(freeram)) + "MB - " + str(int(SD_storage)) + "%"
                            if record == 0:
                                text(0,1,6,1,1,ss,12,3)
                            else:
                                text(0,1,6,1,1,ss,12,0)
                    record = 0            
                    # clear LONG EXT trigger
                    if ES == 2 and use_gpio == 1:
                        led_s_trig.off()
                        led_s_focus.off()
                        
                    # rename new frames
                    if trace == 1:
                        print ("Step 8 RENAME NEW")
                    zpics = glob.glob('/run/shm/test*.jpg')
                    zpics.reverse()
                    if v_length < 1000:
                        count = int(fps*(v_length/1000))
                    else:
                        count = len(zpics)-1
                    for x in range(0,count):
                        fxa = "00000" + str(fx)
                        if os.path.exists(zpics[x]):
                            os.rename(zpics[x],zpics[x][0:9] + timestamp + "_" + str(fxa[-5:]) + '.jpg')
                            fx +=1
                    ram_frames +=1
                    photos = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
                    photos.sort()
                    vf = str(ram_frames) + " - " + str(frames)
                    if Pi == 5 and cam2 != "2":
                        vf = vf + " - " + str(len(photos))
                    if menu == -1:
                        text(0,0,3,1,1,vf,14,7)
                    pygame.image.save(image,"/run/shm/" + str(timestamp) + "_99999.jpg")
                    of = 1
                    old_cropped = pygame.transform.scale(image, (xwidth,xheight))
                    last = time.monotonic()    
                    st = os.statvfs("/run/shm/")
                    freeram = (st.f_bavail * st.f_frsize)/1100000
                    free = (os.statvfs('/'))
                    SD_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
                    ss = str(int(freeram)) + " - " + str(int(SD_storage))
                    photos = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
                    photos.sort()
                    # if RAM space < RAM Limit
                    if ram_frames > 0 and freeram < ram_limit:
                        if trace == 1:
                            print ("Step 10 COPY TO SD")
                        if menu == -1:
                            text(0,0,5,0,1,"CAPTURE",16,0)
                            text(0,0,5,1,1," ",15,0)
                        Videos = glob.glob('/run/shm/2*.jpg')
                        Videos.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(Videos)):
                            Tideos = Videos[x].split("/")
                            if Tideos[len(Tideos) - 1][:-10] != z:
                                z = Tideos[len(Tideos) - 1][:-10]
                                outvids.append(z)
                                outvids.append(z)
                        zvpics = glob.glob('/run/shm/' +  str(outvids[0]) + '*.jpg')
                        zvpics.sort()
                        # move RAM Files to SD card
                        for xx in range(0,len(zvpics)):
                            if not os.path.exists(h_user + "/" + '/Pictures/' + zvpics[xx][9:]):
                                shutil.move(zvpics[xx], h_user + '/Pictures/')
                        # read list of existing RAM Video Files
                        Videos = glob.glob('/run/shm/2*.jpg')
                        Videos.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(Videos)):
                            Tideos = Videos[x].split("/")
                            if Tideos[len(Tideos) - 1][:-10] != z:
                                z = Tideos[len(Tideos) - 1][:-10]
                                outvids.append(z)
                        ram_frames = len(outvids)
                        # read list of existing SD Card Video Files
                        if trace == 1:
                            print ("Step 11 READ SD FILES")
                        Videos = glob.glob(h_user + '/Pictures/*.jpg')
                        Videos.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(Videos)):
                            Tideos = Videos[x].split("/")
                            if Tideos[len(Tideos) - 1][:-10] != z:
                                z = Tideos[len(Tideos) - 1][:-10]
                                outvids.append(z)
                        frames = len(outvids)
                        vf = str(ram_frames) + " - " + str(frames)
                        if Pi == 5 and cam2 != "2":
                            vf = vf + " - " + str(len(photos))
                        if menu == 3:
                            if ram_frames + frames > 0:
                                text(0,4,3,1,1,str(ram_frames + frames),14,7)
                            else:
                                text(0,4,3,1,1," ",14,7)
                    # check free RAM and SD storage space
                    st = os.statvfs("/run/shm/")
                    freeram = (st.f_bavail * st.f_frsize)/1100000
                    free = (os.statvfs('/'))
                    SD_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
                    ss = str(int(freeram)) + "MB - " + str(int(SD_storage)) + "%"
                    if SD_storage > SD_limit and menu == -1:
                        if record == 0:
                            text(0,1,6,1,1,ss,12,3)
                        else:
                            text(0,1,6,1,1,ss,12,0)
                    if menu == -1:
                        text(0,0,3,1,1,vf,14,0)
                    record = 0
                    timer10 = time.monotonic()
                    oldimg = []
                    vidjr = 1

                    if ((ram_frames > 0 or frames > 0 or len(photos) > 0)  and menu == -1):
                        text(0,6,1,0,1,"SHOW,EDIT or",13,7)
                        text(0,6,1,1,1,"DELETE",14,7)
                    elif menu == -1:
                        text(0,6,0,0,1,"SHOW,EDIT or",13,7)
                        text(0,6,0,1,1,"DELETE",14,7)
                    if (ram_frames > 0 or frames > 0) and menu == -1:
                        text(0,8,1,0,1,"MAKE",14,7)
                        text(0,8,1,1,1,"MP4",14,7)
                    elif menu == -1:
                        text(0,8,0,0,1,"MAKE",14,7)
                        text(0,8,0,1,1,"MP4",14,7)
                    USB_Files  = []
                    USB_Files  = (os.listdir(m_user))
                    if len(USB_Files) > 0:
                        usedusb = os.statvfs(m_user + "/" + USB_Files[0] + "/")
                        USB_storage = ((1 - (usedusb.f_bavail / usedusb.f_blocks)) * 100)
                    # check SD space for jpg files ,move to usb stick (if available)
                    if SD_storage > SD_limit and len(USB_Files) > 0 and SD_F_Act == 2 and USB_storage < 90:
                        if trace == 1:
                            print ("Step 12 USED SD CARD > LIMIT")
                        os.killpg(p.pid, signal.SIGTERM)
                        restart = 1
                        if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Videos/") :
                            os.system('mkdir ' + m_user + "/'" + USB_Files[0] + "'/Videos/")
                        if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Pictures/") :
                            os.system('mkdir ' + m_user + "/'" + USB_Files[0] + "'/Pictures/")
                        text(0,0,2,0,1,"CAPTURE",16,0)
                        while SD_storage > SD_limit:
                            zzpics = glob.glob(h_user + '/Pictures/2*.jpg')
                            zzpics.sort()
                            if len(zzpics) > 0:
                                q = 0
                                if os.path.getsize(zzpics[q]) > 0:
                                    move = glob.glob(zzpics[q][0:len(zzpics[q])-10] + "2*.jpg")
                                    for tt in range(0,len(move)):
                                        fjs = move[tt].split("/")
                                        fj = fjs[len(fjs)-1]
                                        #print(fj)
                                        if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Pictures/" + fj):
                                            shutil.move(move[tt],m_user + "/'" + USB_Files[0] + "'/Pictures/")
                                        else:
                                            os.remove(move[tt])
                            free = (os.statvfs('/'))
                            SD_storage = ((1 - (free.f_bavail / free.f_blocks)) * 100)
                            ss = str(int(freeram)) + "MB - " + str(int(SD_storage)) + "%"
                            if record == 0:
                                text(0,1,6,1,1,ss,12,3)
                            else:
                                text(0,1,6,1,1,ss,12,0)
                            
                        text(0,0,6,0,1,"CAPTURE",16,0)
                    elif SD_storage > SD_limit:
                        #STOP CAPTURE IF NO MORE SD CARD SPACE AND NO USB STICK
                        if trace == 1:
                            print ("Step 12a sd card limit exceeded and no or full USB stick")
                        if SD_F_Act == 0:
                            Capture = 0 # stop
                        else:
                            # remove oldest video from SD card
                            zzpics = glob.glob(h_user + '/Pictures/2*.jpg')
                            zzpics.sort()
                            q = 0
                            if os.path.getsize(zzpics[q]) > 0:
                                remove = glob.glob(zzpics[q][0:len(zzpics[q])-10] + "2*.jpg")
                            for tt in range(0,len(remove)):
                                os.remove(remove[tt])
                            frames -=1
                            vf = str(ram_frames) + " - " + str(frames)
                            if Pi == 5 and cam2 != "2":
                                vf = vf + " - " + str(len(photos))
                         
                    if Capture == 0 and menu == -1:
                        button(0,0,0)
                        text(0,0,0,0,1,"CAPTURE",16,7)
                        text(0,0,3,1,1,vf,14,7)
                    elif menu == -1 :
                        button(0,0,5)
                        text(0,0,3,0,1,"CAPTURE",16,2)
                        vf = str(ram_frames) + " - " + str(frames)
                        if Pi == 5 and cam2 != "2":
                            vf = vf + " - " + str(len(photos))
                        text(0,0,3,1,1,vf,14,2)
                    if menu == -1:
                        button(0,1,3)
                        text(0,1,6,0,1,"RECORD",16,3)
                        text(0,1,6,1,1,ss,12,3)
                    photos = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
                    photos.sort()
                   
                else:
                    if Capture == 1 and menu == -1:
                        text(0,0,3,1,1,str(interval - (int(time.monotonic() - timer10))),15,0)
            elif menu == 0:
                text(0,1,2,0,1,"Low Detect " + str(int((sar5/diff) * 100)) + "%",14,7)
        # show frame
        gcount +=1
        if gcount > 0:
          gcount = 0
          if zoom == 0:
              if camera == 0:
                  cropped = pygame.transform.scale(image, (xwidth,xheight))
              else:
                  cropped = pygame.transform.scale(image, (scr_width-bw,xheight))
              if of == 1 and alp < 255:
                  cropped.set_alpha(alp)
          else:
              cropped = pygame.surfarray.make_surface(crop2)
              cropped = pygame.transform.scale(cropped, (xwidth,xheight))
          if of == 1 and alp < 255:
              old_cropped.set_alpha(255 - alp)
              windowSurfaceObj.blit(old_cropped, (0, 0))
          windowSurfaceObj.blit(cropped, (0, 0))
          # show colour filtering
          if col_filter < 3 and (preview == 1 or col_timer > 0):
            imageqw = pygame.image.load('/run/shm/qw.jpg')
            if zoom == 0:
                imagegray = pygame.transform.scale(imageqw, (v_crop*2,h_crop*2))
            else:
                imagegray = pygame.transform.scale(imageqw, (xheight,xwidth))
            imagegray = pygame.transform.flip(imagegray, True, False)
            imagegray = pygame.transform.rotate(imagegray, 90)
            
            if zoom == 0:
                windowSurfaceObj.blit(imagegray, (a-h_crop,b-v_crop))
            else:
                windowSurfaceObj.blit(imagegray, (0,0))
          # show detected pixels if required
          if preview == 1 and np.shape(gray) == np.shape(oldimg):
            if zoom == 0:
                imagep = pygame.transform.scale(imagep, (h_crop*2,v_crop*2))
                windowSurfaceObj.blit(imagep, (a-h_crop,b-v_crop))
            elif preview == 1:
                imagep = pygame.transform.scale(imagep, (xwidth,xheight))
                windowSurfaceObj.blit(imagep, (0,0))
            #if square == 0:
            #    pygame.draw.rect(windowSurfaceObj, (255,255,0), Rect(int(cwidth/2) - int(xheight/2) ,0 ,int(xheight),int(xheight)), 1)
            #    pygame.draw.line(windowSurfaceObj, (255,255,0), (int(cwidth/2) - 50,int(xheight/2)),(int(cwidth/2) + 50, int(xheight/2)))
            #    pygame.draw.line(windowSurfaceObj, (255,255,0), (int(cwidth/2),int(xheight/2)-50),(int(cwidth/2), int(xheight/2)+50))
          if zoom == 0:
              pygame.draw.rect(windowSurfaceObj, (0,255,0), Rect(a - h_crop,b - v_crop ,h_crop*2,v_crop*2), 2)
              nmask = pygame.surfarray.make_surface(mask)
              nmask = pygame.transform.scale(nmask, (h_crop*2,v_crop*2))
              nmask.set_colorkey((0,0,50))
              nmask.set_alpha(m_alpha)
              windowSurfaceObj.blit(nmask, (a - h_crop,b - v_crop))
                                   
          if preview == 1 and detect == 1:
            now = datetime.datetime.now()
            timestamp = now.strftime("%y%m%d%H%M%S")
            pygame.image.save(windowSurfaceObj, h_user + '/scr' + str(timestamp) + '.jpg')
          if Pi_Cam == 3 and fxz != 1 and zoom == 0 and menu == 7:
            pygame.draw.rect(windowSurfaceObj,(200,0,0),Rect(int(fxx*cwidth),int(fxy*cheight*.75),int(fxz*cwidth),int(fxz*cheight)),1)
          pygame.display.update(0,0,scr_width-bw,scr_height)

        if vidjr != 1:
           oldimg[:] = gray[:]
        vidjr = 0

        if fcount < max_fcount and Pi != 5 and (Pi_Cam == 5 or Pi_Cam == 6) and v3_f_mode == 0:
            Capture = 0
            if menu == -1:
                button(0,0,0)
                text(0,0,0,0,1,"CAPTURE",16,7)
                text(0,0,3,1,1,vf,14,7)
                rep = 0
        elif Pi != 5 and (Pi_Cam == 5 or Pi_Cam == 6) and rep == 0 and v3_f_mode == 0:
            Capture = old_capture
            if menu == -1:
                if Capture == 1 and frames + ram_frames == 0:
                    button(0,0,4)
                    text(0,0,6,0,1,"CAPTURE",16,4)
                    text(0,0,3,1,1,vf,14,4)
                elif Capture == 1 and frames + ram_frames > 0:
                    button(0,0,5)
                    text(0,0,3,0,1,"CAPTURE",16,2)
                    text(0,0,3,1,1,vf,14,2)
                else:
                    button(0,0,0)
                    text(0,0,0,0,1,"CAPTURE",16,7)
                    text(0,0,3,1,1,vf,14,7)
                text(0,9,3,0,1," ",14,7)
                text(0,9,3,1,1," ",14,7)
            rep = 1

        # ARDUCAM AF
        if (Pi_Cam == 5 or Pi_Cam == 6) and v3_f_mode == 0 and fcount < max_fcount and Pi != 5:
                foc = cv2.Laplacian(gray, cv2.CV_64F).var()
                if menu == -1:
                    text(0,9,3,0,1,"Focusing...",14,7)
                    text(0,9,3,1,1,str(int(foc)),14,7)
                if foc >= min_foc:
                    ran = 0
                else:
                    focus = random.randint(10,3990)
                    fcount = 1
                    ran = 1
                    old_foc = foc
                if (int(foc) >= int(old_foc) or fcount == 0) and ran == 0:
                    if fcount == 0:
                        if focus < int(2000):
                            focus  += fstep
                        else:
                            focus  -= fstep
                    else:        
                        focus  += fstep
                elif ran == 0:
                    fstep = -fstep
                    focus += fstep
                old_foc = foc
                if focus < 10 or focus > 3990:
                    focus = int(2000)
                    fcount = 0
                os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub5) + " -c focus_absolute=" + str(focus))
                time.sleep(.5)
                fcount += 1
                
    save_config = 0
    #check for any mouse button presses
    for event in pygame.event.get():
        if (event.type == MOUSEBUTTONUP):
            timer = time.monotonic()
            mousex, mousey = event.pos
            # set crop position
            if mousex < xwidth and zoom == 0 and ((menu != 7 or (Pi_Cam == 3 and v3_f_mode == 1)) or (Pi_Cam == 5 or Pi_Cam == 6)) and event.button != 3:
                if (Pi_Cam == 5 or Pi_Cam == 6):
                    fcount = 0
                a = mousex
                b = mousey
                if a + h_crop > xwidth:
                   a = xwidth - h_crop
                if b + v_crop > xheight:
                   b = xheight - v_crop
                if a - h_crop < 0:
                   a = h_crop
                if b - v_crop < 0:
                   b = v_crop
                a2 = int(a * (cap_width/cwidth))
                b2 = int(b * (cap_height/xheight))
                oldimg = []
                save_config = 1
                
            # set mask
            if mousex < xwidth and zoom == 0 and event.button == 3 :
                if mousex > a - h_crop and mousex < a + h_crop and mousey < b + v_crop and mousey > b - v_crop:
                    mx = int((mousex - (a - h_crop)) *(cap_width/cwidth))
                    my = int((mousey - (b - v_crop)) *(cap_height/xheight))
                    su = int(h_crop/5)
                    sl = 0-su
                    if mask[mx][my] == 0:
                        for aa in range(sl,su):
                            for bb in range(sl,su):
                                if mx + bb > 0 and my + aa > 0 and mx + bb < h_crop * ((2 * cap_width/cwidth) -0.1) and my + aa < v_crop * ((2 * cap_height/xheight) - 0.1):
                                    mask[mx + bb][my + aa] = 1
                    else:
                        for aa in range(sl,su):
                            for bb in range(sl,su):
                                if mx + bb > 0 and my + aa > 0 and mx + bb < h_crop * ((2 * cap_width/cwidth) -0.1) and my + aa < v_crop * ((2 * cap_height/xheight) - 0.1):
                                    mask[mx + bb][my + aa] = 0
                    nmask = pygame.surfarray.make_surface(mask)
                    nmask = pygame.transform.scale(nmask, (200,200))
                    nmask = pygame.transform.rotate(nmask, 270)
                    nmask = pygame.transform.flip(nmask, True, False)
                    pygame.image.save(nmask,h_user + '/CMask.bmp')
                 
            # set v3 camera autofocus position 
            if mousex < xwidth and zoom == 0 and menu == 7 and Pi_Cam == 3 and (v3_f_mode == 0 or v3_f_mode == 2):
                c = mousex
                d = mousey
                fxx = (c - 25)/cwidth
                d  = min(d,int((cheight - 25) * .75))
                fxy = ((d - 20) * 1.3333)/cheight
                fxz = 50/cwidth
                text(0,0,3,1,1,"Spot",14,7)
                if trace == 1:
                    print("v3 AUTO FOCUS POSN")
                restart = 1
                a = mousex
                b = mousey
                if a + h_crop > xwidth:
                   a = xwidth - h_crop
                if b + v_crop > xheight:
                   b = xheight - v_crop
                if a - h_crop < 0:
                   a = h_crop
                if b - v_crop < 0:
                   b = v_crop
                a2 = int(a * (cap_width/cwidth))
                b2 = int(b * (cap_height/xheight))
                oldimg = []
                save_config = 1
            # keys   
            elif mousex > cwidth:
                g = int(mousey/bh)
                gv = mousey - (g * bh)
                h = 0
                hp = (scr_width - mousex) / bw
                if hp < 0.5:
                    h = 1
                if g == 0 and menu == -1 :
                    # CAPTURE
                    Capture +=1
                    #if zoom > 0:
                    #    restart = 1
                    zoom = 0
                    if Capture > 1:
                        Capture = 0
                        button(0,0,0)
                        text(0,0,0,0,1,"CAPTURE",16,7)
                        text(0,0,3,1,1,vf,14,7)
                        timer10 = 0
                    else:
                        num = 0
                        button(0,0,4)
                        text(0,0,6,0,1,"CAPTURE",16,4)
                        text(0,0,3,1,1,vf,14,4)
                    old_cap = Capture
                    save_config = 1

                elif g == 10 and menu == -1 and event.button == 3:
                    # EXIT
                    if trace == 1:
                         print ("Step 13 EXIT")
                    # Move RAM FRAMES to SD CARD
                    if ram_frames > 0:
                        if menu == -1 :
                            button(0,0,1)
                            text(0,0,5,0,1,"CAPTURE",16,0)
                        zpics = glob.glob('/run/shm/2*.jpg')
                        zpics.sort()
                        for xx in range(0,len(zpics)):
                            shutil.copy(zpics[xx], h_user + '/Pictures/')
                    # Move MP4s to USB if present
                    USB_Files  = []
                    USB_Files  = (os.listdir(m_user))
                    if len(USB_Files) > 0:
                        spics = glob.glob(h_user + '/Videos/*.mp4')
                        spics.sort()
                        for xx in range(0,len(spics)):
                            movi = spics[xx].split("/")
                            if not os.path.exists(m_user + "/" + USB_Files[0] + "/Videos/" + movi[4]):
                                shutil.move(spics[xx],m_user + "/" + USB_Files[0] + "/Videos/")
                    # Move CAM1 jpgs to USB if present
                    USB_Files  = []
                    USB_Files  = (os.listdir(m_user))
                    if len(USB_Files) > 0:
                        spics = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
                        spics.sort()
                        for xx in range(0,len(spics)):
                            movi = spics[xx].split("/")
                            #if not os.path.exists(m_user + "/" + USB_Files[0] + "/Pictures/" + movi[4]):
                            shutil.move(spics[xx],m_user + "/" + USB_Files[0] + "/Pictures/")
                    if use_gpio == 1 and fan_ctrl == 1:
                        led_fan.value = 0
                    pygame.quit()
                    poll = p.poll()
                    if poll == None:
                        os.killpg(p.pid, signal.SIGTERM)

                elif g == 9 and menu == 4:
                  if event.button == 3:
                    # Check for usb_stick and Move Video JPGs to it
                    USB_Files  = []
                    USB_Files  = (os.listdir(m_user))
                    text(0,9,3,0,1,"Moving JPGs",14,7)
                    text(0,9,3,1,1,"to USB",14,7)
                    if len(USB_Files) > 0 and frames + ram_frames > 0:
                        if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Pictures/") :
                            os.system('mkdir ' + m_user + "/'" + USB_Files[0] + "'/Pictures/")
                        zpics = glob.glob( h_user + '/Pictures/*.jpg')
                        zpics.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(zpics)-1):
                            Tideos = zpics[x].split("/")
                            if Tideos[len(Tideos) - 1][:-10] != z:
                                z = Tideos[len(Tideos) - 1][:-10]
                                outvids.append(z)
                        for xz in range(0,len(outvids)):
                            xzpics = glob.glob(h_user + '/Pictures/' + outvids[xz] + '*.jpg')
                            xzpics.sort()
                            for xx in range(0,len(xzpics)):
                                shutil.move(xzpics[xx],m_user + '/' + USB_Files[0] + "/Pictures/")
                        frames = 0
                        zpics = glob.glob('/run/shm/2*.jpg')
                        zpics.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(zpics)-1):
                            Tideos = zpics[x].split("/")
                            if Tideos[len(Tideos) - 1][:-10] != z:
                                z = Tideos[len(Tideos) - 1][:-10]
                                outvids.append(z)
                        for xz in range(0,len(outvids)):
                            if menu == -1:
                                text(0,8,3,1,1,str(len(outvids) - xz),14,7)
                            xzpics = glob.glob('/run/shm/' + outvids[xz] + '*.jpg')
                            xzpics.sort()
                            for xx in range(0,len(xzpics)):
                                shutil.move(xzpics[xx],m_user + "/'" + USB_Files[0] + "'/Pictures/")
                        ram_frames = 0
                        vf = str(ram_frames) + " - " + str(frames)
                        if Pi == 5 and cam2 != "2":
                            vf = vf + " - " + str(len(photos))
                    text(0,9,2,0,1,"Move JPGs",14,7)
                    text(0,9,2,1,1,"to USB",14,7)
                    if reboot == 1:
                        os.system('reboot')
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
                    text(0,1,3,1,1,str(detection),14,7)
                    save_config = 1
                    
                elif g == 3 and menu == 0:
                    # Threshold
                    if (h == 1 and event.button == 1) or event.button == 4:
                        threshold +=1
                        threshold = min(threshold,threshold2 - 1)
                        text(0,3,2,0,1,"Low Threshold",14,7)
                        text(0,3,3,1,1,str(threshold),14,7)
                        timer10 = 0
                    else:
                        threshold -=1
                        threshold = max(threshold,0)
                        text(0,3,2,0,1,"Low Threshold",14,7)
                        text(0,3,3,1,1,str(threshold),14,7)
                        timer10 = 0
                    save_config = 1

                elif g == 4 and menu == 0:
                    # High Threshold
                    if (h == 1 and event.button == 1) or event.button == 4:
                        threshold2 +=1
                        threshold2 = min(threshold2,255)
                        text(0,4,2,0,1,"High Threshold",14,7)
                        text(0,4,3,1,1,str(threshold2),14,7)
                        timer10 = 0
                    else:
                        threshold2 -=1
                        threshold2 = max(threshold2,threshold + 1)
                        text(0,4,2,0,1,"High Threshold",14,7)
                        text(0,4,3,1,1,str(threshold2),14,7)
                        timer10 = 0
                    save_config = 1

                elif g == 2 and menu == 0:
                    # High Detection
                    if (h == 1 and event.button == 1) or event.button == 4:
                        det_high +=1
                        det_high = min(det_high,100)
                        text(0,2,3,1,1,str(det_high),14,7)
                    else:
                        det_high -=1
                        det_high = max(det_high,detection)
                        text(0,2,3,1,1,str(det_high),14,7)
                    save_config = 1
                    
                elif g == 1 and menu == -1:
                    # RECORD
                    record = 1
                    button(0,1,1)
                    text(0,1,3,0,1,"RECORD",16,0)
                    
                elif g == 8 and menu == 4 and use_gpio == 1:
                    # EXT Trigger
                    ES +=1
                    if ES > 2:
                        ES = 0
                    if ES == 0:
                        text(0,8,3,1,1,"OFF",14,7)
                    elif ES == 1:
                        text(0,8,3,1,1,"Short",14,7)
                    else:
                        text(0,8,3,1,1,"Long",14,7)
                    save_config = 1

                elif g == 9 and menu == 7:
                    # SHUTDOWN HOUR
                    if h == 1:
                        sd_hour +=1
                        if sd_hour > 23:
                            sd_hour = 0
                    if h == 0:
                        sd_hour -=1
                        if sd_hour  < 0:
                            sd_hour = 23
                    text(0,9,1,0,1,"Shutdown Hour",14,7)
                    text(0,9,3,1,1,str(sd_hour) + ":00",14,7)
                    save_config = 1
                    
                elif g == 9 and (menu == 1 or menu == 8):
                    # ZOOM
                    zoom +=1
                    if zoom == 1:
                        button(0,9,1)
                        text(0,9,1,0,1,"Zoom",14,0)
                        if event.button == 3:
                            preview = 1
                    else:
                        zoom = 0
                        button(0,9,0)
                        text(0,9,2,0,1,"Zoom",14,7)
                        preview = 0

                elif g == 0 and menu == 8:
                    # Photo Timer
                    if (h == 1 and event.button == 1) or event.button == 4:
                        photo_timer +=0.1
                        photo_timer = min(photo_timer,10)
                        text(0,0,3,1,1,str(photo_timer)[0:3],14,7)
                    else:
                        photo_timer -=0.1
                        photo_timer = max(photo_timer,0.3)
                        text(0,0,3,1,1,str(photo_timer)[0:3],14,7)
                    save_config = 1

                elif g == 3 and menu == 7:
                    # ZOOM
                    zoom +=1
                    if zoom == 1:
                        button(0,3,1)
                        text(0,3,1,0,1,"Zoom",14,0)
                        if event.button == 3:
                            preview = 1
                    else:
                        zoom = 0
                        button(0,3,0)
                        text(0,3,2,0,1,"Zoom",14,7)
                        preview = 0
                    
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
                        text(0,2,3,1,1,str(int(speed/1000)),14,7)
                    else:
                        text(0,2,0,1,1,str(int(speed/1000)),14,7)
                    text(0,1,3,1,1,modes[mode],14,7)
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
                        text(0,2,0,1,1,str(int(speed/1000)),14,7)
                    else:
                        text(0,2,3,1,1,str(int(speed/1000)),14,7)
                    save_config = 1
                    
                elif g == 3 and menu == 1:
                    # GAIN
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        gain +=1
                        gain = min(gain,max_gain)
                    else:
                        gain -=1
                        gain = max(gain,0)
                    if gain > 0:
                        text(0,3,3,1,1,str(gain),14,7)
                    else:
                        text(0,3,3,1,1,"Auto",14,7)
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
                    text(0,4,3,1,1,str(brightness),14,7)
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
                    text(0,5,3,1,1,str(contrast),14,7)
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
                    text(0,6,3,1,1,str(ev),14,7)
                    save_config = 1

                elif g == 1 and menu == 8:
                    # MODE2
                    restart = 1
                    if h == 1 :
                        mode2 +=1
                        mode2 = min(mode2,2)
                    else:
                        mode2 -=1
                        mode2 = max(mode2,0)
                    if mode2 == 0:
                        text(0,2,3,1,1,str(int(speed2/1000)),14,7)
                        framerate2 = int((1/speed2)*1000000)
                        framerate2 = min(framerate2,60)
                        framerate2 = max(framerate2,1)
                    else:
                        text(0,2,0,1,1,str(int(speed2/1000)),14,7)
                        framerate2 = 25
                    text(0,1,3,1,1,modes[mode2],14,7)
                    text(0,8,3,1,1,str(framerate2),14,7)
                    save_config = 1
                    
                elif g == 2 and menu == 8:
                    # Shutter Speed2
                    if mode2 == 0:
                        restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        speed2 +=1000
                        if speed2 > 50000:
                            speed2 +=9000
                        speed2 = min(speed2,100000)
                    else:
                        speed2 -=1000
                        if speed2 > 50000:
                            speed2 -=9000
                        speed2 = max(speed2,1)
                    if mode2 != 0:
                        text(0,2,0,1,1,str(int(speed2/1000)),14,7)
                    else:
                        text(0,2,3,1,1,str(int(speed2/1000)),14,7)
                    framerate2 = int((1/speed2)*1000000)
                    framerate2 = min(framerate2,60)
                    framerate2 = max(framerate2,1)
                    text(0,8,3,1,1,str(framerate2),14,7)
                    save_config = 1
                    
                elif g == 3 and menu == 8:
                    # GAIN2
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        gain2 +=1
                        gain2 = min(gain2,max_gain)
                    else:
                        gain2 -=1
                        gain2 = max(gain2,0)
                    if gain2 > 0:
                        text(0,3,3,1,1,str(gain2),14,7)
                    else:
                        text(0,3,3,1,1,"Auto",14,7)
                    save_config = 1
                    
                elif g == 4 and menu == 8:
                    # BRIGHTNESS2
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        brightness2 +=1
                        brightness2 = min(brightness2,100)
                    else:
                        brightness2 -=1
                        brightness2 = max(brightness2,0)
                    text(0,4,3,1,1,str(brightness2),14,7)
                    save_config = 1
                    
                elif g == 5 and menu == 8:
                    # CONTRAST2
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        contrast2 +=1
                        contrast2 = min(contrast2,100)
                    else:
                        contrast2 -=1
                        contrast2 = max(contrast2,-100)
                    text(0,5,3,1,1,str(contrast2),14,7)
                    save_config = 1

                elif g == 6 and menu == 8:
                    # EV2
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        ev2 +=1
                        ev2 = min(ev2,12)
                    else:
                        ev2 -=1
                        ev2 = max(ev2,-12)
                    text(0,6,5,0,1,"eV",14,7)
                    text(0,6,3,1,1,str(ev2),14,7)
                    save_config = 1
                    
                elif g == 7 and menu == 1:
                    # Metering
                    if h == 1:
                        meter +=1
                        meter = min(meter,len(meters)-1)
                    else:
                        meter -=1
                        meter = max(meter,0)
                    text(0,7,3,1,1,str(meters[meter]),14,7)
                    restart = 1
                    save_config = 1

                elif g == 7 and menu == 8:
                    # Metering2
                    if h == 1:
                        meter2 +=1
                        meter2 = min(meter2,len(meters)-1)
                    else:
                        meter2 -=1
                        meter2 = max(meter2,0)
                    text(0,7,3,1,1,str(meters[meter2]),14,7)
                    restart = 1
                    save_config = 1

                elif g == 3 and menu == 2:
                    # PRE FRAMES
                    if h == 1:
                        pre_frames +=1
                        pre_frames = min(pre_frames,100)
                    else:
                        pre_frames -=1
                        pre_frames = max(pre_frames,0)
                    text(0,3,3,1,1,str(pre_frames),14,7)
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
                    text(0,8,3,1,1,str(saturation),14,7)
                    save_config = 1
                   
                elif g == 9 and menu == 7 and scientif == 1:
                    # SCIENTIFIC
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        scientific +=1
                        scientific = min(scientific,1)
                    else:
                        scientific -=1
                        scientific = max(scientific,0)
                    text(0,9,3,1,1,str(scientific),14,7)

                elif g == 2 and menu == 2:
                    # FPS
                    if (h == 1 and event.button == 1) or event.button == 4:
                        fps +=1
                        fps = min(fps,80)
                    else:
                        fps -=1
                        fps = max(fps,5)
                    pre_frames = 2 * fps
                    text(0,3,3,1,1,str(pre_frames),14,7)
                    text(0,2,3,1,1,str(fps),14,7)
                    text(0,1,3,1,1,str(v_length/1000) + "  (" + str(int(fps*(v_length/1000))) +")",14,7)
                    mp4_fps = fps
                    restart = 1
                    save_config = 1

                elif g == 8 and menu == 8:
                    # FPS2
                    if (h == 1 and event.button == 1) or event.button == 4:
                        framerate2 +=1
                        framerate2 = min(framerate2,80)
                    else:
                        framerate2 -=1
                        framerate2 = max(framerate2,5)
                    text(0,8,3,1,1,str(framerate2),14,7)
                    restart2 = 1
                    save_config = 1

                elif g == 4 and menu == 2:
                    # AWB setting
                    if (h == 1 and event.button == 1) or event.button == 4:
                        awb +=1
                        awb = min(awb,len(awbs)-1)
                    else:
                        awb -=1
                        awb = max(awb,0)
                    text(0,4,3,1,1,str(awbs[awb]),14,7)
                    if awb == 0:
                        text(0,5,3,1,1,str(red)[0:3],14,7)
                        text(0,6,3,1,1,str(blue)[0:3],14,7)
                    else:
                        text(0,5,0,1,1,str(red)[0:3],14,7)
                        text(0,6,0,1,1,str(blue)[0:3],14,7)
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
                    text(0,5,3,1,1,str(red)[0:3],14,7)
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
                    text(0,6,3,1,1,str(blue)[0:3],14,7)
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
                    text(0,7,3,1,1,str(sharpness),14,7)
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
                    text(0,8,3,1,1,str(denoises[denoise]),14,7)
                    save_config = 1

                elif g == 0 and menu == 1:
                    # QUALITY
                    restart = 1
                    if (h == 1 and event.button == 1) or event.button == 4:
                        quality +=1
                        quality = min(quality,100)
                    else:
                        quality -=1
                        quality = max(quality,0)
                    text(0,0,3,1,1,str(quality),14,7)
                    save_config = 1

                elif g == 0 and menu == 3  and show == 1 and len(photos) > 0 and Pi == 5 and cam2 != "2":
                    # SHOW next photo
                    text(0,1,3,1,1,"",14,7)
                    text(0,6,3,1,1,"PHOTO ",14,7)
                    text(0,7,3,1,1,"ALL Photos ",14,7)
                    if en_photo == 1:
                      if (h == 1 and event.button == 1) or event.button == 4:
                        q +=1
                        if q > len(photos)-1:
                            q = 0
                      else:
                        q -=1
                        if q < 0:
                            q = len(photos)-1
                    en_photo = 1
                    if os.path.getsize(photos[q]) > 0:
                        text(0,0,3,1,1,str(q+1) + " / " + str(len(photos)),14,7)
                        if len(photos) > 0:
                            image = pygame.image.load(photos[q])
                            cropped = pygame.transform.scale(image, (cwidth,xheight))
                            windowSurfaceObj.blit(cropped, (0, 0))
                            fontObj = pygame.font.Font(None, 25)
                            msgSurfaceObj = fontObj.render(str(photos[q]), False, (255,255,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,10)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(len(photos))), False, (255,128,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,35)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            pygame.display.update()
                    
                elif g == 1 and (menu == 3 or menu == 5) and show == 1 and len(zzpics) > 0:
                    # SHOW next video
                    if en_photo == 1 and square == 1:
                        pygame.draw.rect(windowSurfaceObj,blackColor,Rect(0,0,scr_width-bw,scr_height))
                    en_photo = 0
                    if menu == 3:
                        text(0,0,3,1,1,str(len(photos)),14,7)
                        text(0,6,3,1,1,"VIDEO ",14,7)
                        text(0,7,3,1,1,"ALL VIDS ",14,7)
                    frame = 0
                    sframe = -1
                    eframe = -1
                    trig = 1
                    text(0,3,2,0,1,"Frame ",14,7)
                    text(0,3,3,1,1," ",14,7)
                    if menu == 3:
                        text(0,5,0,0,1,"DELETE",14,7)
                        text(0,5,0,1,1,"START - END",14,7)
                        
                        text(0,4,0,0,1,"DELETE ",14,7)
                        text(0,4,0,1,1,"FRAME ",14,7)
                    elif menu == 5:
                        text(0,4,0,0,1,"DELETE",14,7)
                        text(0,4,0,1,1,"START - END",14,7)
                    if (h == 1 and event.button == 1) or event.button == 4:
                        q +=1
                        if q > len(zzpics)-1:
                            q = 0
                    else:
                        q -=1
                        if q < 0:
                            q = len(zzpics)-1
                    tlen = int(fps*(v_length/1000)) + pre_frames
                    if os.path.getsize(zzpics[q]) > 0:
                        text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),14,7)
                        if len(zzpics) > 0:
                            play = glob.glob(zzpics[q][:-10] + "*.jpg")
                            play.sort()
                            image = pygame.image.load(zzpics[q])
                            cropped = pygame.transform.scale(image, (xwidth,xheight))
                            windowSurfaceObj.blit(cropped, (0, 0))
                            fontObj = pygame.font.Font(None, 25)
                            msgSurfaceObj = fontObj.render(str(zzpics[q]), False, (255,255,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,10)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            if len(play) >= tlen:
                                msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,0,0))
                            else:
                                msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,128,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,35)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            pygame.display.update()

                elif en_photo == 1 and g == 6 and menu == 3 and show == 1 and len(photos) > 0 and event.button == 3:
                    # DELETE A PHOTO
                    try:
                      fontObj = pygame.font.Font(None, 70)
                      msgSurfaceObj = fontObj.render("DELETING....", False, (255,0,0))
                      msgRectobj = msgSurfaceObj.get_rect()
                      msgRectobj.topleft = (10,100)
                      windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                      pygame.display.update()
                      os.remove(photos[q])
                    except:
                        pass
                    photos = []
                    photos = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
                    photos.sort()
                    #q = 0
                    if q > len(photos)-1:
                        q -=1
                    if len(photos) > 0 and os.path.getsize(photos[q]) > 0:
                        text(0,0,3,1,1,str(q+1) + " / " + str(len(photos)),14,7)
                        if len(photos) > 0:
                            image = pygame.image.load(photos[q])
                            cropped = pygame.transform.scale(image, (cwidth,xheight))
                            windowSurfaceObj.blit(cropped, (0, 0))
                            fontObj = pygame.font.Font(None, 25)
                            msgSurfaceObj = fontObj.render(str(photos[q]), False, (255,255,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,10)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(len(photos))), False, (255,128,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,35)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            pygame.display.update()
                    else:
                        en_photo = 0
                        main_menu()

                elif en_photo == 0 and g == 6 and menu == 3 and show == 1 and frames + ram_frames > 0 and len(zzpics) > 0 and event.button == 3:
                    # DELETE A VIDEO
                    sframe = -1
                    eframe = -1
                    trig = 1
                    text(0,3,3,1,1," ",14,7)
                    text(0,4,0,1,1,"FRAME ",14,7)
                    text(0,3,2,0,1,"Frame ",14,7)
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
                    except:
                        pass
                    zzpics = []
                    rpics = []
                    zzpics = glob.glob(h_user + '/Pictures/*99999.jpg')
                    rpics = glob.glob('/run/shm/*99999.jpg')
                    frames = 0
                    ram_frames = 0
                    rpics.sort()
                    for x in range(0,len(rpics)):
                         zzpics.append(rpics[x])
                    if len(USB_Files) > 0:
                        upics = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/*99999.jpg")
                        for x in range(0,len(upics)):
                            zzpics.append(upics[x])
                    zzpics.sort()
                    z = ""
                    y = ""
                    for x in range(0,len(zzpics)):
                        Tideos = zzpics[x].split("/")
                        if len(Tideos) >= 5:
                            if Tideos[len(Tideos) - 1][:-10] != z:
                                z = Tideos[len(Tideos) - 1][:-10]
                                frames +=1
                        else:
                            if Tideos[len(Tideos) - 1][:-10] != y:
                                y = Tideos[len(Tideos) - 1][:-10]
                                ram_frames +=1
                    if q > len(zzpics)-1:
                        q -=1
                    if len(zzpics) > 0:
                      try:
                        tlen = int(fps*(v_length/1000)) + pre_frames
                        play = glob.glob(zzpics[q][:-10] + "*.jpg")
                        play.sort()
                        image = pygame.image.load(zzpics[q])
                        cropped = pygame.transform.scale(image, (xwidth,xheight))
                        windowSurfaceObj.blit(cropped, (0, 0))
                        fontObj = pygame.font.Font(None, 25)
                        msgSurfaceObj = fontObj.render(str(zzpics[q]), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (10,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        if len(play) >= tlen:
                            msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,0,0))
                        else:
                            msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,128,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (10,35)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                      except:
                          pass
                    else:
                        show = 0
                        main_menu()
                        q = 0
                        of = 0
                        ram_frames = 0
                        frames = 0
                        snaps = 0
                        restart = 1
                    if ram_frames + frames > 0 and (menu == 3 or menu == 5):
                        text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),14,7)
                    elif (menu == 3 or menu == 5):
                        text(0,1,3,1,1," ",14,7)
                    vf = str(ram_frames) + " - " + str(frames)
                    if Pi == 5 and cam2 != "2":
                        vf = vf + " - " + str(len(photos))
                    if square == 1:
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(xheight,0,int(xheight/2.3),scr_height))
                    pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,scr_width-bw,scr_height))
                    oldimg = []
                    time.sleep(0.5)

                elif en_photo == 1 and g == 7 and menu == 3 and show == 1 and len(photos) > 0:
                    # DELETE ALL PHOTOS
                    text(0,3,3,1,1," ",14,7)
                    text(0,4,0,1,1,"FRAME ",14,7)
                    text(0,3,2,0,1,"Frame ",14,7)
                    if event.button == 3:
                        fontObj = pygame.font.Font(None, 70)
                        msgSurfaceObj = fontObj.render("DELETING....", False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (10,100)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                        try:
                            zpics = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
                            for xx in range(0,len(zpics)):
                                os.remove(zpics[xx])
                            photos = []
                        except:
                             pass
                        text(0,1,3,1,1," ",14,7)
                        menu = -1
                        Capture = old_cap
                        main_menu()
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,scr_width-bw,scr_height))
                        show = 0
                        restart = 1
                   
                        
                elif en_photo == 0 and g == 7 and menu == 3:
                    # DELETE ALL VIDEOS
                    sframe = -1
                    eframe = -1
                    of = 0
                    trig = 1
                    text(0,3,3,1,1," ",14,7)
                    text(0,4,0,1,1,"FRAME ",14,7)
                    text(0,3,2,0,1,"Frame ",14,7)
                    if event.button == 3:
                        fontObj = pygame.font.Font(None, 70)
                        msgSurfaceObj = fontObj.render("DELETING....", False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (10,100)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                        try:
                            zpics = glob.glob('/run/shm/2*.jpg')
                            for xx in range(0,len(zpics)):
                                os.remove(zpics[xx])
                            ram_frames = 0
                            zpics = glob.glob(h_user + '/Pictures/2*.jpg')
                            for xx in range(0,len(zpics)):
                                os.remove(zpics[xx])
                            frames = 0
                            if len(USB_Files) > 0:
                                upics = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/*.jpg")
                                for xx in range(0,len(upics)):
                                    os.remove(upics[xx])
                            vf = str(ram_frames) + " - " + str(frames)
                            if Pi == 5 and cam2 != "2":
                                vf = vf + " - " + str(len(photos))
                        except:
                             pass
                        text(0,1,3,1,1," ",14,7)
                        menu = -1
                        Capture = old_cap
                        main_menu()
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,scr_width-bw,scr_height))
                        show = 0
                        restart = 1
                        oldimg = []

                elif en_photo == 0 and g == 2 and (menu == 3 or menu == 5) and show == 1:
                    # PLAY VIDEO
                    sframe = -1
                    eframe = -1
                    trig   = 0
                    text(0,3,3,1,1," ",14,7)
                    text(0,3,2,0,1,"Frame ",14,7)
                    button(0,2,0)
                    text(0,2,3,0,1,"STOP",14,7)
                    text(0,2,3,1,1,"Video",14,7)
                    if menu == 3:
                        text(0,4,3,0,1,"DELETE ",14,7)
                        text(0,4,3,1,1,"FRAME ",14,7)
                        text(0,5,3,0,1,"DELETE ",14,7)
                        text(0,5,3,1,1,"START - END",14,7)
                    else:
                        text(0,4,3,0,1,"DELETE",14,7)
                        text(0,4,3,1,1,"START - END",14,7)
                    step = 1
                    if hp > 0.75:
                        step = -4
                    elif hp > 0.5:
                        step = -1
                    elif hp < 0.25:
                        step = 4
                    elif hp < 0.5:
                        step = 1
                    play = glob.glob(zzpics[q][:-10] + "*.jpg")
                    play.sort()
                    #frame = 0
                    st = 0
                    while frame < len(play) - 1 and st == 0:
                        image = pygame.image.load(play[frame])
                        image = pygame.transform.scale(image, (xwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 25)
                        msgSurfaceObj = fontObj.render(str(play[int(frame)]), False, (0,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(len(zzpics)) + " - " + str(frame+1) + "/" + str(len(play)-1)), False, (0,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,35)
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
                            if frame < 0:
                                frame = 0
                                st = 1
                                
                    if st == 0:   
                      if os.path.exists(zzpics[q][:-10] + "_99999.jpg"):
                        image = pygame.image.load(zzpics[q][:-10] + "_99999.jpg")
                      elif os.path.exists(zzpics[q][:-10] + "_00001.jpg"):
                        image = pygame.image.load(zzpics[q][:-10] + "_00001.jpg")
                      else:
                        image = pygame.image.load(zzpics[q])
                      image = pygame.transform.scale(image, (xwidth,xheight))
                      windowSurfaceObj.blit(image, (0, 0))
                      fontObj = pygame.font.Font(None, 25)
                      msgSurfaceObj = fontObj.render(str(zzpics[q]), False, (255,0,0))
                      msgRectobj = msgSurfaceObj.get_rect()
                      msgRectobj.topleft = (0,10)
                      windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                      msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(len(zzpics))), False, (255,0,0))
                      msgRectobj = msgSurfaceObj.get_rect()
                      msgRectobj.topleft = (0,35)
                      windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                      frame = 0
                    text(0,2,2,0,1,"PLAY",14,7)
                    text(0,2,2,1,1,"<<   <    >   >>",14,7)
                    pygame.display.update()
                    
                elif en_photo == 0 and g == 3 and (menu == 3 or menu == 5) and show == 1 :
                    # NEXT / PREVIOUS FRAME
                    play = glob.glob(zzpics[q][:-10] + "*.jpg")
                    play.sort()
                    if (h == 1 and event.button == 1) or event.button == 4:
                        trig = 0
                        frame +=1
                        frame = min(frame,len(play)-2)
                        image = pygame.image.load(play[int(frame)])
                        image = pygame.transform.scale(image, (xwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 25)
                        msgSurfaceObj = fontObj.render(str(play[int(frame)]), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame+1)) + "/" + str(len(play)-1)), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,35)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                    elif (h == 0 and event.button == 1) or event.button == 5:
                        trig = 0
                        frame -=1
                        frame = max(frame,0)
                        image = pygame.image.load(play[int(frame)])
                        image = pygame.transform.scale(image, (xwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 25)
                        msgSurfaceObj = fontObj.render(str(play[int(frame)]), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame+1)) + "/" + str(len(play)-1)), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,35)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                    if menu == 3 and trig == 0:
                        text(0,5,3,0,1,"DELETE",14,7)
                        text(0,5,3,1,1,"START - END",14,7)
                        text(0,4,3,0,1,"DELETE ",14,7)
                        text(0,4,3,1,1,"FRAME ",14,7)
                    elif menu == 5:
                        text(0,4,3,0,1,"DELETE",14,7)
                        text(0,4,3,1,1,"START - END",14,7)
                        
                    if h == 1 and event.button == 3 and sframe > -1 and trig == 0 and menu == 3 and frame > sframe:
                        eframe = frame
                        text(0,3,3,1,1,str(sframe + 1) + " : " + str(eframe + 1),14,7)
                        text(0,4,3,1,1,"FRAMES ",14,7)
                        text(0,3,2,0,1,"Frames ",14,7)
                    elif h == 0 and event.button == 3 and sframe == -1 and trig == 0 and menu == 3:
                        sframe = frame
                        text(0,3,3,1,1,str(sframe + 1),14,7)
                        
                    elif h == 0 and event.button == 3 and sframe > -1 and menu == 3:
                        sframe = -1
                        eframe = -1
                        trig   = 1
                        text(0,3,3,1,1," ",14,7)
                        text(0,4,3,1,1,"FRAME ",14,7)
                        text(0,3,2,0,1,"Frame ",14,7)
                        
                                         
                     
                elif en_photo == 0 and ((g == 5 and menu == 3) or (g == 4 and menu == 5)) and show == 1 and frame > 0 and event.button == 3:
                    # DELETE from START or to END
                    sframe = -1
                    eframe = -1
                    text(0,3,3,1,1," ",14,7)
                    if menu == 3:
                        text(0,5,3,0,1,"DELETING",14,7)
                    else:
                        text(0,4,3,0,1,"DELETING",14,7)
                    remove = glob.glob(zzpics[q][:-10] + "*.jpg")
                    remove.sort()
                    if h == 1: # and event.button == 1) or event.button == 4:
                        for tt in range(int(frame) + 1,len(remove)-1):
                            if remove[tt][40:45] != "99999":
                                os.remove(remove[tt])
                            fr = 1
                    else:
                        for tt in range(0,int(frame)):
                            if remove[tt][40:45] != "99999":
                                os.remove(remove[tt])
                            fr = 0
                            
                    play = glob.glob(zzpics[q][:-10] + "*.jpg")
                    play.sort()
                    if fr == 0:
                        frame = 0
                        for x in range(0,len(play)):
                            fxa = "00000" + str(x)
                            fxb = play[x].split("_")
                            if fxb[1] != "99999.jpg":
                                os.rename(play[x],fxb[0] + "_" + str(fxa[-5:]) + '.jpg')
                        play.sort()
                    else:
                        frame = len(play)-2
                    image = pygame.image.load(play[int(frame)])
                    image = pygame.transform.scale(image,(xwidth,xheight))
                    windowSurfaceObj.blit(image, (0, 0))
                    fontObj = pygame.font.Font(None, 25)
                    msgSurfaceObj = fontObj.render(str(play[int(frame)]), False, (255,255,0))
                    msgRectobj = msgSurfaceObj.get_rect()
                    msgRectobj.topleft = (0,10)
                    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame)+1) + "/" + str(len(play)-1)), False, (255,255,0))
                    msgRectobj = msgSurfaceObj.get_rect()
                    msgRectobj.topleft = (0,35)
                    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    if menu == 3:
                        text(0,5,0,0,1,"DELETE",14,7)
                        text(0,5,0,1,1,"START - END",14,7)
                    else:
                        text(0,4,0,0,1,"DELETE",14,7)
                        text(0,4,0,1,1,"START - END",14,7)
                    pygame.display.update()

                    
                elif en_photo == 0 and g == 4 and menu == 3 and show == 1 and trig == 0 and event.button == 3:
                    # DELETE FRAME or FRAMES
                    remove = glob.glob(zzpics[q][:-10] + "*.jpg")
                    remove.sort()
                    if sframe > -1 and eframe > -1 and eframe > sframe and trig == 0:
                        for tt in range(int(sframe),int(eframe) + 1):
                            if remove[tt][40:45] != "99999":
                                os.remove(remove[tt])
                    else:
                        if remove[int(frame)][40:45] != "99999":
                            os.remove(remove[int(frame)])
                    sframe = -1
                    eframe = -1
                    text(0,3,3,1,1," ",14,7)
                    text(0,4,3,1,1,"FRAME ",14,7)
                    text(0,3,2,0,1,"Frame ",14,7)
                    play = glob.glob(zzpics[q][:-10] + "*.jpg")
                    play.sort()
                    for x in range(0,len(play)):
                        fxa = "00000" + str(x)
                        fxb = play[x].split("_")
                        if fxb[1] != "99999.jpg":
                            os.rename(play[x],fxb[0] + "_" + str(fxa[-5:]) + '.jpg')
                    play = glob.glob(zzpics[q][:-10] + "*.jpg")
                    play.sort()
                    if len(play) > 1:
                        if frame > len(play) - 2:
                            frame = len(play) - 2
                        image = pygame.image.load(play[int(frame)])
                        image = pygame.transform.scale(image, (xwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 25)
                        msgSurfaceObj = fontObj.render(str(play[int(frame)]), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(len(zzpics)) + " - " + str(int(frame+1)) + "/" + str(len(play)-1)), False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,35)
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
                            Tideos = Videos[x].split("/")
                            if Tideos[len(Tideos) - 1][:-10] != z:
                                z = Tideos[len(Tideos) - 1][:-10]
                                outvids.append(z)
                        ram_frames = len(outvids)
                        # read list of existing SD Card & USB Video Files
                        if trace == 1:
                            print ("Step 11 READ SD FILES")
                        Videos = glob.glob(h_user + '/Pictures/*.jpg')
                        USB_Files  = (os.listdir(m_user))
                        if len(USB_Files) > 0:
                            upics = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/*.jpg")
                            upics.sort()
                            for x in range(0,len(upics)):
                                Videos.append(upics[x])
                        Videos.sort()
                        outvids = []
                        z = ""
                        for x in range(0,len(Videos)):
                            Tideos = Videos[x].split("/")
                            if Tideos[len(Tideos) - 1][:-10] != z:
                                z = Tideos[len(Tideos) - 1][:-10]
                                outvids.append(z)
                        frames = len(outvids)
                        vf = str(ram_frames) + " - " + str(frames)
                        if Pi == 5 and cam2 != "2":
                            vf = vf + " - " + str(len(photos))
                        main_menu()
                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,scr_width-bw,scr_height))
                        show = 0
                        restart = 1

                elif en_photo == 0 and g == 8 and menu == 3 and len(zzpics) > 0:
                    # SHOW ALL videos
                    sframe = -1
                    eframe = -1
                    text(0,3,3,1,1," ",14,7)
                    text(0,4,3,1,1,"FRAME ",14,7)
                    text(0,3,2,0,1,"Frame ",14,7)
                    frame = 0
                    if menu == 3:
                        text(0,5,0,0,1,"DELETE",14,7)
                        text(0,5,0,1,1,"START - END",14,7)
                        text(0,4,0,0,1,"DELETE ",14,7)
                        text(0,4,0,1,1,"FRAME ",14,7)
                    if menu == 5:
                        text(0,4,0,0,1,"DELETE",14,7)
                        text(0,4,0,1,1,"START - END",14,7)
                    text(0,8,2,0,1,"STOP",14,7)
                    text(0,8,2,1,1,"     ",14,7)
                    st = 0
                    nq = 0
                    while st == 0:
                        for q in range (0,len(zzpics)):
                            for event in pygame.event.get():
                                if (event.type == MOUSEBUTTONUP):
                                    mousex, mousey = event.pos
                                    if mousex > cwidth:
                                        buttonx = int(mousey/bh)
                                        nq = q
                                        if buttonx == 8:
                                            st = 1
                            
                            if os.path.getsize(zzpics[q]) > 0 and st == 0:
                                text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),14,7)
                                if len(zzpics) > 0:
                                    tlen = int(fps*(v_length/1000)) + pre_frames
                                    image = pygame.image.load(zzpics[q])
                                    cropped = pygame.transform.scale(image, (xwidth,xheight))
                                    windowSurfaceObj.blit(cropped, (0, 0))
                                    if square == 1:
                                        pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(xheight,0,int(xheight/2.3),scr_height))
                                    fontObj = pygame.font.Font(None, 25)
                                    msgSurfaceObj = fontObj.render(str(zzpics[q]), False, (255,0,0))
                                    msgRectobj = msgSurfaceObj.get_rect()
                                    msgRectobj.topleft = (10,10)
                                    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                                    if len(play) >= tlen:
                                        msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,0,0))
                                    else:
                                        msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,128,0))
                                    msgRectobj = msgSurfaceObj.get_rect()
                                    msgRectobj.topleft = (10,35)
                                    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                                    pygame.display.update()
                                    time.sleep(0.5)
                    text(0,8,2,0,1,"SHOW ALL",14,7)
                    text(0,8,2,1,1,"Videos",14,7)
                    q = nq - 1

                    
                elif g == 5 and menu == 0:
                    # H CROP
                    if (h == 1 and event.button == 1) or event.button == 4:
                        h_crop +=1
                        h_crop = min(h_crop,180)
                        if a-h_crop < 1 or b-v_crop < 1 or a+h_crop > cwidth or b+v_crop > int(cwidth/(cap_width/cap_height)):
                            h_crop -=1
                            new_crop = 0
                            new_mask = 0
                        h_crop2 = int(h_crop * (cap_width/cwidth))
                        text(0,5,3,1,1,str(h_crop),14,7)
                    else:
                        h_crop -=1
                        h_crop = max(h_crop,1)
                        h_crop2 = int(h_crop * (cap_width/cwidth))
                        text(0,5,3,1,1,str(h_crop),14,7)
                    mask,change = MaskChange()
                    save_config = 1
                    
                elif g == 6 and menu == 0:
                    # V CROP
                    if (h == 1 and event.button == 1) or event.button == 4:
                        v_crop +=1
                        v_crop = min(v_crop,180)
                        if a-h_crop < 1 or b-v_crop < 1 or a+h_crop > cwidth or b+v_crop > int(cwidth/(cap_width/cap_height)):
                            v_crop -=1
                        v_crop2 = int(v_crop * (cap_height/xheight))
                        text(0,6,3,1,1,str(v_crop),14,7)
                    else:
                        v_crop -=1
                        v_crop = max(v_crop,1)
                        v_crop2 = int(v_crop * (cap_height/xheight))
                        text(0,6,3,1,1,str(v_crop),14,7)
                    mask,change = MaskChange()
                    save_config = 1
                    
                elif g == 9 and menu == 2:
                    # INTERVAL
                    if (h == 1 and event.button == 1) or event.button == 4:
                        interval +=1
                        interval = min(interval,180)
                    else:
                        interval -=1
                        interval = max(interval,0)
                    text(0,9,3,1,1,str(interval),14,7)
                    save_config = 1
                    
                elif g == 1 and menu == 2:
                    # VIDEO LENGTH
                    if (h == 0 and event.button == 1) or event.button == 5:
                        if v_length > 1000:
                           v_length -=1000
                        else:
                           v_length -=100
                        v_length = max(v_length,100)
                    else:
                        if v_length > 900:
                            v_length +=1000
                        else:
                           v_length +=100
                        v_length = min(v_length,100000)
                    text(0,1,3,1,1,str(v_length/1000) + "  (" + str(int(fps*(v_length/1000))) +")",14,7)
                    save_config = 1

                elif g == 0 and menu == 2:
                    # VIDEO FORMAT
                    if (h == 0 and event.button == 1) or event.button == 5 and vformat > 0:
                        vformat -=1
                        vformat = max(vformat,0)
                    elif vformat < len(vwidths):
                        vformat += 1
                        vformat = min(vformat,len(vwidths)-1)
                    old_vf = vformat
                    pygame.draw.rect(windowSurfaceObj, (0,0,0), Rect(0 ,0 ,int(scr_width-bw),int(scr_height)), 0)
                    cap_width = vwidths[vformat]
                    cap_height = vheights[vformat]
                    cwidth  = scr_width - bw
                    cheight = scr_height
                    xheight = int(cwidth * (cap_height/cap_width))
                    if xheight > scr_height:
                        xheight = scr_height
                        cwidth = int(xheight * (cap_width/cap_height))   
                    if square == 0:
                        xwidth = cwidth
                    else:
                        xwidth = xheight
                    if a > xwidth - v_crop:
                        a = int(xwidth/2)
                    if b > xheight - h_crop:
                        b = int(xheight/2)
                    if square == 1:
                        apos = 100
                    else:
                        apos = int(cap_width/3)
                    a2 = int(a * (cap_width/cwidth))
                    b2 = int(b * (cap_height/xheight))
                    h_crop2 = int(h_crop * (cap_width/cwidth))
                    v_crop2 = int(v_crop * (cap_height/xheight))
                    text(0,0,3,1,1,str(vwidths[vformat]) + "x" + str(vheights[vformat]),14,7)
                    pygame.display.update()
                    mask,change = MaskChange()
                    save_config = 1
                    restart = 1
                    time.sleep(1)
                    
                elif g == 7 and menu == 0:
                    # COLOUR FILTER
                    if (h == 0 and event.button == 1) or event.button == 5:
                        col_filter -=1
                        col_filter = max(col_filter,0)
                    else:
                        col_filter +=1
                        col_filter = min(col_filter,3)
                    text(0,7,3,1,1,str(col_filters[col_filter]),14,7)
                    save_config = 1
                    if col_filter < 4:
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
                    text(0,9,3,1,1,str(noise_filters[nr]),14,7)
                    save_config = 1

                elif g == 8 and menu == 7 :
                    # CLEAR MASK
                    if event.button == 3:
                        if h == 0:
                            mp = 0
                        else:
                            mp = 1
                        for bb in range(0,int(h_crop * ((2 * cap_width/cwidth) -0.1))):
                            for aa in range(0,int(v_crop * ((2 * cap_height/xheight)-0.1))):
                                mask[bb][aa] = mp
                        nmask = pygame.surfarray.make_surface(mask)
                        nmask = pygame.transform.scale(nmask, (200,200))
                        nmask = pygame.transform.rotate(nmask, 270)
                        nmask = pygame.transform.flip(nmask, True, False)
                        pygame.image.save(nmask,h_user + '/CMask.bmp')
                        mask,change = MaskChange()
                        

                elif g == 1 and menu == 4 :
                    # AUTO TIME
                    if (h == 0 and event.button == 1) or event.button == 5:
                        auto_time -=1
                        auto_time = max(auto_time,0)
                    else:
                        auto_time += 1
                        auto_time = min(auto_time,200)
                    if auto_time > 0:
                        text(0,1,3,1,1,str(auto_time),14,7)
                    else:
                        text(0,1,3,1,1,"OFF",14,7)
                    save_config = 1
                    
                elif g == 2 and menu == 4 :
                    # RAM LIMIT
                    if (h == 0 and event.button == 1) or event.button == 5:
                        ram_limit -=10
                        ram_limit = max(ram_limit,10)
                    else:
                        ram_limit += 10
                        ram_limit = min(ram_limit,int(sfreeram) - 100)
                    text(0,2,3,1,1,str(int(ram_limit)),14,7)
                    save_config = 1

                elif g == 3 and menu == 4 :
                    # SD LIMIT
                    if (h == 0 and event.button == 1) or event.button == 5:
                        SD_limit -=1
                        SD_limit = max(SD_limit,10)
                    else:
                        SD_limit += 1
                        SD_limit = min(SD_limit,99)
                    text(0,3,3,1,1,str(int(SD_limit)),14,7)
                    save_config = 1

                elif g == 4 and menu == 4 :
                    # SD DELETE
                    if (h == 0 and event.button == 1) or event.button == 5:
                        SD_F_Act -=1
                        SD_F_Act = max(SD_F_Act,0)
                    else:
                        SD_F_Act += 1
                        SD_F_Act = min(SD_F_Act,2)
                    if SD_F_Act == 0:
                        text(0,4,3,1,1,"STOP",14,7)
                    elif SD_F_Act == 1:
                        text(0,4,3,1,1,"DEL OLD",14,7)
                    else:
                        text(0,4,3,1,1,"To USB",14,7)
                    save_config = 1
                    
                elif g == 5 and menu == 4 and use_gpio == 1 and fan_ctrl == 1:
                    # FAN TIME
                    if (h == 0 and event.button == 1) or event.button == 5:
                        fan_time -=1
                        fan_time = max(fan_time,2)
                    else:
                        fan_time += 1
                        fan_time = min(fan_time,60)
                    text(0,5,3,1,1,str(fan_time),14,7)
                    save_config = 1
                    
                elif g == 6 and menu == 4 and use_gpio == 1 and fan_ctrl == 1:
                    # FAN LOW
                    if (h == 0 and event.button == 1) or event.button == 5:
                        fan_low -=1
                        fan_low = max(fan_low,30)
                    else:
                        fan_low += 1
                        fan_low = min(fan_low,fan_high - 1)
                    text(0,6,3,1,1,str(fan_low),14,7)
                    save_config = 1

                elif g == 7 and menu == 4 and use_gpio == 1 and fan_ctrl == 1:
                    # FAN HIGH
                    if (h == 0 and event.button == 1) or event.button == 5:
                        fan_high -=1
                        fan_high = max(fan_high,fan_low + 1)
                    else:
                        fan_high +=1
                        fan_high = min(fan_high,80)
                    text(0,7,3,1,1,str(fan_high),14,7)
                    save_config = 1

                elif g == 8 and menu == 0:
                    # DETECTION SPEED
                    if (h == 0 and event.button == 1) or event.button == 5:
                        dspeed -=1
                        dspeed = max(dspeed,1)
                    else:
                        dspeed +=1
                        dspeed = min(dspeed,100)
                    text(0,8,3,1,1,str(dspeed),14,7)
                    save_config = 1

                elif g == 0 and menu == 7 and (Pi_Cam == 3 or Pi_Cam == 5):
                    # v3 camera focus mode
                    if (h == 0 and event.button == 1) or event.button == 5:
                        v3_f_mode -=1
                        v3_f_mode = max(v3_f_mode,0)
                    else:
                        v3_f_mode +=1
                        v3_f_mode = min(v3_f_mode,2)
                    text(0,0,3,1,1,v3_f_modes[v3_f_mode],14,7)
                    if v3_f_mode == 1:
                        text(0,1,2,0,1,"Focus Manual",14,7)
                        if v3_focus == 0 and Pi_Cam == 3:
                            text(0,1,3,1,1,"inf",14,7)
                        elif (Pi_Cam == 5 or Pi_Cam == 6):
                            text(0,1,3,1,1,str(focus),14,7)
                        else:
                            fd = 1/(v3_focus/100)
                            text(0,1,3,1,1,str(fd)[0:5] + "m",14,7)
                    else:
                        text(0,1,3,0,1," ",14,7)
                        text(0,1,3,1,1," ",14,7)
                    fxx = 0
                    fxy = 0
                    fxz = 1
                    if Pi_Cam == 5 or Pi_Cam == 6:
                        fcount = 0
                    restart = 1
                    save_config = 1

                elif g == 1 and menu == 7 and v3_f_mode == 1 and Pi_Cam == 3:
                    # v3 camera focus manual
                    if gv < bh/3:
                        mp = 1 - hp
                        v3_focus = int((mp * 990) + 10)
                    else:
                        if h == 0:
                            v3_focus -= 3
                        else:
                            v3_focus += 3
                    v3_focus = max(v3_focus,10)
                    v3_focus = min(v3_focus,1000)
                    fd = 1/(v3_focus/100)
                    text(0,1,3,1,1,str(fd)[0:5] + "m",14,7)
                    restart = 1

                elif g == 1 and menu == 7 and v3_f_mode == 1 and (Pi_Cam == 5 or Pi_Cam == 6):
                    # Arducam camera focus manual
                    if gv < bh/3:
                        mp = 1 - hp
                        focus = int((mp * 3900) + 100)
                    else:
                        if h == 0:
                            focus -= 10
                        else:
                            focus += 10
                    focus = max(focus,100)
                    focus = min(focus,4000)
                    os.system("v4l2-ctl -d /dev/v4l-subdev" + str(foc_sub5) + " -c focus_absolute=" + str(focus))
                    text(0,1,3,1,1,str(focus),14,7)

                elif g == 0 and menu == 5:
                    # MP4 FPS
                    if (h == 0 and event.button == 1) or event.button == 5:
                        mp4_fps -=1
                        mp4_fps = max(mp4_fps,1)
                    else:
                        mp4_fps +=1
                        mp4_fps = min(mp4_fps,100)
                    text(0,0,3,1,1,str(mp4_fps),14,7)
                    save_config = 1

                elif g == 9 and menu == 5:
                    # MP4 ANNOTATE
                    if (h == 0 and event.button == 1) or event.button == 5:
                        anno -=1
                        anno = max(anno,0)
                    else:
                        anno +=1
                        anno = min(anno,1)
                    if anno == 1:
                        text(0,9,3,1,1,"Yes",14,7)
                    else:
                        text(0,9,3,1,1,"No",14,7)
                    save_config = 1
                    
                elif g == 4 and menu == 7:
                    # SQUARE
                    pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,0,int(xwidth),scr_height))
                    if (h == 0 and event.button == 1) or event.button == 5:
                        square -=1
                        square = max(square,0)
                    else:
                        square +=1
                        square = min(square,1)
                    if square == 1:
                        text(0,4,3,1,1,"Yes",14,7)
                    else:
                        text(0,4,3,1,1,"No",14,7)
                    if square == 0:
                        xwidth = cwidth
                    else:
                        xwidth = xheight
                    if a > xwidth - v_crop:
                        a = int(xwidth/2)
                    if b > xheight - h_crop:
                        b = int(xheight/2)
                    if square == 1:
                        apos = 100
                    else:
                        apos = int(cap_width/3)
                    mask,change = MaskChange()
                    restart = 1
                    save_config = 1

                elif g == 5 and menu == 7:
                    # SQUARE position
                    if (h == 0 and event.button == 1) or event.button == 5:
                        sqpos -= .01
                        sqpos = max(sqpos,0)
                    else:
                        sqpos += .01
                        sqpos = min(sqpos,0.5)
                    text(0,5,3,1,1,str(sqpos)[0:4],14,7)
                    restart = 1
                    save_config = 1

                elif g == 6 and menu == 7:
                    # ALPHA
                    if (h == 0 and event.button == 1) or event.button == 5:
                        alp -= 128
                        alp = max(alp,0)
                    else:
                        alp += 128
                        alp = min(alp,255)
                    text(0,6,3,1,1,str(alp)[0:4],14,7)

                elif g == 7 and menu == 7:
                    # MASK ALPHA
                    if (h == 0 and event.button == 1) or event.button == 5:
                        m_alpha -= 10
                        m_alpha = max(m_alpha,0)
                    else:
                        m_alpha += 10
                        m_alpha = min(m_alpha,250)
                    text(0,7,3,1,1,str(m_alpha)[0:4],14,7)
                    
                elif g == 5 and menu == 5 and event.button != 3 and show == 1 and ((len(USB_Files) > 0 and movtousb == 1) or movtousb == 0):
                  # MAKE A MP4
                  Sideos = glob.glob(h_user + '/Pictures/2*.jpg')
                  Rideos = glob.glob('/run/shm/2*.jpg')
                  for x in range(0,len(Rideos)-1):
                      Sideos.append(Rideos[x])
                  if len(USB_Files) > 0:
                        Uideos = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/2*.jpg")
                        Uideos.sort()
                        for x in range(0,len(Uideos)-1):
                            Sideos.append(Uideos[x])
                  Sideos.sort()
                  if len(Sideos) > 0:
                    if use_gpio == 1 and fan_ctrl == 1:
                        led_fan.value = 1
                    frame = 0
                    text(0,5,3,0,1,"MAKING",14,7)
                    text(0,5,3,1,1,"MP4",14,7)
                    pygame.display.update()
                    z = ""
                    y = ""
                    outvids = []
                    mp4vids = []
                    mp42vids = []
                    for x in range(0,len(Sideos)):
                        Tideos = Sideos[x].split("/")
                        if Tideos[len(Tideos) - 1][:-10] != z:
                            z = Tideos[len(Tideos) - 1][:-10]
                            y = Tideos[len(Tideos) - 2]
                            v = Tideos[1]
                            outvids.append(z)
                            mp4vids.append(y)
                            mp42vids.append(v)
                    year = 2000 + int(outvids[q][0:2])
                    mths = int(outvids[q][2:4])
                    days = int(outvids[q][4:6])
                    hour = int(outvids[q][6:8])
                    mins = int(outvids[q][8:10])
                    secs = int(outvids[q][10:12])
                    if movtousb == 1 and len(USB_Files) > 0:
                        new_dir = m_user + "/'" + USB_Files[0] + "'/Videos"
                    else:
                        new_dir = h_user + "/Videos"
                    if not os.path.exists(new_dir):
                        os.system('mkdir ' + "/" + new_dir)
                    logfile = new_dir + "/" + str(outvids[q]) + ".mp4"
                    txt = "file " + logfile
                    if txt not in txtvids:
                        txtvids.append(txt)
                        with open('mylist.txt', 'w') as f:
                            for item in txtvids:
                                f.write("%s\n" % item)
                    if os.path.exists(logfile):
                        os.remove(logfile)
                    if mp4vids[q] == "Pictures" and mp42vids[q] == "home":
                        cmd = 'ffmpeg -framerate ' + str(mp4_fps) + ' -f image2 -i ' + h_user + '/Pictures/' + str(outvids[q]) + '_%5d.jpg '
                    elif mp4vids[q] == "shm" and mp42vids[q] == "run":
                        cmd = 'ffmpeg -framerate ' + str(mp4_fps) + ' -f image2 -i /run/shm/' + str(outvids[q]) + '_%5d.jpg '
                    elif mp4vids[q] == "Pictures" and mp42vids[q] == "media":
                        cmd = 'ffmpeg -framerate ' + str(mp4_fps) + ' -f image2 -i ' + m_user + "/" + USB_Files[0] +  '/Pictures/' + str(outvids[q]) + '_%5d.jpg '
                    if anno == 1:
                        cmd += '-vf drawtext="fontsize=15:fontfile=/usr/share/fonts/truetype/freefont/FreeSerif.ttf:\ '
                        cmd += "timecode='  " +str(hour) +"\:" + str(mins) + "\:" + str(secs) + "\:00':rate=" + str(mp4_fps) + ":text=" + str(days)+"/"+str(mths)+"/"+str(year)+"--"
                        cmd += ":fontsize=50:fontcolor='white@0.7':\ "
                        cmd += 'boxcolor=black@0.1:box=1:x=100:y=1000" '
                    cmd += str(logfile)
                    os.system(cmd)
                    
                    if os.path.exists(new_dir + "/" + str(outvids[q]) + ".mp4"):
                         if os.path.getsize(new_dir + "/" + str(outvids[q]) + ".mp4") < 1000:
                             os.remove(new_dir + "/" + str(outvids[q]) + ".mp4")
                             fontObj = pygame.font.Font(None, 25)
                             msgSurfaceObj = fontObj.render("Failed to make MP4 !!", False, (255,255,0))
                             msgRectobj = msgSurfaceObj.get_rect()
                             msgRectobj.topleft = (50,200)
                             windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                             pygame.display.update()
                             time.sleep(10)
                    else:
                        fontObj = pygame.font.Font(None, 25)
                        msgSurfaceObj = fontObj.render("Failed to make MP4 !!", False, (255,255,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (50,200)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                        pygame.display.update()
                        time.sleep(10)
                    if len(outvids) > 0:
                        if os.path.exists(h_user + '/Pictures/' + outvids[q] + "_99999.jpg"):
                            image = pygame.image.load(h_user + '/Pictures/' + outvids[q] + "_99999.jpg")
                        elif os.path.exists(h_user + '/Pictures/' + outvids[q] + "_00001.jpg"):
                            image = pygame.image.load(h_user + '/Pictures/' + outvids[q] + "_00001.jpg")
                        elif os.path.exists('/run/shm/' + outvids[q] + "_99999.jpg"):
                            image = pygame.image.load('/run/shm/' + outvids[q] + "_99999.jpg")
                        elif os.path.exists('/run/shm/' + outvids[q] + "_00001.jpg"):
                            image = pygame.image.load('/run/shm/' + outvids[q] + "_00001.jpg")
                        elif os.path.exists(m_user + "/" + USB_Files[0] + '/Pictures/' + outvids[q] + "_99999.jpg"):
                            image = pygame.image.load(m_user + "/" + USB_Files[0] + '/Pictures/' + outvids[q] + "_99999.jpg")
                        elif os.path.exists(m_user + "/" + USB_Files[0] + '/Pictures/' + outvids[q] + "_00001.jpg"):
                            image = pygame.image.load(m_user + "/" + USB_Files[0] + '/Pictures/' + outvids[q] + "_00001.jpg")
                        image = pygame.transform.scale(image, (xwidth,xheight))
                        windowSurfaceObj.blit(image, (0, 0))
                        fontObj = pygame.font.Font(None, 25)
                        msgSurfaceObj = fontObj.render(str(outvids[q] + " " + str(q+1) + "/" + str(ram_frames + frames)), False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (0,10)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    else:
                        msgSurfaceObj = fontObj.render("No Videos Found", False, (255,0,0))
                        msgRectobj = msgSurfaceObj.get_rect()
                        msgRectobj.topleft = (100,cheight/2)
                        windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    if len(txtvids) > 1:
                        text(0,5,9,0,1,"MAKE A",14,7)
                        text(0,5,9,1,1,"MP4",14,7)
                    else:
                        text(0,5,2,0,1,"MAKE A",14,7)
                        text(0,5,2,1,1,"MP4",14,7)
                    USB_Files  = (os.listdir(m_user))
                    Mideos = glob.glob(h_user + '/Videos/*.mp4')
                    if len(USB_Files) > 0:
                        usedusb = os.statvfs(m_user + "/" + USB_Files[0] + "/")
                        USB_storage = ((1 - (usedusb.f_bavail / usedusb.f_blocks)) * 100)
                    if len(USB_Files) > 0 and movtousb == 0 and len(Mideos) > 0:
                        text(0,8,2,0,1,"MOVE MP4s",14,7)
                        text(0,8,2,1,1,"to USB" + str(int(USB_storage))+"%",14,7)
                    else:
                        text(0,8,0,0,1,"MOVE MP4s",14,7)
                        text(0,8,0,1,1,"to USB",14,7)
                    pygame.display.update()
                    if use_gpio == 1 and fan_ctrl == 1:
                        led_fan.value = dc

                elif g == 5 and menu == 5 and event.button == 3 and show == 1 and ((len(USB_Files) > 0 and movtousb == 1) or movtousb == 0):
                  # make MP4 from individual MP4s
                  if os.path.exists('mylist.txt'):
                    text(0,5,3,0,1,"MAKING",14,7)
                    text(0,5,3,1,1,"MP4",14,7)
                    outfile = new_dir + "/" + str(outvids[0]) + "p.mp4"
                    if os.path.exists(outfile):
                        os.remove(outfile)
                    os.system('ffmpeg -f concat -safe 0 -i mylist.txt -c copy ' + outfile)
                    os.remove('mylist.txt')
                    txtvids = []
                    text(0,5,2,0,1,"MAKE A",14,7)
                    text(0,5,2,1,1,"MP4",14,7)
               
                elif (g == 6 or g == 7) and menu == 5 and show == 1 and ((len(USB_Files) > 0 and movtousb == 1) or movtousb == 0):
                 # MAKE ALL or FULL MP4
                 if os.path.exists('mylist.txt'):
                     os.remove('mylist.txt')
                 Sideos = glob.glob(h_user + '/Pictures/2*.jpg')
                 Rideos = glob.glob('/run/shm/2*.jpg')
                 for x in range(0,len(Rideos)-1):
                     Sideos.append(Rideos[x])
                 if len(USB_Files) > 0:
                     Uideos = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/2*.jpg")
                     for x in range(0,len(Uideos)-1):
                         Sideos.append(Uideos[x])
                 Sideos.sort()    
                 if len(Sideos) > 0:
                  if use_gpio == 1 and fan_ctrl == 1:
                      led_fan.value = 1
                  frame = 0
                  if g == 6:
                      text(0,6,3,0,1,"MAKING",14,7)
                      text(0,6,3,1,1,"ALL MP4s",14,7)
                  else:
                      text(0,7,3,0,1,"MAKING",14,7)
                      text(0,7,3,1,1,"FULL MP4",14,7)
                  pygame.display.update()
                  if movtousb == 1 and len(USB_Files) > 0:
                      new_dir = m_user + "/'" + USB_Files[0] + "'/Videos/"
                  else:
                      new_dir = h_user + "/Videos/"
                  outvids = []
                  mp4vids = []
                  mp42vids = []
                  txtvids = []
                  text(0,5,2,0,1,"MAKE A",14,7)
                  text(0,5,2,1,1,"MP4",14,7)
                  z = ""
                  y = ""
                  for x in range(0,len(Sideos)):
                      Tideos = Sideos[x].split("/")
                      if Tideos[len(Tideos) - 1][:-10] != z:
                          z = Tideos[len(Tideos) - 1][:-10]
                          txt = "file '" + new_dir + z + ".mp4'"
                          y = Tideos[len(Tideos) - 2]
                          v = Tideos[1]
                          outvids.append(z)
                          mp4vids.append(y)
                          mp42vids.append(v)
                          txtvids.append(txt)
                  with open('mylist.txt', 'w') as f:
                      for item in txtvids:
                          f.write("%s\n" % item)
                  for w in range(0,len(outvids)):
                    if os.path.exists(h_user + '/Pictures/' + outvids[w] + "_99999.jpg"):
                        image = pygame.image.load( h_user + '/Pictures/' + outvids[w] + "_99999.jpg")
                    elif os.path.exists(h_user + '/Pictures/' + outvids[w] + "_00001.jpg"):
                        image = pygame.image.load(h_user + '/Pictures/' + outvids[w] + "_00001.jpg")
                    elif os.path.exists('/run/shm/' + outvids[w] + "_99999.jpg"):
                        image = pygame.image.load('/run/shm/' + outvids[w] + "_99999.jpg")
                    elif os.path.exists('/run/shm/' + outvids[w] + "_00001.jpg"):
                        image = pygame.image.load('/run/shm/' + outvids[w] + "_00001.jpg")
                    elif os.path.exists(m_user + "/" + USB_Files[0] + '/Pictures/' + outvids[w] + "_99999.jpg"):
                        image = pygame.image.load(m_user + "/" + USB_Files[0] + '/Pictures/' + outvids[w] + "_99999.jpg")
                    elif os.path.exists(m_user + "/" + USB_Files[0] + '/Pictures/' + outvids[w] + "_00001.jpg"):
                        image = pygame.image.load(m_user + "/" + USB_Files[0] + '/Pictures/' + outvids[w] + "_00001.jpg")
                    imageo = pygame.transform.scale(image, (xwidth,xheight))
                    windowSurfaceObj.blit(imageo, (0, 0))
                    fontObj = pygame.font.Font(None, 25)
                    msgSurfaceObj = fontObj.render(str(outvids[w] + " " + str(w+1) + "/" + str(len(outvids))), False, (255,0,0))
                    msgRectobj = msgSurfaceObj.get_rect()
                    msgRectobj.topleft = (0,10)
                    windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                    text(0,1,3,1,1,str(w+1) + " / " + str(ram_frames + frames),14,7)
                    pygame.display.update()
                    year = 2000 + int(outvids[w][0:2])
                    mths = int(outvids[w][2:4])
                    days = int(outvids[w][4:6])
                    hour = int(outvids[w][6:8])
                    mins = int(outvids[w][8:10])
                    secs = int(outvids[w][10:12])
                    if movtousb == 1 and len(USB_Files) > 0:
                        new_dir = m_user + "/'" + USB_Files[0] + "'/Videos"
                    else:
                        new_dir = h_user + "/Videos"
                    if not os.path.exists(new_dir):
                        os.system('mkdir ' + "/" + new_dir)
                    logfile = new_dir + "/" + str(outvids[w]) + ".mp4"
                    if os.path.exists(logfile):
                        os.remove(logfile)
                    if mp4vids[w] == "Pictures" and mp42vids[w] == "home":
                        cmd = 'ffmpeg -framerate ' + str(mp4_fps) + ' -f image2 -i ' + h_user + '/Pictures/' + str(outvids[w]) + '_%5d.jpg '
                    elif mp4vids[w] == "shm" and mp42vids[w] == "run":
                        cmd = 'ffmpeg -framerate ' + str(mp4_fps) + ' -f image2 -i /run/shm/' + str(outvids[w]) + '_%5d.jpg '
                    elif mp4vids[w] == "Pictures" and mp42vids[w] == "media":
                        cmd = 'ffmpeg -framerate ' + str(mp4_fps) + ' -f image2 -i ' + m_user + "/" + USB_Files[0] +  '/Pictures/' + str(outvids[w]) + '_%5d.jpg '

                    if anno == 1:
                        cmd += '-vf drawtext="fontsize=15:fontfile=/Library/Fonts/DroidSansMono.ttf:\ '
                        cmd += "timecode='  " + str(hour) +"\:" + str(mins) + "\:" + str(secs) + "\:00':rate=" + str(mp4_fps) + ":text=" + str(days)+"/"+str(mths)+"/"+str(year)+"--"
                        cmd += ":fontsize=50:fontcolor='white@0.7':\ "
                        cmd += 'boxcolor=black@0.3:box=1:x=0:y=1030" '
                    cmd += str(logfile)
                    os.system(cmd)
                    if os.path.exists(new_dir + "/" + str(outvids[w]) + ".mp4"):
                         if os.path.getsize(new_dir + "/" + str(outvids[w]) + ".mp4") < 1000:
                             os.remove(new_dir + "/" + str(outvids[w]) + ".mp4")
                             fontObj = pygame.font.Font(None, 25)
                             msgSurfaceObj = fontObj.render("Failed to make MP4 !!", False, (255,255,0))
                             msgRectobj = msgSurfaceObj.get_rect()
                             msgRectobj.topleft = (50,200)
                             windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                             pygame.display.update()
                             time.sleep(5)
                  if g == 7:
                      # make FULL MP4 from ALL MP4s
                      outfile = new_dir + "/" + str(outvids[0]) + "f.mp4"
                      if os.path.exists(outfile):
                          os.remove(outfile)
                      os.system('ffmpeg -f concat -safe 0 -i mylist.txt -c copy ' + outfile)
                      # delete individual MP4s leaving the FULL MP4 only.
                      # read mylist.txt file
                      txtconfig = []
                      with open('mylist.txt', "r") as file:
                          line = file.readline()
                          line2 = line.split(" ")
                          while line:
                              txtconfig.append(line2[1][1:-2].strip())
                              line = file.readline()
                              line2 = line.split(" ")
                      for x in range(0,len(txtconfig)):
                          if os.path.exists(txtconfig[x]):
                              os.remove(txtconfig[x])
                      os.remove('mylist.txt')
                      txtvids = []
                      #move MP4 to usb
                      USB_Files  = []
                      USB_Files  = (os.listdir(m_user))
                      if len(USB_Files) > 0:
                        if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Videos/") :
                            os.system('mkdir ' + m_user + "/'" + USB_Files[0] + "'/Videos/")
                        if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Pictures/") :
                            os.system('mkdir ' + m_user + "/'" + USB_Files[0] + "'/Pictures/")
                        text(0,8,3,0,1,"MOVING",14,7)
                        text(0,8,3,1,1,"MP4s",14,7)
                        spics = glob.glob(h_user + '/Videos/*.mp4')
                        spics.sort()
                        for xx in range(0,len(spics)):
                            movi = spics[xx].split("/")
                            if os.path.exists(m_user + "/" + USB_Files[0] + "/Videos/" + movi[4]):
                                os.remove(m_user + "/" + USB_Files[0] + "/Videos/" + movi[4])
                            shutil.copy(spics[xx],m_user + "/" + USB_Files[0] + "/Videos/")
                            if os.path.exists(m_user + "/" + USB_Files[0] + "/Videos/" + movi[4]):
                                os.remove(spics[xx])
                        spics = glob.glob(h_user + '/Videos/*.mp4')
                        text(0,8,0,0,1,"MOVE MP4s",14,7)
                        text(0,8,0,1,1,"to USB",14,7)
                       
                  Videos = glob.glob(h_user + '/Pictures/*.jpg')
                  USB_Files  = (os.listdir(m_user))
                  if len(USB_Files) > 0:
                      upics = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/*.jpg")
                      upics.sort()
                      for x in range(0,len(upics)):
                          Videos.append(upics[x])
                  Videos.sort()
                  outvids = []
                  z = ""
                  for x in range(0,len(Videos)):
                      Tideos = Videos[x].split("/")
                      if Tideos[len(Tideos) - 1][:-10] != z:
                          z = Tideos[len(Tideos) - 1][:-10]
                          outvids.append(z)
                  w = 0
                  text(0,6,2,0,1,"MAKE ALL",14,7)
                  text(0,6,2,1,1,"MP4",14,7)
                  text(0,7,2,0,1,"MAKE FULL",14,7)
                  text(0,7,2,1,1,"MP4",14,7)
                  text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),14,7)
                  USB_Files  = (os.listdir(m_user))
                  Mideos = glob.glob(h_user + '/Videos/*.mp4')
                  if len(USB_Files) > 0:
                      usedusb = os.statvfs(m_user + "/" + USB_Files[0] + "/")
                      USB_storage = ((1 - (usedusb.f_bavail / usedusb.f_blocks)) * 100)
                  if len(USB_Files) > 0 and movtousb == 0 and len(Mideos) > 0:
                      text(0,8,2,0,1,"MOVE MP4s",14,7)
                      text(0,8,2,1,1,"to USB " + str(int(USB_storage))+"%",14,7)
                  else:
                      text(0,8,0,0,1,"MOVE MP4s",14,7)
                      text(0,8,0,1,1,"to USB",14,7)
                  pygame.display.update()
                  Capture = old_cap
                  main_menu()
                  if square == 1:
                      pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(xheight,0,int(xheight/2.3),scr_height))
                  pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,scr_width-bw,scr_height))
                  show = 0
                  restart = 1
                  USB_Files  = (os.listdir(m_user))
                  Mideos = glob.glob(h_user + '/Videos/*.mp4')
                  if use_gpio == 1 and fan_ctrl == 1:
                      led_fan.value = dc

                elif menu == 5 and g == 8:
                    #move MP4 & CAM1_jpgs to usb
                    if os.path.exists('mylist.txt'):
                        os.remove('mylist.txt')
                    txtvids = []
                    USB_Files  = []
                    USB_Files  = (os.listdir(m_user))
                    if len(USB_Files) > 0:
                        if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Videos/") :
                            os.system('mkdir ' + m_user + "/'" + USB_Files[0] + "'/Videos/")
                        if not os.path.exists(m_user + "/'" + USB_Files[0] + "'/Pictures/") :
                            os.system('mkdir ' + m_user + "/'" + USB_Files[0] + "'/Pictures/")
                        text(0,8,3,0,1,"MOVING",14,7)
                        text(0,8,3,1,1,"MP4s",14,7)
                        spics = glob.glob( h_user + '/Videos/*.mp4')
                        spics.sort()
                        for xx in range(0,len(spics)):
                            movi = spics[xx].split("/")
                            if os.path.exists(m_user + "/" + USB_Files[0] + "/Videos/" + movi[4]):
                                os.remove(m_user + "/" + USB_Files[0] + "/Videos/" + movi[4])
                            shutil.copy(spics[xx],m_user + "/" + USB_Files[0] + "/Videos/")
                            if os.path.exists(m_user + "/" + USB_Files[0] + "/Videos/" + movi[4]):
                                os.remove(spics[xx])
                        spics = glob.glob(h_user + '/Videos/*.mp4')
                        text(0,8,0,0,1,"MOVE MP4s",14,7)
                        text(0,8,0,1,1,"to USB",14,7)
                    # Move CAM1 jpgs to USB if present
                    USB_Files  = []
                    USB_Files  = (os.listdir(m_user))
                    if len(USB_Files) > 0:
                        photos = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
                        photos.sort()
                        for xx in range(0,len(spics)):
                            shutil.move(photos[xx],m_user + "/" + USB_Files[0] + "/Pictures/")
                    photos = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
                    photos.sort()
                  
                elif (menu == -1 and g > 1) or (menu != -1 and g == 10) or (menu == 3 and g == 9):
                    # MENUS
                    # check for usb_stick
                    USB_Files  = []
                    USB_Files  = (os.listdir(m_user + "/"))
                    if show == 1 and menu != 3:
                        show = 0
                        restart = 1
                    pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,scr_width-bw,scr_height))
                    
                    if g == 2 and event.button != 3:
                        menu = 0
                        old_capture = Capture
                        Capture = 0
                        for d in range(0,10):
                            button(0,d,0)
                        text(0,3,2,0,1,"Low Threshold",14,7)
                        text(0,3,3,1,1,str(threshold),14,7)
                        text(0,2,2,0,1,"High Detect %",14,7)
                        text(0,2,3,1,1,str(det_high),14,7)
                        text(0,1,2,0,1,"Low Detect %",14,7)
                        text(0,1,3,1,1,str(detection),14,7)
                        if preview == 1:
                            button(0,0,1)
                            text(0,0,1,0,1,"Preview",14,0)
                            text(0,0,1,1,1,"Threshold",13,0)
                        else:
                            button(0,0,0)
                            text(0,0,2,0,1,"Preview",14,7)
                            text(0,0,2,1,1,"Threshold",13,7)
                        text(0,4,2,0,1,"High Threshold",14,7)
                        text(0,4,3,1,1,str(threshold2),14,7)
                        text(0,5,2,0,1,"Horiz'l Crop",14,7)
                        text(0,5,3,1,1,str(h_crop),14,7)
                        text(0,6,2,0,1,"Vert'l Crop",14,7)
                        text(0,6,3,1,1,str(v_crop),14,7)
                        text(0,7,2,0,1,"Colour Filter",14,7)
                        text(0,7,3,1,1,str(col_filters[col_filter]),14,7)
                        text(0,8,2,0,1,"Det Speed",14,7)
                        text(0,8,3,1,1,str(dspeed),14,7)
                        text(0,9,2,0,1,"Noise Red'n",14,7)
                        text(0,9,3,1,1,str(noise_filters[nr]),14,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)

                    if g == 2 and event.button == 3:
                        # PREVIEW
                        preview +=1
                        if preview > 1:
                            preview = 0
                            text(0,2,1,1,1,"Settings",14,7)
                            
                    if g == 3:
                        menu = 1
                        old_capture = Capture
                        Capture = 0
                        for d in range(0,10):
                            button(0,d,0)
                        text(0,0,5,0,1,"Quality",14,7)
                        text(0,0,3,1,1,str(quality),14,7)
                        text(0,7,5,0,1,"Meter",14,7)
                        text(0,7,3,1,1,meters[meter],14,7)
                        text(0,1,5,0,1,"Mode",14,7)
                        text(0,1,3,1,1,modes[mode],14,7)
                        text(0,2,5,0,1,"Shutter mS",14,7)
                        if mode == 0:
                            text(0,2,3,1,1,str(int(speed/1000)),14,7)
                        else:
                            text(0,2,0,1,1,str(int(speed/1000)),14,7)
                        text(0,3,5,0,1,"gain",14,7)
                        if gain > 0:
                            text(0,3,3,1,1,str(gain),14,7)
                        else:
                            text(0,3,3,1,1,"Auto",14,7)
                        text(0,4,5,0,1,"Brightness",14,7)
                        text(0,4,3,1,1,str(brightness),14,7)
                        text(0,5,5,0,1,"Contrast",14,7)
                        text(0,5,3,1,1,str(contrast),14,7)
                        text(0,6,5,0,1,"eV",14,7)
                        text(0,6,3,1,1,str(ev),14,7)
                        text(0,7,5,0,1,"Metering",14,7)
                        text(0,7,3,1,1,str(meters[meter]),14,7)
                        text(0,8,5,0,1,"Saturation",14,7)
                        text(0,8,3,1,1,str(saturation),14,7)
                        if zoom == 0:
                            button(0,9,0)
                            text(0,9,2,0,1,"Zoom",14,7)
                        else:
                            button(0,9,1)
                            text(0,9,1,0,1,"Zoom",14,0)
                        if scientif == 1:
                            text(0,9,5,0,1,"Scientific",14,7)
                            text(0,9,3,1,1,str(scientific),14,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)

                    if g == 9 and menu == -1 and Pi == 5 and cam2  != "2":
                        menu = 8
                        camera = 1
                        for d in range(0,10):
                            button(0,d,0)
                        text(0,0,2,0,1,"Photo Rate",14,7)
                        text(0,0,3,1,1,str(photo_timer),14,7)
                        text(0,9,2,0,1,"MAIN Camera",14,7)
                        text(0,9,3,1,1,str(camera),14,7)
                        text(0,1,5,0,1,"Mode",14,7)
                        text(0,1,3,1,1,modes[mode2],14,7)
                        text(0,2,5,0,1,"Shutter mS",14,7)
                        if mode2 == 0:
                            text(0,2,3,1,1,str(int(speed2/1000)),14,7)
                            framerate2 = int((1/speed2)*1000000)
                            framerate2 = min(framerate2,60)
                            framerate2 = max(framerate2,1)
                            text(0,8,3,1,1,str(framerate2),14,7)
                        else:
                            text(0,2,0,1,1,str(int(speed2/1000)),14,7)
                        text(0,3,5,0,1,"gain",14,7)
                        if gain2 > 0:
                            text(0,3,3,1,1,str(gain2),14,7)
                        else:
                            text(0,3,3,1,1,"Auto",14,7)
                        text(0,4,5,0,1,"Brightness",14,7)
                        text(0,4,3,1,1,str(brightness2),14,7)
                        text(0,5,5,0,1,"Contrast",14,7)
                        text(0,5,3,1,1,str(contrast2),14,7)
                        text(0,6,5,0,1,"eV",14,7)
                        text(0,6,3,1,1,str(ev2),14,7)
                        text(0,7,5,0,1,"Metering",14,7)
                        text(0,7,3,1,1,str(meters[meter2]),14,7)
                        text(0,8,5,0,1,"Framerate",14,7)
                        text(0,8,3,1,1,str(framerate2),14,7)
                        if zoom == 0:
                            button(0,9,0)
                            text(0,9,2,0,1,"Zoom",14,7)
                        else:
                            button(0,9,1)
                            text(0,9,1,0,1,"Zoom",14,0)
                        text(0,10,1,0,1,"MAIN MENU",14,7)
                        poll = p.poll()
                        if poll == None:
                            os.killpg(p.pid, signal.SIGTERM)
                        while poll == None:
                            poll = p.poll()
                        # clear ram
                        zpics = glob.glob('/run/shm/test*.jpg')
                        for tt in range(0,len(zpics)):
                            os.remove(zpics[tt])
                        os.system('pkill -SIGUSR2 rpicam-still')
                        restart = 1
                        time.sleep(1)
                       

                    if g == 4:
                        menu = 2
                        for d in range(0,10):
                            button(0,d,0)
                        text(0,0,2,0,1,"V Format",14,7)
                        text(0,0,3,1,1,str(vwidths[vformat]) + "x" + str(vheights[vformat]),14,7)
                        text(0,4,5,0,1,"AWB",14,7)
                        text(0,4,3,1,1,str(awbs[awb]),14,7)
                        text(0,2,5,0,1,"fps",14,7)
                        text(0,2,3,1,1,str(fps),14,7)
                        text(0,5,5,0,1,"Red",14,7)
                        text(0,6,5,0,1,"Blue",14,7)
                        if awb == 0:
                            text(0,5,3,1,1,str(red)[0:3],14,7)
                            text(0,6,3,1,1,str(blue)[0:3],14,7)
                        else:
                            text(0,5,0,1,1,str(red)[0:3],14,7)
                            text(0,6,0,1,1,str(blue)[0:3],14,7)
                        text(0,7,5,0,1,"Sharpness",14,7)
                        text(0,7,3,1,1,str(sharpness),14,7)
                        text(0,3,2,0,1,"V Pre-Frames",14,7)
                        text(0,3,3,1,1,str(pre_frames),14,7)
                        text(0,8,5,0,1,"Denoise",14,7)
                        text(0,8,3,1,1,str(denoises[denoise]),14,7)
                        text(0,9,2,0,1,"Interval S",14,7)
                        text(0,9,3,1,1,str(interval),14,7)
                        text(0,1,2,0,1,"V Length S (F)",14,7)
                        text(0,1,3,1,1,str(v_length/1000) + "  (" + str(int(fps*(v_length/1000))) +")",14,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)
                        
                    if g == 6 and (ram_frames > 0 or frames > 0 or len(photos) > 0):
                        menu = 3
                        en_photo = 0
                        poll = p.poll()
                        if poll == None:
                            os.killpg(p.pid, signal.SIGTERM)
                        for d in range(0,10):
                            button(0,d,0)
                        show = 1
                        frame = 0
                        trig = 1
                        old_cap = Capture
                        zzpics = []
                        rpics = []
                        zzpics = glob.glob(h_user + '/Pictures/*99999.jpg')
                        rpics = glob.glob('/run/shm/*99999.jpg')
                        frames = 0
                        ram_frames = 0
                        rpics.sort()
                        for x in range(0,len(rpics)):
                            zzpics.append(rpics[x])
                        USB_Files  = (os.listdir(m_user))
                        if len(USB_Files) > 0:
                            upics = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/*99999.jpg")
                            upics.sort()
                            for x in range(0,len(upics)):
                                zzpics.append(upics[x])
                        zzpics.sort()
                        z = ""
                        y = ""
                        for x in range(0,len(zzpics)):
                            Tideos = zzpics[x].split("/")
                            if len(Tideos) >= 5:
                                if Tideos[len(Tideos) - 1][:-10] != z:
                                    z = Tideos[len(Tideos) - 1][:-10]
                                    outvids.append(z)
                                    frames +=1
                            else:
                                if Tideos[len(Tideos) - 1][:-10] != y:
                                    y = Tideos[len(Tideos) - 1][:-10]
                                    outvids.append(y)
                                    ram_frames +=1
                        q = 0
                        if len(zzpics) > 0:
                            tlen = int(fps*(v_length/1000)) + pre_frames
                            play = glob.glob(zzpics[q][:-10] + "*.jpg")
                            play.sort()
                            image = pygame.image.load(zzpics[q])
                            cropped = pygame.transform.scale(image, (xwidth,xheight))
                            windowSurfaceObj.blit(cropped, (0, 0))
                            fontObj = pygame.font.Font(None, 25)
                            msgSurfaceObj = fontObj.render(str(zzpics[q]), False, (255,255,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,10)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            if len(play) >= tlen:
                                msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,0,0))
                            else:
                                msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1)), False, (255,128,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,35)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,xheight,scr_width-bw,scr_height))
                            pygame.display.update()
                            text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),14,7)
                        photos = glob.glob(h_user + '/Pictures/CAM1_*.jpg')
                        photos.sort()
                        if Pi == 5 and cam2 != "2":
                            text(0,0,2,0,1,"Photo",14,7)
                            text(0,0,3,1,1,str(len(photos)),14,7)
                        text(0,1,2,0,1,"Video",14,7)
                        text(0,2,2,0,1,"PLAY",14,7)
                        text(0,2,2,1,1,"<<   <    >   >>",14,7)
                        text(0,3,2,0,1,"Frame",14,7)
                        text(0,4,0,0,1,"DELETE ",14,7)
                        text(0,4,0,1,1,"FRAME ",14,7)
                        text(0,5,0,0,1,"DELETE",14,7)
                        text(0,5,0,1,1,"START - END",14,7)
                        text(0,6,3,0,1,"DELETE ",14,7)
                        text(0,6,3,1,1,"VIDEO ",14,7)
                        text(0,7,3,0,1,"DELETE",14,7)
                        text(0,7,3,1,1,"ALL VIDS  ",14,7)
                        text(0,8,2,0,1,"SHOW ALL",14,7)
                        text(0,8,2,1,1,"Videos",14,7)
                        if ram_frames > 0 or frames > 0:
                            text(0,9,1,0,1,"MAKE",14,7)
                            text(0,9,1,1,1,"MP4",14,7)
                        else:
                            text(0,9,0,0,1,"MAKE",14,7)
                            text(0,9,0,1,1,"MP4",14,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)
                        
                    if g == 5:
                        menu = 7
                        old_capture = Capture
                        Capture = 0
                        for d in range(0,10):
                            button(0,d,0)
                        if zoom == 0:
                            button(0,3,0)
                            text(0,3,2,0,1,"Zoom",14,7)
                        else:
                            button(0,3,1)
                            text(0,3,1,0,1,"Zoom",14,0)
                        text(0,4,2,0,1,"Square Format",14,7)
                        if square == 1:
                            text(0,4,3,1,1,"Yes",14,7)
                        else:
                            text(0,4,3,1,1,"No",14,7)
                        text(0,5,2,0,1,"Sq Pos",14,7)
                        text(0,5,3,1,1,str(sqpos)[0:4],14,7)
                        text(0,6,2,0,1,"Alpha",14,7)
                        text(0,6,3,1,1,str(alp),14,7)
                        text(0,7,2,0,1,"MASK Alpha",14,7)
                        text(0,7,3,1,1,str(m_alpha),14,7)
                        text(0,8,3,0,1,"CLEAR Mask",14,7)
                        text(0,8,3,1,1," 0       1  ",14,7)
                        text(0,9,1,0,1,"Shutdown Hour",14,7)
                        if synced == 1:
                            text(0,9,3,1,1,str(sd_hour) + ":00",14,7)
                        else:
                            text(0,9,0,1,1,str(sd_hour) + ":00",14,7)
                        if scientif == 1 and Pi_Cam == 4:
                            text(0,9,5,0,1,"Scientific",14,7)
                            text(0,9,3,1,1,str(scientific),14,7)
                        if Pi_Cam == 3 or Pi_Cam == 5:
                            text(0,0,2,0,1,"Focus",14,7)
                            if v3_f_mode == 1:
                                text(0,1,2,0,1,"Focus Manual",14,7)
                                if v3_focus == 0 and Pi_Cam == 3:
                                    text(0,1,3,1,1,"inf",14,7)
                                elif (Pi_Cam == 5 or Pi_Cam == 6):
                                    text(0,1,3,1,1,str(focus),14,7)
                                else:
                                    fd = 1/(v3_focus/100)
                                    text(0,1,3,1,1,str(fd)[0:5] + "m",14,7)
                            text(0,0,3,1,1,v3_f_modes[v3_f_mode],14,7)
                            if fxz != 1:
                                text(0,0,3,1,1,"Spot",14,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)
                        
                    if g == 7:
                        menu = 4
                        old_capture = Capture
                        Capture = 0
                        for d in range(0,10):
                            button(0,d,0)
                        text(0,1,2,0,1,"Auto Time",14,7)
                        if Pi == 5:
                            text(0,0,2,0,1,"CPU Temp/FAN",13,7)
                            if os.path.exists ('fantxt.txt'): 
                                os.remove("fantxt.txt")
                            os.system("cat /sys/devices/platform/cooling_fan/hwmon/*/fan1_input >> fantxt.txt")
                            time.sleep(0.25)
                            with open("fantxt.txt", "r") as file:
                                line = file.readline()
                                if line == "":
                                    line = 0
                            text(0,0,3,1,1,str(int(temp)) + " / " + str(int(line)),14,7)
                        else:
                            text(0,0,2,0,1,"CPU Temp",14,7)
                            text(0,0,3,1,1,str(int(temp)),14,7)
                        if auto_time > 0:
                            text(0,1,3,1,1,str(auto_time),14,7)
                        else:
                            text(0,1,3,1,1,"OFF",14,7)
                        text(0,2,2,0,1,"RAM Limit MB",14,7)
                        text(0,2,3,1,1,str(int(ram_limit)),14,7)
                        text(0,3,2,0,1,"SD Limit %",14,7)
                        text(0,3,3,1,1,str(int(SD_limit)),14,7)
                        text(0,4,2,0,1,"SD Full Action",14,7)
                        if SD_F_Act == 0:
                            text(0,4,3,1,1,"STOP",14,7)
                        elif SD_F_Act == 1:
                            text(0,4,3,1,1,"DEL OLD",14,7)
                        else:
                            text(0,4,3,1,1,"To USB",14,7)
                        if use_gpio == 1:
                            if fan_ctrl == 1:
                                text(0,5,2,0,1,"Fan Time S",14,7)
                                text(0,5,3,1,1,str(fan_time),14,7)
                                text(0,6,2,0,1,"Fan Low degC",14,7)
                                text(0,6,3,1,1,str(fan_low),14,7)
                                text(0,7,2,0,1,"Fan High degC",14,7)
                                text(0,7,3,1,1,str(fan_high),14,7)
                            text(0,8,2,0,1,"Ext. Trigger",14,7)
                            if ES == 0:
                                text(0,8,3,1,1,"OFF",14,7)
                            elif ES == 1:
                                text(0,8,3,1,1,"Short",14,7)
                            else:
                                text(0,8,3,1,1,"Long",14,7)
                        USB_Files  = []
                        USB_Files  = (os.listdir(m_user))
                        if len(USB_Files) > 0:
                            usedusb = os.statvfs(m_user + "/" + USB_Files[0] + "/Pictures/")
                            USB_storage = ((1 - (usedusb.f_bavail / usedusb.f_blocks)) * 100)
                        if frames + ram_frames > 0 and len(USB_Files) > 0:
                            text(0,9,3,0,1,"Move JPGs",14,7)
                            text(0,9,3,1,1,"to USB " + str(int(USB_storage)) + "%",14,7)
                        else:
                            text(0,9,0,0,1,"Move JPGs",14,7)
                            text(0,9,0,1,1,"to USB",14,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)
                        
                    if ((g == 8 and menu == -1) or (g == 9 and menu == 3)) and ram_frames + frames > 0:
                        menu = 5
                        for d in range(0,10):
                            button(0,d,0)
                        show = 1
                        frame = 0
                        poll = p.poll()
                        if poll == None:
                            os.killpg(p.pid, signal.SIGTERM)
                        old_cap = Capture
                        text(0,1,2,0,1,"Video",14,7)
                        zzpics = []
                        rpics = []
                        zzpics = glob.glob(h_user + '/Pictures/*99999.jpg')
                        rpics = glob.glob('/run/shm/*99999.jpg')
                        frames = 0
                        ram_frames = 0
                        rpics.sort()
                        for x in range(0,len(rpics)):
                             zzpics.append(rpics[x])
                        USB_Files  = (os.listdir(m_user))
                        if len(USB_Files) > 0:
                            upics = glob.glob(m_user + "/'" + USB_Files[0] + "'/Pictures/*99999.jpg")
                            upics.sort()
                            for x in range(0,len(upics)):
                                zzpics.append(upics[x])
                        zzpics.sort()
                        z = ""
                        y = ""
                        for x in range(0,len(zzpics)):
                            Tideos = zzpics[x].split("/")
                            if len(Tideos) >= 5:
                                if Tideos[len(Tideos) - 1][:-10] != z:
                                    z = Tideos[len(Tideos) - 1][:-10]
                                    outvids.append(z)
                                    frames +=1
                            else:
                                if Tideos[len(Tideos) - 1][:-10] != y:
                                    y = Tideos[len(Tideos) - 1][:-10]
                                    outvids.append(y)
                                    ram_frames +=1
                        if len(zzpics) > 0:
                            play = glob.glob(zzpics[q][:-10] + "2*.jpg")
                            play.sort()
                            image = pygame.image.load(zzpics[q])
                            cropped = pygame.transform.scale(image, (xwidth,xheight))
                            windowSurfaceObj.blit(cropped, (0, 0))
                            if square == 1:
                                pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(xheight,0,int(xheight/2.4),scr_height))
                            fontObj = pygame.font.Font(None, 25)
                            msgSurfaceObj = fontObj.render(str(zzpics[q]), False, (255,255,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,10)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            msgSurfaceObj = fontObj.render((str(q+1) + "/" + str(ram_frames + frames) + " - " + str(len(play)-1) ), False, (255,0,0))
                            msgRectobj = msgSurfaceObj.get_rect()
                            msgRectobj.topleft = (10,35)
                            windowSurfaceObj.blit(msgSurfaceObj, msgRectobj)
                            pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,cheight,scr_width-bw,scr_height))
                            pygame.display.update()
                        text(0,1,3,1,1,str(q+1) + " / " + str(ram_frames + frames),14,7)
                        text(0,0,2,0,1,"MP4 FPS",14,7)
                        text(0,0,3,1,1,str(mp4_fps),14,7)
                        text(0,2,2,0,1,"PLAY",14,7)
                        text(0,2,2,1,1,"<<   <    >   >>",14,7)
                        text(0,3,2,0,1,"Frame",14,7)
                        text(0,5,2,0,1,"MAKE A",14,7)
                        text(0,5,2,1,1,"MP4",14,7)
                        text(0,6,2,0,1,"MAKE ALL",14,7)
                        text(0,6,2,1,1,"MP4s",14,7)
                        text(0,7,2,0,1,"MAKE FULL",14,7)
                        text(0,7,2,1,1,"MP4",14,7)
                        USB_Files  = []
                        USB_Files  = (os.listdir(m_user))
                        Mideos = glob.glob(h_user + '/Videos/*.mp4')
                        if len(USB_Files) > 0:
                            usedusb = os.statvfs(m_user + "/" + USB_Files[0] + "/")
                            USB_storage = ((1 - (usedusb.f_bavail / usedusb.f_blocks)) * 100)
                        if len(USB_Files) > 0 and movtousb == 0 and len(Mideos) > 0:
                             text(0,8,2,0,1,"MOVE MP4s",14,7)
                             text(0,8,2,1,1,"to USB " + str(int(USB_storage)) + "%",14,7)
                        else:
                             text(0,8,0,0,1,"MOVE MP4s",14,7)
                             text(0,8,0,1,1,"to USB",14,7)
                        text(0,9,2,0,1,"MP4 Annotate",14,7)
                        if anno == 1:
                            text(0,9,3,1,1,"Yes",14,7)
                        else:
                            text(0,9,3,1,1,"No",14,7)
                        text(0,4,0,0,1,"DELETE",14,7)
                        text(0,4,0,1,1,"START - END",14,7)
                        text(0,10,1,0,1,"MAIN MENU",14,7)

                    if g == 10 and menu != -1:
                        sframe = -1
                        eframe = -1
                        trig = 1
                        poll = p.poll()
                        if poll != None:
                            restart = 1
                        if os.path.exists('mylist.txt'):
                            os.remove('mylist.txt')
                        txtvids = []
                        if menu == 8 and cam2 != "2":
                            restart2 = 1
                            camera = 0
                            restart = 1
                            pygame.draw.rect(windowSurfaceObj,(0,0,0),Rect(0,0,scr_width-bw,scr_height))
                            pygame.display.update(0,0,scr_width-bw,scr_height)
                            time.sleep(1)
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
                config[8]  = SD_limit
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
                config[27] = det_high
                config[28] = quality
                config[29] = fan_time
                config[30] = sd_hour
                config[31] = vformat
                config[32] = threshold2
                config[33] = col_filter
                config[34] = nr
                config[35] = pre_frames
                config[36] = auto_time
                config[37] = ram_limit
                config[38] = v3_f_mode
                config[39] = v3_focus
                config[40] = square
                config[41] = int(sqpos*100)
                config[42] = mp4_fps
                config[43] = anno
                config[44] = SD_F_Act
                config[45] = dspeed
                config[46] = int(photo_timer*10)
                config[47] = camera
                config[48] = mode2
                config[49] = speed2
                config[50] = gain2
                config[51] = brightness2
                config[52] = contrast2
                config[53] = ev2
                config[54] = meter2
                config[55] = sharpness2
                config[56] = saturation2
                config[57] = framerate2
              
                with open(config_file, 'w') as f:
                    for item in config:
                        f.write("%s\n" % item)
                        
       
    if restart2 == 1 and time.monotonic() - timer2 > 1:
        if trace == 1:
            print ("Step 15 RESTART2")
        timer2 = time.monotonic()
        restart2 = 0
        os.system('pkill -SIGUSR2 rpicam-still')
        if same_cams == 0:
            Camera_Version()
        pygame.display.set_caption('Action ' + cameras[Pi_Cam])
        now = datetime.datetime.now()
        timestamp = now.strftime("%y%m%d%H%M%S")
        fname =  pic_dir + 'CAM1_'  + str(timestamp) + '_%04d.jpg'
        rpistr2 = 'rpicam-still --camera 1 -s -n -t 0 -e jpg -o ' + fname + ' --contrast ' + str(contrast2/100) + " --brightness " + str(brightness2/100)
        if mode2 == 0:
            rpistr2 +=" --shutter " + str(speed2)
        else:
            rpistr2 +=" --exposure " + str(modes[mode2])
        rpistr2 += " --ev " + str(ev2) +  " --gain " + str(gain2)
        rpistr2 += " --metering "   + meters[meter2]
        rpistr2 += " --sharpness "  + str(sharpness2/10)
        #print(rpistr2)
        s = subprocess.Popen(rpistr2, shell=True, preexec_fn=os.setsid)
        poll = s.poll()
        while poll != None:
            print("waiting...")
            poll = s.poll()

    if restart == 1 and time.monotonic() - timer > 1:
        if trace == 1:
            print ("Step 14 RESTART")
        timer = time.monotonic()
        restart = 0
        poll = p.poll()
        if poll == None:
            os.killpg(p.pid, signal.SIGTERM)
        # clear ram
        zpics = glob.glob('/run/shm/test*.jpg')
        for tt in range(0,len(zpics)):
             os.remove(zpics[tt])
        if same_cams == 0:
            Camera_Version()
        pygame.display.set_caption('Action ' + cameras[Pi_Cam])
        Camera0_start(cap_width,cap_height,zoom)

            





                  





                      

