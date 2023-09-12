#!/usr/bin/python
#
# Bamclone - Dave Hartburn August 2023
# A clone of the old Archimedes game bambuzle, by Kuldip S Pardesi, published by Arxe Systems

import pygame
import csv, math, random
import os, sys
from tileImages import tileImages

# Constants
# =========
TILESIZE = 120          # The size of individual tiles (square)
TILESX = 8              # Number of tiles across the X
TILESY = 6               # Number of tiles across the y
WINMARG = TILESIZE/3      # The margin around the tiles
PWIDTH=TILESIZE/2.5     # Pipe width. Pipes and balls are based on this size
WHSIZE=TILESIZE*0.9     # Size of a wheel
BALLSIZE=PWIDTH*0.7

# Define the top bar
TOPMARG=WINMARG/2       # Use a smaller margin, screen down will go TOPMARG, TOPBAR, TOPMARG
TOPBAR=BALLSIZE+8       # Allow display for a ball, and a border

# Ball speed, rot steps and FPS control how fast the game flows. If you make the tiles smaller, you may
# want to drop FPS or slow down the ball, as it will still cover the same amount of pixels as a larger tile
BALLSPEED=3             # Number of pixels to move per cycle
ROTSTEPS=10             # Number of steps to rotate the wheel in
FPS = 120               # Game frames per second
EXPTIME = 200           # ms for the explosion to appear and the ball finally die
BALL_LIMIT = -1          # -1 for infinite balls. May set a limit for testing or an extra challenge
ballCount = 0           # Track the number of balls released

# Explosion details
EXP_PREFIX=os.path.join("sprites","expl_03_00")
EXP_SUFFIX=".png"
EXP_NO=23
EXP_INTERVAL=EXPTIME/EXP_NO

# Global game counters
NUM_WHEELS=0        # Count of the number of wheels
BLOWN_WHEELS=0      # Count the number of wheels blown

# Colours
BG=(0,0,64)
# Theme - General UI colours in here
THEME = {
    "bg":(0,0,64),
    "main":(184, 115, 51),
    "dark":(81, 59, 28),
    "light":(230, 191, 131),
    "font":(236, 229, 182)
}

fontName='freesansbold'    # This should be a generic font on all systems
# Fonts defined below classes

LINECOL=(200,200,200)
LINEWIDTH=2
# Ball colours
BALLCOLS = {
    "R":(255,0,0),
    "G":(0,255,0),
    "B":(0,0,255),
    "Y":(255,255,0)
}
ICONBOR=3                   # Number of pixels wide for icon border
INFOPBOR=4                  # Size of info panel border

# List structure of what tiles have open, used to decide if a ball can flow
openEnds={
    "N":["V","NEL","NWL","W"],
    "E":["H", "ST", "NEL", "SEL", "W"],
    "S":["V", "SEL", "SWL", "W"],
    "W":["H", "ST", "NWL", "SWL", "W"]
}

# Claculate the window size
WIDTH=(TILESIZE*TILESX)+(WINMARG*2)
HEIGHT=(TILESIZE*TILESY)+(WINMARG*2)+TOPBAR
origin=(WINMARG, WINMARG+TOPBAR)
paused=False
nextCol="R"
showInfoPan=False

# Default level name
levelFile=os.path.join("levels","level1.csv")
# Process command line arguments
# Basic - If a second argument is supplied, assume this is the path to a level file
if(len(sys.argv)>1):
    levelFile=sys.argv[1]



# Start pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bamclone")
# Init fonts
pygame.font.init()
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()

