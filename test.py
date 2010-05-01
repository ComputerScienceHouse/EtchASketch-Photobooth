from EtchASketch import *

# declair globals
global ser, output, curX, curY

# Open serial connection
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

# Used by pygame for the window and image displays
global window, screen
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

def line(length,dir=6,inv=False):
    '''
    Draw a line of length in the numpad direction dir.

    @param length  the length of the line
    @param dir     integer 1-9 representing numpad direction
    @param inv     if true, this inverts the x direction
    '''
    global ser
    # Invert
    if inv and (dir%3 is 0):
        dir = dir-2 
    elif inv and (dir in [1,4,7]):
        dir = dir+2

    # Calibrate
    scale = calibrate(dir)

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

def testShapes():
    line(150,3)
    square(150)
    triangle(150,1)
    semioct(150)
    
def testPixel():
    line(150,3)
    drawPixel(255,128,5,100)
    line(50,4)
    drawPixel(128,100,255,100,1)


testShapes()
displayImage(etch)

# loop
while(1):
    events = pygame.event.get()
    for event in events:
        if event.type == QUIT or (event.type == KEYDOWN):
            # Exit on keyboard event
            sys.exit(0)
