#!/usr/bin/python
#
# Bamclone - Dave Hartburn August 2023
# A clone of the old Archimedes game bambuzle, by Kuldip S Pardesi, published by Arxe Systems

import pygame
import csv, math, random
import os
from tileImages import tileImages

# Constants
# =========
TILESIZE = 140          # The size of individual tiles
TILESX = 8              # Number of tiles across the X
TILESY = 6               # Number of tiles across the y
WINMARG = TILESIZE/3      # The margin around the tiles
PWIDTH=TILESIZE/2.5     # Pipe width. Pipes and balls are based on this size
WHSIZE=TILESIZE*0.9
BALLSIZE=PWIDTH*0.7
BALLSPEED=3             # Number of pixels to move per cycle
ROTSTEPS=10             # Number of steps to rotate the wheel in

# Colours
BG=(0,0,64)
LINECOL=(200,200,200)
LINEWIDTH=2
# Ball colours
BALLCOLS = {
    "R":(255,0,0),
    "G":(0,255,0),
    "B":(0,0,255),
    "Y":(255,255,0)
}

# List of what tiles have open, used to decide if a ball can flow
openNorth=["V","NEL","NWL","W"]
openEast=["H", "ST", "NEL", "SEL", "W"]
openSouth=["V", "SEL", "SWL", "W"]
openWest=["H", "ST", "NWL", "SWL", "W"]

# Claculate the window size
WIDTH=(TILESIZE*TILESX)+(WINMARG*2)
HEIGHT=(TILESIZE*TILESY)+(WINMARG*2)
origin=(WINMARG, WINMARG)


# Start pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bamclone")
# Init fonts
pygame.font.init()
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()

# Game essentials
FPS = 120            # Game frames per second

# Load in time images
tImg = tileImages(TILESIZE, PWIDTH)

# Define the level array
levelData=[]
wheels={}
southTs={}

# Define opposites, used for traversing tiles
opposite={"N":"S","E":"W","S":"N","W":"E"}

# Load images
gradball = pygame.image.load(os.path.join('sprites','300gradball.png')).convert()
gradball.set_colorkey((0,0,0))

