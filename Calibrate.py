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
DEFAULT_OUTPUT_HEIGHT = 720
DEFAULT_OUTPUT_WIDTH = 960
DEFAULT_PIXEL_SCALE = 4
#DEFAULT_SERIAL_PORT = -1
DEFAULT_SERIAL_PORT = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A70063dg-if00-port0"
SCALES = [1,.799,1,.799,1,1,1,1,1]
BACKLASHES = [0,11,0,13,0,10,0,11,0]




def displayImage(image,x=0):
    """
    Displays an opencv image on the pygame surface.

    @param  image   the opencv image to display
    """
    global window, screen
    # Initialize pygame if not already initialized
    if not pygame.display.get_init():
        pygame.init()
        window = pygame.display.set_mode((image.width,image.height))
        pygame.display.set_caption("Etch-A-Sketch")
        screen = pygame.display.get_surface()

    pilim = adaptors.Ipl2PIL(image)
    pg_img = pygame.image.frombuffer(pilim.tostring(), pilim.size, pilim.mode)
    pygame.display.flip()
    screen.blit(pg_img, (0,0))
    if (not x):
        displayImage(image,1)


def sendSerial(c,s=0.01):
    """
    Move the cursor one unit in any numpad direction.

    @param  c  send the serial charicter c
    @param  s  sleep time
    """
    global ser
    
    time.sleep(s)
    ser.write(str(c))

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
                    curY = 0
                elif curY >= DEFAULT_OUTPUT_HEIGHT:
                    curY = DEFAULT_OUTPUT_HEIGHT-1 
                if curX < 0:
                    curX = 0
                elif curX >= DEFAULT_OUTPUT_WIDTH:
                    curX = DEFAULT_OUTPUT_WIDTH-1 
                opencv.cvSet2D(output,curY,curX,[0,0,0])
                #displayImage(output)

def calibrate(dir):
    return SCALES[dir-1]

def line(length,dir=6,inv=False):
    '''
    Draw a line of length in the numpad direction dir.

    @param length  the length of the line
    @param dir     integer 1-9 representing numpad direction
    @param inv     if true, this inverts the x direction
    '''
    global ser,lastdir
    # Invert
    if inv and (dir%3 is 0):
        dir = dir-2 
    elif inv and (dir in [1,4,7]):
        dir = dir+2

    # Calibrate
    scale = calibrate(dir)

    # Backlash
    xdir = None
    ydir = None
    if dir in [1,4,7]:
        xdir = -1
    elif dir in [9,6,3]:
        xdir = 1
    if dir < 4:
        ydir = -1
    elif dir > 6:
        ydir = 1
    if xdir is not None and ydir is not None:
        if xdir+last_dir[0] is 0:
            [sendSerial(5+xdir) for x in range(BACKLASHES[4+xdir])]
        if ydir+last_dir[1] is 0:
            [sendSerial(dir-((dir%3)-1)) for x in range(BACKLASHES[dir-(dir%3)])]
    last_dir = [xdir,ydir] 

    # Draw
    for i in range(int(length)):
        draw(dir)

    for i in range(int(scale*length)):
        if not (ser is 0):
            if i is 0:
                sendSerial(dir,0.2)
            else:
                sendSerial(dir)

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
    
def drawPixel(c,size,inv=False):
    """
    Draw a single pixel of the input image into a pixel of
    specified size.

    @param  c      list of 3 color intensities between 0 and 1
    @param  size   size of the pixel after drawn
    @param  inv    reverse drawing direction
    """
    c = [int(j*size) for j in c]
    c.sort()
    c.reverse()
    sp = (size-sum(c))/2
    e = size-((2*sp)+sum(c))
    if (sp >= 0):
        line(sp,6,inv)
    triangle(c[0],inv)
    if (sp < 0):
        line(abs(sp),4,inv)
    semioct(c[1],inv)
    if (sp < 0):
        line(abs(sp+e),4,inv)
    square(c[2],inv)
    if (sp >= 0):
        line(sp+e,6,inv)

def getFeedback():
     events = pygame.event.get()
     for event in events:
         if event.type == QUIT:
             exit() 
         elif (event.type == KEYDOWN):
             if (event.key == K_l):
                 print "Backlash for L-R is at "+str(BACKLASHES[5]) 
                 print "Enter new value: "
                 BACKLASHES[5] = int(raw_input())
             elif (event.key == K_k):
                 print "Backlash for D-U is at "+str(BACKLASHES[7]) 
                 print "Enter new value: "
                 BACKLASHES[7] = int(raw_input())
             elif (event.key == K_j):
                 print "Backlash for U-D is at "+str(BACKLASHES[1]) 
                 print "Enter new value: "
                 BACKLASHES[1] = int(raw_input())
             elif (event.key == K_h):
                 print "Backlash for R-L is at "+str(BACKLASHES[3]) 
                 print "Enter new value: "
                 BACKLASHES[3] = int(raw_input())

def calibrationRoutine(s):
    """
    Runs a routine that prompts the user to correct the error.

    @param  s  size of each line
    """
    s=s+0.00

    while 1:
        [line(s,i) for i in [2,6,8,4]]
        getFeedback()
        s += 20


def main(argv=None):

    # declair globals
    global ser, output, curX, curY, last_dir

    # Open serial connection
    ser = serial.Serial(DEFAULT_SERIAL_PORT, 9600, timeout=1)
    last_dir = 6

    # Print starting time stamp
    print time.strftime ('Start Time: %H:%M:%S')

    # Create the output image
    curX = 0
    curY = 0
    output = opencv.cvCreateImage(opencv.cvSize(DEFAULT_OUTPUT_WIDTH,DEFAULT_OUTPUT_HEIGHT), opencv.IPL_DEPTH_8U, 3)
    opencv.cvZero(output)
    opencv.cvNot(output,output)

    global window, screen
    # Initialize pygame if not already initialized
    if not pygame.display.get_init():
        pygame.init()
        window = pygame.display.set_mode((DEFAULT_OUTPUT_WIDTH,DEFAULT_OUTPUT_HEIGHT))
        pygame.display.set_caption("Etch-A-Sketch")
        screen = pygame.display.get_surface()
    
    # Draw the image
    calibrationRoutine(200)

    # Show the image
    displayImage(output)

    # Print end time stamp
    print time.strftime ('End Time: %H:%M:%S')

    # loop
    while(1):
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT or (event.type == KEYDOWN):
		exit()

def exit():
    # Exit on keyboard event
    line(DEFAULT_OUTPUT_WIDTH,4)
    line(DEFAULT_OUTPUT_WIDTH,8)
    sys.exit(0)
    

if __name__ == "__main__":
    sys.exit(main())
