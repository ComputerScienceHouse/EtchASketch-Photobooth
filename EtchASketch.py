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

# Used by pygame for the window and image displays
pygame.init()
window = pygame.display.set_mode((640,480))
pygame.display.set_caption("Etch-A-Sketch")
screen = pygame.display.get_surface()


def displayImage(image):
    """
    Displays an opencv image on the pygame surface.

    @param  image   the opencv image to display
    """
    pilim = adaptors.Ipl2PIL(image)
    pg_img = pygame.image.frombuffer(pilim.tostring(), pilim.size, pilim.mode)
    pygame.display.flip()
    screen.blit(pg_img, (0,0))


def send_serial(c,s=0.01):
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
    numPad = [["7","4","1"],["8","5","2"],["9","6","3"]]
    for dy in range(len(numPad)):
        for dx in range(len(numPad[dy])):
            if numPad[dy][dx] is str(c):
                curX += dx
                curY -= dy

    opencv.cvSet2D(etch,curY,curX,[0,0,0])
    displayImage(etch)

def line(length,dir=6,inv=False):
    if (dir%3 is 0):
        dir = dir-2
    elif [1,4,7].contains(dir):
        dir = dir+2
    for i in range(length):
        draw(dir)
        if ser is not None:
            send_serial(dir)

def square(size,inv=False):
    '''
    Draw a square blip within a square.

    @param size length bounding square's side
    @param inv  inv    invert the x direction
    '''
    line(size,8)
    line(size,6,inv)
    line(size,2)

def triangle(size,inv=False):
    '''
    Draw a triangular blip within a square.

    @param size length bounding square's side
    @param inv  inv    invert the x direction
    '''
    seg = ((size**2)/2)**(1/2)
    line(seg/2,9,inv)
    line(seg/2,3,inv)

def semioct(size,inv=False):
    '''
    Draw a semi-octal blip within a square.  Should almost
    look like a semi-circle.

    @param size length bounding square's side
    @param inv  inv    invert the x direction
    '''
    seg = 5.0+(size*4.472136) 
    line(seg,8)
    line(seg/2,9,inv)
    line(seg,6,inv)
    line(seg/2,3,inv)
    line(seg,2)
    
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
    s = (r/255.0)*size
    l = size-b/2.0
    line(l,6,inv)
    triangle(s,inv)
    line(l,6,inv)
    # blue data
    s = (b/255.0)*size
    l = size-b/2.0
    line(l,4,inv)
    semicircle(s,not inv)
    line(l,4,inv)
    # green data
    s = (g/255.0)*size
    l = size-b/2.0
    line(l,6,inv)
    square(s,inv)
    line(l,6,inv)

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
    h = h/psize
    w = w/psize
    size = opencv.cvSize(w,h)
    scaled = opencv.cvCreateImage(size,8,3)
    opencv.cvResize(image,scaled)

    # Draw each pixel in the image
    for y in range(scaled.height):
        inv = y%2
        for x in range(scaled.width):
            s = opencv.cvGet2D(scaled,y,x)
            drawPixel(s[0],s[1],s[2],psize,inv)

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

    # Print starting time stamp
    print time.strftime ('Start Time: %H:%M:%S')

    # Load the image
    image = highgui.cvLoadImage(im);

    # Draw the image
    drawImage(image,h,w,psize)

    # Print end time stamp
    print time.strftime ('End Time: %H:%M:%S')

if __name__ == "__main__":
    sys.exit(main())