# ************* Game classes *******************
class Ball(pygame.sprite.Sprite):
    def __init__(self, col):
        pygame.sprite.Sprite.__init__(self)
        self.colour=col
        self.image=ballImage[col]
        self.newBall=True           # Will change to false on first dock/entry ally is free
        self.direction="W"          # Use 4 compass points as directions
        self.wheel=-1               # Will have the number of a wheel if docked, -1 if in motion
        self.myTile=(-1,-1)         # Track what tile we are on
        self.rect=self.image.get_rect()
        self.rect.x=WINMARG+TILESIZE*TILESX
        self.rect.centery=WINMARG+TILESIZE/2
        self.hitMiddle=False    # Track if we have been in the middle of the tile yet
        self.msg=""             # A persistant message which can be set, useful for debugging. Will print if changed on update

    def update(self):
        if(self.wheel==-1):
            msg=""  # Blank debugging message if needed
            # What tile coord are we in, and what tile type is it?
            xtile=math.floor((self.rect.centerx-WINMARG)/TILESIZE)
            # Special case on launch as the ball is off the board
            if(xtile>=TILESX):
                self.rect.x-=BALLSPEED
                return
            
            ytile=math.floor((self.rect.centery-WINMARG)/TILESIZE)
            # Create tuple as useful index
            tileTup=(xtile, ytile)
            if(tileTup!=self.myTile):
                #print("I'm on a new tile")
                self.hitMiddle=False
                self.myTile=tileTup
            tiletype=levelData[ytile][xtile]
            #msg="Tile coord ({},{}), type {}".format(xtile,ytile, tiletype)
            # Calculate position within the tile
            xpos=self.rect.centerx-WINMARG-TILESIZE*xtile
            ypos=self.rect.centery-WINMARG-TILESIZE*ytile

            # Are we over a wheel?
            if(tiletype=="W"):
                #msg="On a wheel, with direction going "+self.direction
                point=opposite[self.direction]
                whid=(xtile,ytile)
                whdoc=wheels[whid].dockingpos[point]
                if(self.direction=="S" and ypos>whdoc[1]):
                    # Dock to the north
                    self.dock(whid, point)
                elif(self.direction=="N" and ypos<whdoc[1]):
                    # Dock to the south
                    self.dock(whid, point)
                elif(self.direction=="E" and xpos>whdoc[0]):
                    # Dock to the west
                    self.dock(whid, point)
                elif(self.direction=="W" and xpos<whdoc[0]):
                    # Dock to the East
                    self.dock(whid, point)
            else:
                #msg="Not on a wheel"
                bounce=False
                # Are we at the tile edge?
                if(self.direction=="W" and (xpos-BALLSIZE/2)<BALLSPEED):
                    # Check the next tile to the left
                    if(xtile==0):
                        # Edge of the game screen
                        bounce=True
                    else:
                        # If the next tile doesn't have an open east, also bounce
                        nextTile=levelData[ytile][xtile-1]
                        if not (nextTile in openEast):
                            bounce=True
                    if(bounce):
                        self.direction="E"
                        self.hitMiddle=False
                elif(self.direction=="E" and (xpos+BALLSIZE/2)>TILESIZE):
                    # Check the next tile to the right
                    if(xtile==TILESX-1):
                        bounce=True
                    else:
                        # If the next tile doesn't have an open west, also bounce
                        nextTile=levelData[ytile][xtile+1]
                        if not (nextTile in openWest):
                            bounce=True
                    if(bounce):
                        self.direction="W"
                        self.hitMiddle=False
                # elif(self.direction=="S" and (ypos+BALLSIZE/2)>TILESIZE):
                #     print("Leaving a south tile")

                # Are we at the tile middle?
                if(self.hitMiddle==False):
                    # Track with hitMiddle, we don't want this executing multiple times.
                    # This must reset as we enter a new tile
                    if(self.direction=="W" and xpos<TILESIZE/2):
                        self.hitMiddle=True
                    elif(self.direction=="E" and xpos>TILESIZE/2):
                        self.hitMiddle=True
                    elif(self.direction=="N" and ypos<TILESIZE/2):
                        self.hitMiddle=True
                    elif(self.direction=="S" and ypos>TILESIZE/2):
                        self.hitMiddle=True
                    if(self.hitMiddle):
                        # Take action on certain tiles, such as corners or Ts
                        if(tiletype=="ST"):
                            if(checkSTopen(self.myTile)):
                                self.direction="S"
                        elif(tiletype.endswith("L")):
                            # We are on a corner, change direction
                            self.direction=LotherEnd(tiletype, opposite[self.direction])
                                
                    # End of hitMiddle actions
            # End of 'not on a wheel'

            if(msg!="" and msg!=self.msg):
                print(msg)
                self.msg=msg


            # Move the ball if in motion
            if(self.direction=="W"):
                self.rect.x-=BALLSPEED
            elif(self.direction=="E"):
                self.rect.x+=BALLSPEED
            elif(self.direction=="N"):
                self.rect.y-=BALLSPEED
            elif(self.direction=="S"):
                self.rect.y+=BALLSPEED
    # End of update

    def dock(self, whid, point):
        # Dock the ball in the wheel
        self.direction=point
        self.wheel=whid
        coord=wheels[whid].dockBall(self, point)
        self.setCoord(coord)
        if(self.newBall):
            # This was a new ball, the top ally is now clear
            self.newBall=False
            launchNext()

    def setCoord(self, coord):
        # Set the coordinate or the ball.
        # Coord received will be center coords relative to the current tile
        self.rect.centerx=coord[0]+WINMARG+self.myTile[0]*TILESIZE
        self.rect.centery=coord[1]+WINMARG+self.myTile[1]*TILESIZE



# End of Ball class
    