# Load in images
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
blownIcon = pygame.image.load(os.path.join('sprites','blownCoin.png')).convert_alpha()
blownIcon = pygame.transform.scale(blownIcon, (WHSIZE/8,WHSIZE/8))
nextBallIcon = pygame.Surface((TOPBAR,TOPBAR))

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
        self.rect.x=origin[0]+TILESIZE*TILESX
        self.rect.centery=origin[1]+TILESIZE/2
        self.hitMiddle=False    # Track if we have been in the middle of the tile yet
        self.msg=""             # A persistant message which can be set, useful for debugging. Will print if changed on update
        self.exploState=-1         # < 0 if we are not exploding
        self.nextExplo=0        # What time do we change the explode graphic?
        
    def update(self):
        if(paused):
            return
        if(self.exploState>=0):
            self.explode()
        elif(self.wheel==-1):
            msg=""  # Blank debugging message if needed
            # What tile coord are we in, and what tile type is it?
            xtile=math.floor((self.rect.centerx-origin[0])/TILESIZE)
            # Special case on launch as the ball is off the board
            if(xtile>=TILESX):
                self.rect.x-=BALLSPEED
                return
            
            ytile=math.floor((self.rect.centery-origin[1])/TILESIZE)
            # Create tuple as useful index
            tileTup=(xtile, ytile)
            if(tileTup!=self.myTile):
                #print("I'm on a new tile")
                self.hitMiddle=False
                self.myTile=tileTup
            tiletype=levelData[ytile][xtile]
            #msg="Tile coord ({},{}), type {}".format(xtile,ytile, tiletype)
            # Calculate position within the tile
            xpos=self.rect.centerx-origin[0]-TILESIZE*xtile
            ypos=self.rect.centery-origin[1]-TILESIZE*ytile

            # Are we over a wheel?
            if(tiletype=="W"):
                #msg="On a wheel, with direction going "+self.direction
                point=opposite[self.direction]
                whid=(xtile,ytile)
                whdoc=wheels[whid].dockingpos[point]
                # Dock if we have passed the docking location in x or y, but if we are over half way
                # then we are being released and should not immediately doc
                if(self.direction=="S" and ypos>whdoc[1] and ypos<TILESIZE/2):
                    # Dock to the north
                    self.dock(whid, point)
                elif(self.direction=="N" and ypos<whdoc[1] and ypos>TILESIZE/2):
                    # Dock to the south
                    self.dock(whid, point)
                elif(self.direction=="E" and xpos>whdoc[0] and xpos<TILESIZE/2):
                    # Dock to the west
                    self.dock(whid, point)
                elif(self.direction=="W" and xpos<whdoc[0] and xpos>TILESIZE/2):
                    # Dock to the East
                    self.dock(whid, point)
            else:
                #msg="Not on a wheel"
                bounce=False
                atEdge=False
                # Are we at the tile edge?
                if(self.direction=="W" and (xpos-BALLSIZE/2)<BALLSPEED):
                    atEdge=True  
                elif(self.direction=="E" and (xpos+BALLSIZE/2)>TILESIZE):
                    atEdge=True
                elif(self.direction=="S" and (ypos+BALLSIZE/2)>TILESIZE):
                    atEdge=True
                elif(self.direction=="N" and (ypos-BALLSIZE/2)<BALLSPEED):
                    atEdge=True
                if(atEdge):
                    nextTile=findNextTile((xtile,ytile), self.direction)
                    if(nextTile==None or not isEndOpen(nextTile["type"], opposite[self.direction])):
                        bounce=True
                if(bounce):
                    self.direction=opposite[self.direction]
                    self.hitMiddle=False
                        

                # Are we at the tile middle?
                if(self.hitMiddle==False):
                    # Track with hitMiddle, we don't want this executing multiple times. That could be detected.
                    # If the ball is not moving at 1px per time it may never hit the middle exactly.
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
        #print("Docking ", point)
        self.direction=point
        self.wheel=whid
        coord=wheels[whid].dockBall(self, point)
        self.setCoord(coord, point)
        if(self.newBall):
            # This was a new ball, the top ally is now clear
            self.newBall=False
            launchNext()

    def setCoord(self, coord, docPoint):
        # Set the coordinate or the ball.
        # Coord received will be center coords relative to the current tile
        # docPoint will be the point of the wheel for a docked ball
        self.rect.centerx=coord[0]+origin[0]+self.myTile[0]*TILESIZE
        self.rect.centery=coord[1]+origin[1]+self.myTile[1]*TILESIZE
        if(docPoint!=None):
            self.direction=docPoint

    def handleEvent(self,event):
        if(paused):
            return
        if(self.rect.collidepoint(event.pos)):
            #print("I was clicked ", self.colour)
            if(self.wheel!=-1):
                #print("  and I was docked in wheel {} point {}, lets go".format(self.wheel, self.direction))
                # Check if I can launch in this direction
                if(wheels[self.wheel].checkExit(self.direction)):
                    # Yes, all clear
                    wheels[self.wheel].undock(self.direction)
                    # Remove from wheel
                    self.wheel=-1
                # else:
                #     print("No valid exit that way....")
    # End of handle event

    def explode(self):
        # Start the explosion in motion or continue the explosion
        if(self.exploState==-1):
            # Explosion not started
            self.exploState=EXP_NO
            self.nextExplo=0
        elif(self.exploState==0):
            # Explosion effect finished
            # If we are docked, undock
            if(self.wheel!=-1):
                wheels[self.wheel].undock(self.direction)
            # And remove
            self.kill()
        else:
            # Continue explosion
            ctime=pygame.time.get_ticks()
            if(ctime>self.nextExplo):
                # This is the next explosion step
                # Change the image
                cx=self.rect.centerx
                cy=self.rect.centery
                self.image=explosion[self.exploState-1]
                self.rect=self.image.get_rect()
                # Centre the image
                self.rect.centerx=cx
                self.rect.centery=cy
                # Update the timer
                self.nextExplo=ctime+EXP_INTERVAL
                # Drop the explosion counter
                self.exploState-=1

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
        self.rect.centerx=origin[0]+TILESIZE*id[0]+TILESIZE/2
        self.rect.centery=origin[1]+TILESIZE*id[1]+TILESIZE/2
        self.rotlimit=math.pi/2         # 90 degrees in radians
        self.rotdelta=self.rotlimit/ROTSTEPS

        # Determine which exits are valid and do not allow ball launch if not
        # i.e. a wheel that goes to a southT or nowhere
        self.validExit={"N":False,"E":False,"S":False,"W":False}
        for d in self.validExit:
            # print("  Wheel: Checking ", d)
            nextTile=findNextTile(id, d)
            #print(nextTile)
            # If the end open?
            if(nextTile!=None):
                o=opposite[d]
                if(nextTile["type"] in openEnds[o]):
                    # Yes, exit is valid
                    self.validExit[d]=True
                    #print("    Valid exit in direction ", d)
    # End of init
 
    def update(self):
        if(paused):
            return
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
            self.docked["N"].setCoord(self.dockingpos["N"], "N")

        if(self.docked["E"]==None):
            pygame.draw.circle(img, pygame.SRCALPHA, self.dockingpos["E"], self.ballrad)
        else:
            self.docked["E"].setCoord(self.dockingpos["E"], "E")

        if(self.docked["S"]==None):
            pygame.draw.circle(img, pygame.SRCALPHA, self.dockingpos["S"], self.ballrad)
        else:
            self.docked["S"].setCoord(self.dockingpos["S"], "S")

        if(self.docked["W"]==None):
            pygame.draw.circle(img, pygame.SRCALPHA, self.dockingpos["W"], self.ballrad)
        else:
            self.docked["W"].setCoord(self.dockingpos["W"], "W")
        if(self.blown):
            r=img.get_rect()
            b=blownIcon.get_rect()
            img.blit(blownIcon,(r.centerx-b.width/2,r.centery-b.height/2))
        return img

    def handleEvent(self,event):
        if(paused):
            return
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
        global BLOWN_WHEELS
        # Is there already another ball docked here?
        if(self.docked[point]!=None):
            # Yes, explode both
            self.docked[point].explode()
            ball.explode()
            self.numDocked-=1
        else:
            self.docked[point]=ball
            self.numDocked+=1
        # Are we full?
        if(self.numDocked==4):
            # Yes
            # What colour is north?
            c=self.docked["N"].colour
            sameCol=True
            for p in self.docked:
                # Is this the same colour? (North obviously will be)
                if(self.docked[p].colour!=c):
                    sameCol=False
            if(sameCol==True):
                # All the same colour, explode
                for p in self.docked:
                    self.docked[p].explode()
                    # Has this already been blown?
                    if(self.blown==False):
                        self.blown=True
                        BLOWN_WHEELS+=1
                        # Game over is tracked in main game loop

        return self.dockingOrig[point]
    
    def checkExit(self, point):
        # Does this point contain a valid exit from the wheel?
        return self.validExit[point]
    
    def undock(self, point):
        # Ball has been launched, drop reference to it
        self.docked[point]=None
        self.image=self.imageGen()
        self.numDocked-=1

    def setInvalid(self, point):
        # Mark an exit point as invalid
        #print("Setting point {} on wheel {} as invalid".format(point, self.id))
        self.validExit[point]=False

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
            #print("Inspecting tile at {},{}".format(tilex, tiley))
            type=levelData[tiley][tilex]
            # Find the exit
            exit=None
            if(type=="ST"):
                # Special case, first tile, we should never encounter another one
                exit="S"
            else:
                # All tiles should have one entry and one exit. Build list of the open ends of types
                myOpen=listOpenEnds(type)

                # for e in ["N", "E", "S", "W"]:
                #     if(type in openEnds[e]):
                #         myOpen.append(e)
                l=len(myOpen)
                if(l==0):
                    errorQuit("Problem. SouthT leads to a dead end. This is not a valid level")
                    break
                elif(l!=2):
                    errorQuit("Problem, we found the wrong number of open ends {}".format(myOpen))
                    foundWheel=2
                    break
                # Which end do we look at?
                if(myOpen[0]==entrydir):
                    # We have entered from this end
                    exit=myOpen[1]
                else:
                    # We have entered from the other end
                    exit=myOpen[0]

            nextTile=findNextTile((tilex,tiley), exit)
            # print("Next tile is {}".format(nextTile))
            # Have we exceeded limits?
            if(nextTile==None):
                foundWheel=2
                errorQuit("Error, ST path took us off screen")
            else:
                # What direction do we enter the tile from?
                entrydir=opposite[exit]
                # Looks good, is the next tile a wheel?
                if(nextTile["type"]=="W"):   
                    # Yes
                    foundWheel=1
                    #print("Found a wheel")
                else:
                    # No, loop
                    tilex=nextTile["coord"][0]
                    tiley=nextTile["coord"][1]
            if(stepCount>(TILESX*TILESY)):
                foundWheel=2
                errorQuit("Error: Unable to find wheel, infinite loop from tile {}".format(self.id))
            else:
                stepCount+=1       
        # End of wheel while loop
        self.linkedWheel=nextTile["coord"]
        #print("Linked southT {} to wheel {} entry point {}".format(self.id, self.linkedWheel, entrydir))
        self.wheelLoc=entrydir
        wheels[self.linkedWheel].setInvalid(entrydir)
        #print("  Wheel found, linking ST to wheel {}, docking point {}".format(self.linkedWheel, self.wheelLoc))
    # End of init

    def isOpen(self):
        # Return if the path is open
        return wheels[self.linkedWheel].slotEmpty(self.wheelLoc)

