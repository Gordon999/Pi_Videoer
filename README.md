# Pi_Videoer

A python script to capture images triggered by motion . Uses Raspberry OS BULLSEYE and libcamera-vid / still.
It can capture videos as still frames, upto 30fps at 1920 x 1080, which can be converted into MP4 files.

lt has some editing facilities, delete individual frames or delete all frames from start or to end of video.

Pi4 recommended.

## Screenshot

![screenshot](screen002.jpg)

To install:

Install latest FULL RaspiOS based on Bullseye (tested with FULL 32bit and 64bit versions)

sudo apt install python3-opencv

Download Pi_Videoer.py and copy to /home/pi (assuming your username is pi)

MAIN MENU

CAPTURE - switch capturing ON / OFF

RECORD  - click to capture a video

DETECTION SETTINGS - PREVIEW THRESHOLD (Shows detected pixels),Set Thresholds, Detection levels, Area of detection, Colour Filter (R/G/B/FULL),Zoom (to help focusing), Noise Reduction (OFF/LOW/HIGH).

CAMERA SETTINGS 1 -  Camera Controls

CAMERA SETTINGS 2 - Video Format, Video Length,Video pre-frames, more Camera Controls, Interval

CAMERA SETTINGS 3 -  Focus (Manual / Auto for v3 camera), Square Format video, SF Position, Detection Speed

OTHER SETTINGS    - Auto Limit, RAM limit, FAN TEMPS (if GPIO enabled), EXT TRIGGER to trigger an external camera (if GPIO enabled), Copy JPGs to USB

SHOW, DELETE & DELETE     - VIDEO (Shows triggered frame), PLAY VIDEO , FRAME (advance by single frames), DELETE FRAME, DEL from START /to END , DELETE VIDEO, DELETE ALL VIDS (RIGHT mouse click), SHOW ALL VIDEOS (sequences through all triggered frames), MAKE MP4 menu

MAKE MP4  - Set MP4 FPS, VIDEO (Shows triggered frame), PLAY VIDEO , FRAME (advance by single frames), DELETE FRAME, DEL from START / to END , MAKE A MP4 (makes an mp4 from chosen video), MAKE ALL MP4s (makes seperate MP4s from ALL Videos), MAKE FULL MP4 (Makes a MP4 from ALL Videos), MOVE MP4s to USB (moves MP4s from SD card to USB if installed), MP4 Annotate with date and time

SD HOUR - will shutdown at this time. set to 0 to disable.

EXIT - EXIT to exit script. ALWAYS USE THIS TO EXIT, OR You will need to reboot your pi.