class Wheel(pygame.sprite.Sprite):
    def __init__(self, id):
        pygame.sprite.Sprite.__init__(self)
        #print("Init wheel ", id)
        self.id=id
        self.rotating=False         # Track if we are rotating
        self.rotangle=0
        self.blown=False
        self.docked={"N":None,"E":None,"S":None,"W":None}
        self.numDocked=0
        # Docking positions for drawing the balls and doing cutouts
        self.halftile=math.floor(TILESIZE/2)
        self.ballrad=math.floor(BALLSIZE/2)
        self.cutdist=math.floor(WHSIZE/2)-self.ballrad+5
        self.dockingOrig={
            "N":(TILESIZE/2,self.halftile-self.cutdist),
            "E":(self.halftile+self.cutdist,TILESIZE/2),
            "S":(TILESIZE/2,self.halftile+self.cutdist),
            "W":(self.halftile-self.cutdist,TILESIZE/2),
        }
        self.dockingpos=self.dockingOrig.copy()        # Save a copy to revert to
        self.image=self.imageGen()
        self.rect=self.image.get_rect()
        self.rect.centerx=WINMARG+TILESIZE*id[0]+TILESIZE/2
        self.rect.centery=WINMARG+TILESIZE*id[1]+TILESIZE/2
        self.rotlimit=math.pi/2         # 90 degrees in radians
        self.rotdelta=self.rotlimit/ROTSTEPS
 
    def update(self):
        if(self.rotating):
            self.rotangle+=self.rotdelta
            ang=self.rotangle
            # Calculate position changes
            h=self.cutdist
            xdelta=math.sin(ang)*h
            ydelta=h-math.cos(ang)*h
            # Adjust the docking positions, x then y
            # North
            x=self.dockingOrig["N"][0]+xdelta
            y=self.dockingOrig["N"][1]+ydelta
            self.dockingpos["N"]=(x, y)
            # East
            x=self.dockingOrig["E"][0]-ydelta
            y=self.dockingOrig["E"][1]+xdelta
            self.dockingpos["E"]=(x, y)
            # South
            x=self.dockingOrig["S"][0]-xdelta
            y=self.dockingOrig["S"][1]-ydelta
            self.dockingpos["S"]=(x, y)
            # West
            x=self.dockingOrig["W"][0]+ydelta
            y=self.dockingOrig["W"][1]-xdelta
            self.dockingpos["W"]=(x, y)
            if(self.rotangle>self.rotlimit):
                self.rotating=False
                # Reset the docking positions to the original
                self.dockingpos=self.dockingOrig.copy()
                # Rotate the array of docked balls
                t=self.docked["W"]    # temporary
                self.docked["W"]=self.docked["S"]
                self.docked["S"]=self.docked["E"]
                self.docked["E"]=self.docked["N"]
                self.docked["N"]=t
            # Regenerate the image
            self.image=self.imageGen()
    # End of update


    def imageGen(self):
        img=wheelImage.copy()
        # Cut out slots or put in balls
        if(self.docked["N"]==None):
            pygame.draw.circle(img, pygame.SRCALPHA, self.dockingpos["N"], self.ballrad)
        else:
            self.docked["N"].setCoord(self.dockingpos["N"])

        if(self.docked["E"]==None):
            pygame.draw.circle(img, pygame.SRCALPHA, self.dockingpos["E"], self.ballrad)
        else:
            self.docked["E"].setCoord(self.dockingpos["E"])

        if(self.docked["S"]==None):
            pygame.draw.circle(img, pygame.SRCALPHA, self.dockingpos["S"], self.ballrad)
        else:
            self.docked["S"].setCoord(self.dockingpos["S"])

        if(self.docked["W"]==None):
            pygame.draw.circle(img, pygame.SRCALPHA, self.dockingpos["W"], self.ballrad)
        else:
            self.docked["W"].setCoord(self.dockingpos["W"])
        return img

    def handleEvent(self,event):
        if(self.rect.collidepoint(event.pos)):
            #print("I was clicked ", self.id)
            self.rotating=True
            self.rotangle=0

    def slotEmpty(self, d):
        # Is there a ball in slot d? True if empty, false if there is a ball
        if(self.docked[d]==None):
            return True
        else:
            return False
        
    def dockBall(self, ball, point):
        # Dock the ball and return coordinates for docking point
        self.docked[point]=ball
        self.numDocked+=1

        return self.dockingOrig[point]
# End of Wheel class

