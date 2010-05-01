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
DEFAULT_SERIAL_PORT = "/dev/ttyUSB0"
BACKLASHES = [0,6,0,13,0,16,0,6,0]
SCALES = [1,.799,1,0.7655180952381,1,0.95809523809524,1,1,1]




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
                    print "Out of Bounds: ("+str(curX)+", "+str(curY)+")"
                    curY = 0
                elif curY >= DEFAULT_OUTPUT_HEIGHT:
                    print "Out of Bounds: ("+str(curX)+", "+str(curY)+")"
                    curY = DEFAULT_OUTPUT_HEIGHT-1 
                if curX < 0:
                    print "Out of Bounds: ("+str(curX)+", "+str(curY)+")"
                    curX = 0
                elif curX >= DEFAULT_OUTPUT_WIDTH:
                    print "Out of Bounds: ("+str(curX)+", "+str(curY)+")"
                    curX = DEFAULT_OUTPUT_WIDTH-1 
                opencv.cvSet2D(output,curY,curX,[0,0,0])

def calibrate(dir):
    return SCALES[dir-1]

def line(length,dir=6,inv=False):
    '''
    Draw a line of length in the numpad direction dir.

    @param length  the length of the line
    @param dir     integer 1-9 representing numpad direction
    @param inv     if true, this inverts the x direction
    '''
    global ser,last_dir
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
    if last_dir[0] is not None and xdir is not None and xdir+last_dir[0] == 0:
        print "backlash in x:", last_dir[0]
        [sendSerial(5+xdir) for x in range(BACKLASHES[4+xdir])]
    if last_dir[1] is not None and ydir is not None and ydir+last_dir[1] == 0:
        print "backlash in y:", last_dir[1]
        [sendSerial(dir) for x in range(BACKLASHES[dir-1])]
    print "last dir was:", last_dir
    if xdir is not None:
      last_dir[0] = xdir
    if ydir is not None:
      last_dir[1] = ydir
    print "last dir is now:", last_dir
        
    # Draw
    for i in range(int(length)):
        draw(dir)

    for i in range(int(scale*length)):
        if not (ser is 0):
            if i is 0:
                sendSerial(dir,0.2)
            else:
                sendSerial(dir)

def square(size,invx=False,invy=0):
    '''
    Draw a square blip within a square.

    @param size length bounding square's side
    @param inv  inv    invert the x direction
    @param invy invert the y direction
    '''

    line(size,abs((10*invy)-2))
    line(size,6,invx)
    line(size,abs((10*invy)-8))

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
    line(size/2,6,inv)
    line(c[0],2)
    line(c[0],6,inv)
    line(c[0],8)
    line(c[0],4,inv)
    line(c[1],8)
    line(c[1],6,inv)
    line(c[1],2)
    line(c[1],4,inv)
    line(c[2],2)
    line(c[2],6,inv)
    line(c[2],8)
    line(c[2],4,inv)
    line(size/2,6,inv)

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
    h = (h/psize)-2
    w = (w/psize)-2
    size = opencv.cvSize(w,h)
    scaled = opencv.cvCreateImage(size,8,3)
    red = opencv.cvCreateImage(size,8,1)
    blue = opencv.cvCreateImage(size,8,1)
    green = opencv.cvCreateImage(size,8,1)
    opencv.cvSplit(scaled,blue,green,red,None)
    opencv.cvEqualizeHist(red,red)
    opencv.cvEqualizeHist(green,green)
    opencv.cvEqualizeHist(blue,blue)
    opencv.cvMerge(red,green,blue,None,scaled)
    opencv.cvResize(image,scaled,opencv.CV_INTER_LINEAR)
    opencv.cvNot(scaled,scaled)

    # Draw each pixel in the image
    xr = range(scaled.width)
    for y in range(scaled.height):
        for x in xr:
            s = opencv.cvGet2D(scaled,y,x)
            s = [s[j] for j in range(3)]
            if (sum(s)/710.0 < 1.0/psize):
                line(psize,6,(xr[0]>0))
            else:
                drawPixel([j/255.0 for j in s],psize,(xr[0]>0))
        line(psize,2)
        xr.reverse()
        displayImage(output)
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT:
		exit()

def main(argv=None):
    if argv is None:
        argv = sys.argv
    if len(argv) <= 1 or argv[1] is "-":
        im = DEFAULT_INPUT_IMAGE
    else:
        im = argv[1]
    if len(argv) <= 2 or argv[2] is "-":
        psize = DEFAULT_PIXEL_SCALE
    else:
        psize = int(argv[2])
    if len(argv) <= 3 or argv[3] is "-":
        h = DEFAULT_OUTPUT_HEIGHT
    else:
        h = int(argv[3])
    if len(argv) <= 4 or argv[4] is "-":
        w = DEFAULT_OUTPUT_WIDTH
    else:
        w = int(argv[4])
    if len(argv) <= 5 or argv[5] is "-":
        serialport = DEFAULT_SERIAL_PORT
    else:
        serialport = argv[5]

    # declair globals
    global ser, output, curX, curY, last_dir

    # Open serial connection
    if serialport is not -1:
        ser = serial.Serial(serialport, 9600, timeout=1)
    else:
        ser = 0
    last_dir = [None,None]

    # Print starting time stamp
    print time.strftime ('Start Time: %H:%M:%S')

    # Load the image
    image = highgui.cvLoadImage(im)

    # Create the output image
    curX = 0
    curY = 0
    output = opencv.cvCreateImage(opencv.cvSize(w,h), opencv.IPL_DEPTH_8U, 3)
    opencv.cvZero(output)
    opencv.cvNot(output,output)
    
    # Draw the image
    drawImage(image,h,w,psize)

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