# End of southT class

class pauseButton(pygame.sprite.Sprite):
    # Small class to implement the pause button
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image=ctrlIcons["pause"]
        self.rect=self.image.get_rect()
        self.rect.x=WIDTH-WINMARG-TOPBAR*2.5
        self.rect.y=WINMARG/2

    def update(self):
        None

    def handleEvent(self, event):
        global paused
        if(self.rect.collidepoint(event.pos)):
            self.pause()
    
    def pause(self):
        global paused, showInfoPan, infPan
        print("Pause/play clicked?")
        paused=not paused
        if(paused):
            self.image=ctrlIcons["play"]
            infPan.setMsg("Paused")
            showInfoPan=True
        else:
            self.image=ctrlIcons["pause"]
            infPan.setMsg("")
            showInfoPan=False
# End of pauseButton class

class infoPanel():
    # An information pop-up panel
    def __init__(self):
        self.msg=""         # Text to display
        self.size=(WIDTH-WINMARG*4, HEIGHT/4)
        # Make the default background
        self.bg=pygame.Surface(self.size)
        self.bg.fill(THEME["main"])
        pygame.draw.rect(self.bg, THEME["dark"], self.bg.get_rect(), INFOPBOR)
        self.genImage()

    def genImage(self):
        # Generate the image. Copy the background
        self.image=self.bg.copy()
        self.rect=self.image.get_rect()
        # Center on screen
        self.rect.center=(WIDTH/2, HEIGHT/2)
        if(self.msg!=""):
            print("msg=", self.msg)
            textSurf=outlineText(self.msg, fonts["infop"], THEME["font"], THEME["dark"], 4)
            trect=textSurf.get_rect(center=(self.rect.width/2,self.rect.height/2))
            print(self.rect.width)
            print(trect.center)
            self.image.blit(textSurf, trect)

    def setMsg(self,msg):
        # Allows the main program to set the message
        self.msg=msg
        self.genImage()