class SouthT():
    # southT class. These are special, used to drop balls from the top gully. There are a few rules:
    # - Balls will not drop if the wheel at the end of the T has a docked ball facing it
    # - Balls can not be ejected from the wheel in the direction of a southT
    #
    # I believe the original game had southTs mapping directly to wheels, but we need to permit
    # something more interesting
    def __init__(self, id):
        self.id=id      # ID is sent as a tuple of the tile coordinates
        #print("New southT at {}".format(id))
        self.linkedWheel=None
        self.wheelLoc=None          # Which location in the wheel does it check (N,E,S,W)
        
        # Find a wheel. We need to walk the path until we find it
        foundWheel=0        # Three states, 0 (not found), 1 (found), 2 (error)
        tilex=id[0]          # What tile are we on?
        tiley=id[1]
        entrydir="W"             # Which direction did we enter from? Doesn't really matter for a T
        #print("Finding the linked wheel")
        stepCount=0             # Used for error tracking
        while(foundWheel==0):
            # Find the next tile
           # print("Inspecting tile at {},{}".format(tilex, tiley))
            type=levelData[tiley][tilex]
            # Find the exit
            exit=None
            if(type=="ST"):
                # Special case, first tile, we should never encounter another one
                exit="S"
            else:
                # All tiles should have one entry and one exit. Build list of the open ends of types
                openEnds=[]
                if(type in openNorth):
                    openEnds.append("N")
                if(type in openEast):
                    openEnds.append("E")
                if(type in openSouth):
                    openEnds.append("S")
                if(type in openWest):
                    openEnds.append("W")
                if(len(openEnds)!=2):
                    errorQuit("Problem, we found the wrong number of open ends ", openEnds)
                    foundWheel=2
                    break
                # Which end do we look at?
                if(openEnds[0]==entrydir):
                    # We have entered from this end
                    exit=openEnds[1]
                else:
                    # We have entered from the other end
                    exit=openEnds[0]
            #print("Entry to current tile ({},{}) (a {}) from {}, exit to {}".format(tilex,tiley, type, entrydir, exit))
            # Find the coordinates of the next tile
            if(exit=="N"):
                nexty=tiley-1
                nextx=tilex
            elif(exit=="E"):
                nextx=tilex+1
                nexty=tiley
            elif(exit=="S"):
                nextx=tilex
                nexty=tiley+1
            elif(exit=="W"):
                nextx=tilex-1
                nexty=tiley
            #print("Next tile is at {},{}".format(nextx, nexty))
            # Have we exceeded limits?
            if(nextx<0 or nexty<0 or nextx>TILESX or nexty>TILESY):
                foundWheel=2
                errorQuit("Error, ST path took us off screen")
            else:
                # What direction do we enter the tile from?
                entrydir=opposite[exit]
                # Looks good, is the next tile a wheel?
                if(levelData[nexty][nextx]=="W"):   
                    # Yes
                    foundWheel=1
                    #print("Found a wheel")
                else:
                    # No, loop
                    tilex=nextx
                    tiley=nexty
            if(stepCount>(TILESX*TILESY)):
                foundWheel=2
                errorQuit("Error: Unable to find wheel, infinite loop from tile {}".format(self.id))
            else:
                stepCount+=1       
        # End of wheel while loop
        self.linkedWheel=(nextx,nexty)
        self.wheelLoc=entrydir
        #print("  Wheel found, linking ST to wheel {}, docking point {}".format(self.linkedWheel, self.wheelLoc))
    # End of init

    def isOpen(self):
        # Return if the path is open
        return wheels[self.linkedWheel].slotEmpty(self.wheelLoc)

# End of southT class

# ************* End of game classes ************

# ************* Functions **********************

# Draw the main game screen
def drawGameScreen():
    screen.fill(BG)

    # Draw a grid, which the tiles will sit on top of.
    # This code will become redundant
    # Vertical lines
    # for x in range(0,TILESX+1):
    #     pygame.draw.lines(screen, LINECOL, False, [(WINMARG+x*TILESIZE,WINMARG), (WINMARG+x*TILESIZE,HEIGHT-WINMARG)], LINEWIDTH)
    # # Horizontal
    # for y in range(0,TILESY+1):
    #     pygame.draw.lines(screen, LINECOL, False, [(WINMARG,WINMARG+y*TILESIZE),(WIDTH-WINMARG,WINMARG+y*TILESIZE)], LINEWIDTH)

    # Draw the tiles
    y=0
    for row in levelData:
        x=0
        for tname in row:
            img=tImg.getTile(tname)
            screen.blit(img, (WINMARG+TILESIZE*x, WINMARG+TILESIZE*y))
            x+=1
        y+=1
    
    all_sprites.draw(screen)
    # Cover up balls entering the screen
    pygame.draw.rect(screen, BG, [(WINMARG+TILESIZE*TILESX, WINMARG),(WINMARG,TILESIZE)])
    pygame.display.flip()
