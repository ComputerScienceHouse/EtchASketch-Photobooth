#!/usr/bin/env python
#
#       EtchASketch.py
#       
#       Copyright 2009 Bryan Goldstein

import sys
import time
import opencv
from pygame.locals import *
from opencv import adaptors
from opencv import highgui
import serial
import pygame

### Global Constants ###
DEFAULT_INPUT_IMAGE = 'input.jpg'
DEFAULT_OUTPUT_HEIGHT = 480
DEFAULT_OUTPUT_WIDTH = 640
DEFAULT_PIXEL_SCALE = 10
DEFAULT_SERIAL_PORT = -1
#DEFAULT_SERIAL_PORT = '/dev/ttyUSB0'

## Global Variables ###

# Used by move cursor to track and display cursor movements
etch = opencv.cvCreateImage(opencv.cvSize(640,480), opencv.IPL_DEPTH_8U, 3)
opencv.cvZero(etch)
opencv.cvNot(etch,etch)
curX = 0
curY = 0



def displayImage(image):
    """
    Displays an opencv image on the pygame surface.

    @param  image   the opencv image to display
    """
    pilim = adaptors.Ipl2PIL(image)
    pg_img = pygame.image.frombuffer(pilim.tostring(), pilim.size, pilim.mode)
    pygame.display.flip()
    screen.blit(pg_img, (0,0))


def sendSerial(c,s=0.01):
    """
    Move the cursor one unit in any numpad direction.

    @param  c  send the serial charicter c
    @param  s  sleep time
    """
    global ser
    
    time.sleep(s)
    ser.write(c)

def draw(c):
    """
    Draw in any numpad direction to the screen.

    @param c numpad number representing direction
    """
    global curX, curY
    numPad = [[7,8,9],[4,5,6],[1,2,3]]
    for dy in range(len(numPad)):
        for dx in range(len(numPad[dy])):
            if numPad[dy][dx] is c:
                curX += dx-1
                curY += dy-1
                if curY < 0:
                    print "Out of Bounds: ("+str(curX)+", "+str(curY)+")"
                    curY = 0
                elif curY >= 480:
                    print "Out of Bounds: ("+str(curX)+", "+str(curY)+")"
                    curY = 479
                if curX < 0:
                    print "Out of Bounds: ("+str(curX)+", "+str(curY)+")"
                    curX = 0
                elif curX >= 640:
                    print "Out of Bounds: ("+str(curX)+", "+str(curY)+")"
                    curX = 639
                opencv.cvSet2D(etch,curY,curX,[0,0,0])


def line(length,dir=6,inv=False):
    if inv and (dir%3 is 0):
        dir = dir-2 
    elif inv and (dir in [1,4,7]):
        dir = dir+2
    for i in range(int(length)):
        draw(dir)
     #   if ser:
     #       sendSerial(dir)

def square(size,inv=False):
    '''
    Draw a square blip within a square.

    @param size length bounding square's side
    @param inv  inv    invert the x direction
    '''
    line(size,2)
    line(size,6,inv)
    line(size,8)

def triangle(size,inv=False):
    '''
    Draw a triangular blip within a square.

    @param size length bounding square's side
    @param inv  inv    invert the x direction
    '''
    line(size,3,inv)
    line(size,8)

def semioct(size,inv=False):
    '''
    Draw a semi-octal blip within a square.  Should almost
    look like a semi-circle.

    @param size length bounding square's side
    @param inv  inv    invert the x direction
    '''
    vert = int((2*size)/3)
    cap = int(size/3)
    e = int(size-(3.0*cap))
    line(vert+e,2)
    line(cap,3,inv)
    line(cap+e,6,inv)
    line(cap,9,inv)
    line(vert+e,8)
    
def drawPixel(r,g,b,size,inv=False):
    """
    Draw a single pixel of the input image into a pixel of
    specified size.

    @param  r      red color intensity (uint8)
    @param  g      green color intensity (uint8)
    @param  b      blue color intensity (uint8)
    @param  size   size of the pixel after drawn
    @param  inv    reverse drawing direction
    """
    # red data
    s = int((r/255.0)*size)
    l = (size-s)/2
    line(l,6,inv)
    triangle(s,inv)
    e = size-(s+(2*l));
    line(l+e,6,inv)
    # blue data
    s = int((b/255.0)*size)
    l = (size-s)/2
    line(l,4,inv)
    semioct(s,not inv)
    e = size-(s+(2*l));
    line(l+e,4,inv)
    # green data
    s = int((g/255.0)*size)
    l = (size-s)/2
    line(l,6,inv)
    square(s,inv)
    e = size-(s+(2*l));
    line(l+e,6,inv)
    # backup
    line(size/2,4,inv)

def drawImage(image,h,w,psize):
    """
    Draw the image as a continuous line on a surface h by w "pixels" where 
    each continuous line representation of a pixel in image is represented
    on the output suface using psize by psize "pixels".

    @param  image   an opencv image with at least 3 channels
    @param  h       integer representing the hight of the output surface
    @param  w       integer representing the width of the output surface
    @param  psize   ammount that each pixel in the input image is scaled up
    """
    h = h/(psize/2)-(psize/2)
    w = w/(psize/2)-(psize/2)
    size = opencv.cvSize(w,h)
    scaled = opencv.cvCreateImage(size,8,3)
    opencv.cvResize(image,scaled,opencv.CV_INTER_LINEAR)

    # Draw each pixel in the image
    xr = range(scaled.width)
    for y in range(scaled.height):
        xr.reverse()
        for x in xr:
            s = opencv.cvGet2D(scaled,y,x)
            if ((s[0]+s[1]+s[2])/710.0 < 2/psize):
                line(psize/2,6,(xr[0]>0))
            else:
                drawPixel(s[0],s[1],s[2],psize,(xr[0]>0))
        line(psize/2,2)
        displayImage(etch)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) <= 1:
        im = DEFAULT_INPUT_IMAGE
    else:
        im = argv[1]
    if len(argv) <= 2:
        h = DEFAULT_OUTPUT_HEIGHT
    else:
        h = argv[2]
    if len(argv) <= 3:
        w = DEFAULT_OUTPUT_WIDTH
    else:
        w = argv[3]
    if len(argv) <= 4:
        psize = DEFAULT_PIXEL_SCALE
    else:
        psize = argv[4]
    if len(argv) <= 5:
        serialport = DEFAULT_SERIAL_PORT
    else:
        serialport = argv[5]

    # Open serial connection
    global ser
    if serialport is not -1:
        ser = serial.Serial(serialport, 9600, timeout=1)
    else:
        ser = 0

    # Print starting time stamp
    print time.strftime ('Start Time: %H:%M:%S')

    # Load the image
    image = highgui.cvLoadImage(im)
    opencv.cvNot(image,image)
    
    # Used by pygame for the window and image displays
    global window, screen
    pygame.init()
    window = pygame.display.set_mode((640,480))
    pygame.display.set_caption("Etch-A-Sketch")
    screen = pygame.display.get_surface()

    # Draw the image
    drawImage(image,h,w,psize)

    # Show the image
    displayImage(etch)
    displayImage(etch)

    # Print end time stamp
    print time.strftime ('End Time: %H:%M:%S')

    # loop
    while(1):
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT or (event.type == KEYDOWN):
                # Exit on keyboard event
                sys.exit(0)

if __name__ == "__main__":
    sys.exit(main())
