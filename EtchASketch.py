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
#import serial
import pygame

### Global Variables ###

## Used for the serial connection
#usbport = '/dev/ttyUSB0'
#ser = serial.Serial(usbport, 9600, timeout=1)

# Used for camera image capturing
camera = highgui.cvCreateCameraCapture(0)
fps = 30.0

# Used by move cursor to track and display cursor movements
etch = opencv.cvCreateImage(opencv.cvSize(640,480), opencv.IPL_DEPTH_8U, 3)
opencv.cvZero(etch)
opencv.cvNot(etch,etch)
curX = 0
curY = 0

# Used by pygame for the window and image displays
#pygame.init()
#window = pygame.display.set_mode((640,480))
#pygame.display.set_caption("Etch-A-Sketch")
#screen = pygame.display.get_surface()


def displayImage(image):
    """
    Displays an opencv image on the pygame surface.

    @param  image   the opencv image to display
    """
    pilim = adaptors.Ipl2PIL(image)
    pg_img = pygame.image.frombuffer(pilim.tostring(), pilim.size, pilim.mode)
    pygame.display.flip()
    screen.blit(pg_img, (0,0))


def moveCursor(dx,dy):
    """
    Move the cursor one unit in any direction.  The display is then refreshed.

    @param  dx  change in x coord, 1 is right, -1 is left
    @param  dy  change in y coord, 1 is up, -1 is down
    """
#    global ser
    global curX, curY
    
#    # Send serial commands to etch-a-sketch
#    numPad = [["7","4","1"],["8","5","2"],["9","6","3"]]
#    i = dx+1
#    j = 1-dy
#    dir = numPad[i][j]
#    if (dx == 1 and curX%4 == 0):
#        time.sleep(0.01)
#        ser.write(dir)
#    if (dy == 1 and curY%4 == 0):
#        time.sleep(0.01)
#        ser.write(dir)
#    time.sleep(0.01)
#    ser.write(dir)

    # Draw image representation of etch-a-sketch
    curX += dx
    curY -= dy
    opencv.cvSet2D(etch,curY,curX,[0,0,0])
    displayImage(etch)

def parseLine(image):
    """
    Traces over an etched image, erasing the paths it has taken as it goes.

    @param  image   an etched image
    @return                 the parameter image mutated to what should be all
                                 white
    """
    x = 0
    y = 0
    altPaths = []

    # While loop cycles through each new point on the line
    while True:
        #print "X: " + str(x)
        #print "Y: " + str(y)

        # Get ranges rx, and ry to check surroundings and stay in bounds
        rx = range(-1,2)
        ry = range(-1,2)
        if y-1 < 0:
            ry = range(-y,2)
        elif y+1 > image.height-1:
            ry = range(-1,image.height-y)
        if x-1 < 0:
            rx = range(-x,2)
        elif x+1 > image.width-1:
            rx = range(-1,image.width-x)

        # Aquire a next move by prioritizing based on direction
        move = [0,0,255,0,0]
        for dy in ry:
            for dx in rx:
                if not (dx==0 and dy==0):
                    c = opencv.cvGet2D(image,y+dy,x+dx)[0]
                    if c < move[2]: # Check for higher priority
                        move[0] = x+dx
                        move[1] = y+dy
                        move[2] = c+abs(dy)+abs(dx)-1
                        move[3] = dx
                        move[4] = dy
                    if c == 0:
                        # Add a "tally" to all the possible paths
                        altPaths.append([])

        # Mark point so as not to return unnessicarily
        opencv.cvSet2D(image,y,x,[255])

        if move[2]<255 and not (x==image.width-1 and y==image.height-1):
            # See if there was a winner
            if len(altPaths)-1 < 0:
				altPaths.append([])
            altPaths[len(altPaths)-1].append([move[3],move[4]])
            moveCursor(move[3],-move[4])
            x = move[0]
            y = move[1]
        elif len(altPaths)>0 and not (x==image.width-1 and y==image.height-1):
            # Otherwise backtrack to the nearest alternate path
            altPaths[len(altPaths)-1].reverse()
            for m in altPaths[len(altPaths)-1]:
                moveCursor(-m[0],m[1])
                x -= m[0]
                y -= m[1]
            altPaths.pop()
        else:
            # break if there are no alternate paths
            break

    return image

def shadeImage(image):
    """
    Shade an image in a way that will allow it to be drawn on an
    etch-a-sketch.

    @param  image   an opencv image with at least 3 channels
    @return                 the input image mutated into a shaded image
    """
    shaded = opencv.cvCreateImage(opencv.cvSize(image.width,image.height), opencv.IPL_DEPTH_8U, 1)
    cont = opencv.cvCreateImage(opencv.cvSize(image.width,image.height), opencv.IPL_DEPTH_8U, 1)

    # Cycle through image and use simple math functions to create a new one
    for y in range(image.height):
        for x in range(image.width):
            # Decrease the range of color values so image forms lines
            c1 = (((int(opencv.cvGet2D(image,y,x)[0])/30)+2)**2)/4
            c2 = (((int(opencv.cvGet2D(image,y,x)[1])/30)+2)**2)/4
            c3 = (((int(opencv.cvGet2D(image,y,x)[2])/30)+2)**2)/4

            # Turns pixel black if it is in one of the functions
            # Radial function would be (int((((y**2)+(x**2))**.5))%c3==0)
            if x%c1==0 or y%c2==0 or (x+y)%(2*c3)==0 or (x-y)%(2*c3)==0 or y==0 or x==image.width-1 or y==image.height-1 or x==0:
                opencv.cvSet2D(shaded,y,x,[0])
            else:
                opencv.cvSet2D(shaded,y,x,[255])

    # Modify the input image to the shaded image
    opencv.cvCvtColor(shaded, image, opencv.CV_GRAY2BGR)

    return image

def getImage():
    """
    Gets an image from the camera using opencv, and delays retrieval with
    pygame.

    @return     The image retrieved from the camera.
    """
    pygame.time.delay(int(1000 * 1.0/fps))
    im = highgui.cvQueryFrame(camera)
    return im

if __name__ == "__main__":
    """
    Main method.

    """
    shotTaken = False
    while True:
        # Show the webcam image until the shot is taken
        if not shotTaken:
            im = getImage()

        # Get the keydown event to start processing
        events = pygame.event.get()
        for event in events:
            if event.type == KEYDOWN and not shotTaken:
                # Take the shot and process it
                shotTaken = True
                
                # Print starting time stamp
                print time.strftime ('Start Time: %H:%M:%S')

                # Shade the image
                shaded = shadeImage(im)
                
                # Parse the shaded image
                im = parseLine(shaded)

                # Print end time stamp
                print time.strftime ('End Time: %H:%M:%S')
                
            elif event.type == QUIT or (event.type == KEYDOWN and shotTaken):
                # Exit on second keyboard event
                sys.exit(0)

        # Write the finished image to a file
        out = adaptors.Ipl2PIL(im)
        pg_img = pygame.image.frombuffer(out.tostring(), out.size, out.mode)
        pygame.image.save(pg_img,"etch.jpg")

        # Display the finished image
        displayImage(im)