# End of drawGameScreen()

def genWheelImage():
    # Create the wheel image. We need a blank (without the cutouts) and the stationary wheel with
    # cutouts aligned to the pipes. But when rotating, the shine stays in the same place and the cut
    # outs rotate with the balls. As it may contain the balls, this has to be done on the fly.
    whsurf=pygame.Surface((TILESIZE,TILESIZE), pygame.SRCALPHA, 32)
    
    whmarg=(TILESIZE-WHSIZE)/2
    tmpsurf=pygame.Surface.copy(gradball)
    tmpsurf=pygame.transform.scale(tmpsurf, (WHSIZE,WHSIZE))
    whsurf.blit(tmpsurf,(whmarg,whmarg))
    return whsurf

def genBalls():
    # Generate the coloured balls
    #print("Generating balls")
    blist={}
    bmaster=pygame.transform.scale(gradball, (BALLSIZE,BALLSIZE))
    for b in BALLCOLS:
        bsurf=pygame.Surface((BALLSIZE,BALLSIZE), pygame.SRCALPHA,32)
        pygame.draw.circle(bsurf, BALLCOLS[b], (BALLSIZE/2,BALLSIZE/2), BALLSIZE/2)
        bmaster.set_alpha(128)
        bsurf.blit(bmaster, (0,0))
        blist[b]=bsurf
    return blist


# End of genBalls

def loadLevel(l):
    # Loads the level from file
    global levelData,wheels,southTs
    levelData=[]
    fileName="level"+str(l)+".csv"
    print("Loading file", fileName)
    lineCount=0
    with open(fileName) as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            #print(row)
            l=len(row)
            if(l!=TILESX):
                errorQuit("Error: In level file {}, line {} contains {} tiles, not {}".format(fileName, lineCount, l, TILESX))
            levelData.append(row)
            lineCount+=1
    # Check the number of lines loaded
    if(lineCount!=TILESY):
        errorQuit("Error: In level file {}, contains {} lines not {}".format(fileName, lineCount, TILESY))
    
    # Initialise wheels and south Ts
    wheels={}
    southTs={}
    coord=(-1,-1)
    y=0
    for row in levelData:
        x=0
        for tname in row:
            coord=(x, y)
            if(tname=="W"):
                wheels[coord]=Wheel(coord)
                all_sprites.add(wheels[coord])
            elif(tname=="ST"):
                southTs[coord]=SouthT(coord)
            x+=1
        y+=1
# End of loadLevel
        
def checkSTopen(tile):
    # Check if a tile is open to the south - is the associated wheel slot free?
    r=southTs[tile].isOpen()
    return r

def nextBall():
    # Pick a random colour for the next ball
    r=random.choice(list(BALLCOLS))
    return r

def LotherEnd(type, entry):
    # Returns the exit direction for a corner based on the entry
    # String should be of the format 'xyL', check what the first two characters are
    if(type[0]==entry):
        r=type[1]
    else:
        r=type[0]
    return r

# Quit if we have an error
def errorQuit(msg):
    print(msg)
    pygame.quit()
    exit(1)

def launchNext():
    # Launch the next ball and pick the one to come after
    global nextCol
    all_sprites.add(Ball(nextCol))
    nextCol=nextBall()
# ************* End of functions / Start of main code ******************

# Generate images
wheelImage = genWheelImage()
ballImage = genBalls()

loadLevel(1)

# Main loop
drawGameScreen()
running = True
# Add a ball to get us started
nextCol=nextBall()
all_sprites.add(Ball(nextCol))

while running:

    # Keep loop running at the right speed
    clock.tick(FPS)

    
    event = pygame.event.poll()
    if event.type == pygame.QUIT:
        running = False
    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_ESCAPE:
            running = False
            print("Escape - quitting")
    elif event.type == pygame.MOUSEBUTTONDOWN:
        # Button 3, right click. Did we click a wheel?
        if(event.button==3):
            #print("Right click")
            for w in wheels:
                wheels[w].handleEvent(event)
        elif(event.button==1):
            # Left click, did we click a ball?
            print("Left click")

    
    # else:
    #     print("Unknown event", event.type)
    #     print(event)
    # Update sprites
    all_sprites.update()

    # Draw / render the scree
    drawGameScreen()
# End of main loop

pygame.quit()