# End of infoPanel class

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
            screen.blit(img, (origin[0]+TILESIZE*x, origin[1]+TILESIZE*y))
            x+=1
        y+=1
    
    # Draw the top info bar
    # This line just to test where it is
    #pygame.draw.rect(screen, (255,0,0), [(WINMARG, WINMARG/2),(TILESIZE*TILESX, TOPBAR)])
    # nextBall icon
    screen.blit(nextBallIcon, (WIDTH-TOPBAR-WINMARG, WINMARG/2))
    #screen.blit(ctrlIcons["pause"], (WIDTH-WINMARG-TOPBAR*2.5, WINMARG/2))

    all_sprites.draw(screen)
    # Cover up balls entering the screen
    pygame.draw.rect(screen, BG, [(origin[0]+TILESIZE*TILESX, origin[1]),(WINMARG,TILESIZE)])

    # Do we display the infoPanel?
    if(showInfoPan):
        screen.blit(infPan.image, infPan.rect)
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

def genNextBallIcon(c):
    # Generate the next ball icon
    global nextBallIcon
    tsurf=genIcon((TOPBAR,TOPBAR))
    pos=(TOPBAR/2-BALLSIZE/2, TOPBAR/2-BALLSIZE/2)
    tsurf.blit(ballImage[c],pos)
    nextBallIcon=tsurf

