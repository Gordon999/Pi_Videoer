# Pi_Videoer

A python script to capture images either triggered by motion or timelapse. It can capture either videos as still frames, upto 30fps at 1920 x 1080, which can be converted into MP4 files, or still photos.

## Screenshot

![screenshot](screen001.jpg)

To install:

Install latest RaspiOS based on Bullseye (tested with FULL 32bit version)

python3 -m pip install -U pygame --user

sudo apt install libsdl-gfx1.2-5 libsdl-image1.2 libsdl-kitchensink1 libsdl-mixer1.2 libsdl-sound1.2 libsdl-ttf2.0-0 libsdl1.2debian libsdl2-2.0-0 libsdl2-gfx-1.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0

sudo apt install python3-opencv

Download Pi_Videoer.py and copy to /home/pi (assuming your username is pi)

MAIN MENU

CAPTURE - switch capturing ON / OFF

RECORD  - click to capture a video or still picture

DETECTION SETTINGS - PREVIEW THRESHOLD (Shows detected pixel),Set Thresholds (set Lo Threshold to 0 for Timelapse, Detection levels, Area of dectection, Interval (set for Timelapse), Zoom (to help focusssing).

CAMERA SETTINGS 1 - Colour filter (R/G/B/FULL), Camera controls, Video Length

CAMERA SETTINGS 2 - Video Format, Camera Controls

OTHER SETTINGS    - FAN TEMPS (if enabled), EXT TRIGGER to trigger an external camera

SHOW & DELETE     - VIDEO (Shows triggered frame), PLAY VIDEO , FRAME (advance by single frames), DELETE FRAME, DEL to END (Deletes from selected frame to end of video), DELETE VIDEO, DELETE ALL VIDS (RIGHT mouse click), SHOW ALL VIDEOS (sequences through all triggered frames)

MAKE MP4  - VIDEO (Shows triggered frame), PLAY VIDEO , FRAME (advance by single frames), DELETE FRAME, DEL to END (Deletes from selected frame to end of video), MAKE A MP4 (makes an mp4 from chosen video), MAKE ALL MP4s (makes seperate MP4s from ALL Videos), MAKE FULL MP4 (Makes a MP4 from ALL Videos), MOVE MP4s to USB (moves MP4s from SD card ro USB if installed)

VIDEOS / PICTURES - Choose to capture Videos or Still Pictures, shows number stored in RAM and on SD CARD

SD HOUR - will shutdown at this time. set to 0 to disable.

COPY / EXIT - COPY will copy all stored JPGs (Video and Pictures) to USB. EXIT to exit script.
