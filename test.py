from EtchASketch import *

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


testPixel()
displayImage(etch)
displayImage(etch)

# loop
while(1):
    events = pygame.event.get()
    for event in events:
        if event.type == QUIT or (event.type == KEYDOWN):
            # Exit on keyboard event
            sys.exit(0)