def genIcon(size):
    # Generate an icon blank of the supplied size
    tile=pygame.Surface((size))
    w=size[0]
    h=size[1]
    tile.fill(THEME["main"])
    for i in range(0,ICONBOR):
        # Dark border bottom and right
        pygame.draw.line(tile, THEME["dark"], (i,h-i),(w,h-i))
        pygame.draw.line(tile, THEME["dark"], (w-i,i),(w-i,h))
        # Light border top and left
        pygame.draw.line(tile, THEME["light"], (0,i),(w-i,i))
        pygame.draw.line(tile, THEME["light"], (i,0),(i,h-i))
    return tile

def genControlIcons():
    # Generate various game control icons
    bgMaster=genIcon((TOPBAR,TOPBAR))
    marg=TOPBAR/5
    iconList={}
    # Make the pause icon
    picon=bgMaster.copy()
    pgap=(TOPBAR-marg*2)/3
    pygame.draw.rect(picon, THEME["dark"], [(marg,marg),(pgap, TOPBAR-marg*2)])
    pygame.draw.rect(picon, THEME["dark"], [(marg+pgap*2,marg),(pgap, TOPBAR-marg*2)])
    iconList["pause"]=picon

    # Make the play icon
    plicon=bgMaster.copy()
    pygame.draw.polygon(plicon, THEME["dark"], [(marg*1.5,marg), (TOPBAR-marg, TOPBAR/2), (marg*1.5, TOPBAR-marg)])
    iconList["play"]=plicon
    return iconList
            
def exploImages():
    # Loads in the explosion images
    imgList=[]
    for i in range(0,EXP_NO):
        imgFile=EXP_PREFIX+str(i+1).zfill(2)+EXP_SUFFIX
        #print("Get image ", imgFile)
        imgList.append(pygame.image.load(imgFile).convert_alpha())
        imgList[i] = pygame.transform.scale(imgList[i], (BALLSIZE*2,BALLSIZE*2))

    return imgList

def loadLevel(filename):
    # Loads the level from file
    global levelData,wheels,southTs, NUM_WHEELS
    levelData=[]
    #filename="level"+str(l)+".csv"
    print("Loading file", filename)
    lineCount=0
    with open(filename) as f:
        reader = csv.reader(f, delimiter=",")
        for row in reader:
            #print(row)
            l=len(row)
            if(l!=TILESX):
                errorQuit("Error: In level file {}, line {} contains {} tiles, not {}".format(filename, lineCount, l, TILESX))
            levelData.append(row)
            lineCount+=1
    # Check the number of lines loaded
    if(lineCount!=TILESY):
        errorQuit("Error: In level file {}, contains {} lines not {}".format(filename, lineCount, TILESY))
    
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
                NUM_WHEELS+=1
            x+=1
        y+=1
    # Look for southTs in the top ally. Did not do this above as we need to set the associated wheel
    # exits as invalid
    y=0
    x=0
    for tname in levelData[0]:
        coord=(x,y)
        if(tname=="ST"):
            southTs[coord]=SouthT(coord)
        x+=1

# End of loadLevel
        
def checkSTopen(tile):
    # Check if a tile is open to the south - is the associated wheel slot free?
    r=southTs[tile].isOpen()
    return r

def nextBall():
    # Pick a random colour for the next ball
    r=random.choice(list(BALLCOLS))
    #print("The next ball colour is ", r)
    genNextBallIcon(r)
    return r

def LotherEnd(type, entry):
    # Returns the exit direction for a corner based on the entry
    # String should be of the format 'xyL', check what the first two characters are
    if(type[0]==entry):
        r=type[1]
    else:
        r=type[0]
    return r

def errorQuit(msg):
    # Quit if we have an error
    print(msg)
    pygame.quit()
    exit(1)

def launchNext():
    # Launch the next ball and pick the one to come after
    global nextCol, ballCount
    if(ballCount>=BALL_LIMIT-1 and BALL_LIMIT!=-1):
        print("Ball limit reached")
    else:
        all_sprites.add(Ball(nextCol))
        nextCol=nextBall()
        ballCount+=1

def findNextTile(coord, dir):
    # Finds the next tile in a specified direction
    # Returns None if there are no tiles (i.e. screen edge)
    # or a dictionary of coord and type
    x=coord[0]
    y=coord[1]
    if(dir=="N"):
        y-=1
    elif(dir=="E"):
        x+=1
    elif(dir=="S"):
        y+=1
    elif(dir=="W"):
        x-=1
    # Check limits
    if(x<0 or y<0 or x==TILESX or y==TILESY):
        return None
    
    rtn={'coord':(x, y),
        'type': levelData[y][x]
    }
    return rtn
# End of nextTile

def isEndOpen(ttype, d):
    # True if the end is open, false if not, None if tile doesn't exist
    if(ttype==None):
        # Been called with a None value, may be because the next tile is out of range
        return None
    # Split tile type, to ignore colours on painters or blockers
    sp=ttype.split(".")
    if(sp[0] in openEnds[d]):
        return True
    # Drop through to false
    return False

def listOpenEnds(type):
    # Lists the ends open for a particular type of tile
   # print("Checking ends for type ", type)

    # Split tile type, to ignore colours on painters or blockers
    sp=type.split(".")
    r=[]                # Return array
    for e in ["N", "E", "S", "W"]:
        if(type in openEnds[e]):
            r.append(e)
    l=len(r)
    #print("  {} ends found - {}".format(l, r))
    if(type!="B"):
        if(l==0):
            errorQuit("Unknown tile type {}".format(type))
        elif(len(r)!=2):
            errorQuit("Problem, we found the wrong number of open ends {} for tile type {}".format(r, type))
    return r

# Draw a font with outline. Copied from
# https://stackoverflow.com/questions/54363047/how-to-draw-outline-on-the-fontpygame
_circle_cache = {}
def _circlepoints(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points

def outlineText(text, font, gfcolor=pygame.Color('dodgerblue'), ocolor=(255, 255, 255), opx=2):
    # Also from stack overflow. Uses above function to produce text with an outline
    textsurface = font.render(text, True, gfcolor).convert_alpha()
    w = textsurface.get_width() + 2 * opx
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, ocolor).convert_alpha(), (0, 0))

    for dx, dy in _circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf


# Explode test
def explodeTest():
    # Test explode function, explode all balls, except the one in the top ally
    for s in all_sprites:
        if(type(s).__name__=="Ball"):
            if(s.newBall==False):
                s.explode()    
# ************* End of functions / Start of main code ******************

# Load fonts
fonts={
    "infop":pygame.font.SysFont(fontName, 128)
}
# Generate images
wheelImage = genWheelImage()
ballImage = genBalls()
explosion = exploImages()
ctrlIcons = genControlIcons()

pButton = pauseButton()
all_sprites.add(pButton)

infPan=infoPanel()


loadLevel(levelFile)

# Main loop
drawGameScreen()
running = True
# Add a ball to get us started
nextCol=nextBall()
all_sprites.add(Ball(nextCol))
nextCol=nextBall()
endTime=-1
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
        elif event.key == pygame.K_e:
            explodeTest()
        elif event.key == pygame.K_p:
            pButton.pause()
    elif event.type == pygame.MOUSEBUTTONDOWN:
        # Button 3, right click. Did we click a wheel?
        if(event.button==3):
            #print("Right click")
            for w in wheels:
                wheels[w].handleEvent(event)
        elif(event.button==1):
            # Left click, did we click a ball?
            # print("Left click")
            for s in all_sprites:
                if(type(s).__name__=="Ball"):
                    s.handleEvent(event)
            pButton.handleEvent(event)
                

    
    # else:
    #     print("Unknown event", event.type)
    #     print(event)
    # Update sprites
    all_sprites.update()

    # Draw / render the scree
    drawGameScreen()

    # Check to see if all wheels are blown
    if(BLOWN_WHEELS==NUM_WHEELS):
        # Delay for a little to finish the ball explode annimation
        if(endTime==-1):
            endTime=pygame.time.get_ticks()+EXPTIME+300
        if(pygame.time.get_ticks()>endTime):
            print("*** Level complete, well done! ***")
            running=False
# End of main loop
print("Game over")

pygame.quit()