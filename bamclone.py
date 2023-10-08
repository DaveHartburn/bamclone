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
WINMARG = TILESIZE//3      # The margin around the tiles
PWIDTH=TILESIZE//2.5     # Pipe width. Pipes and balls are based on this size
WHSIZE=TILESIZE*0.9     # Size of a wheel
BALLSIZE=math.floor(PWIDTH*0.7)

# Define the top bar
TOPMARG=WINMARG//2       # Use a smaller margin, screen down will go TOPMARG, TOPBAR, TOPMARG
TOPBAR=BALLSIZE+8       # Allow display for a ball, and a border

# Ball speed, rot steps and FPS control how fast the game flows. If you make the tiles smaller, you may
# want to drop FPS or slow down the ball, as it will still cover the same amount of pixels as a larger tile
BALLSPEED=3             # Number of pixels to move per cycle
ROTSTEPS=10             # Number of steps to rotate the wheel in
FPS = 120               # Game frames per second
EXPTIME = 200           # ms for the explosion to appear and the ball finally die
BALL_LIMIT = -1          # -1 for infinite balls. May set a limit for testing or an extra challenge
ballCount = 0           # Track the number of balls released

LEVEL_TIME = 120         # Default number of seconds for the level
LEVEL_LIST_FILE = os.path.join("levels", "levelList")

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
bxmarg=40           # Button border margin
bymarg=30
brad=20             # Button corner radius

# Ball colours
BALLCOLS = {
    "R":(255,0,0),
    "G":(0,255,0),
    "B":(0,0,255),
    "Y":(255,255,0)
}
ICONBOR=3                   # Number of pixels wide for icon border
INFOPBOR=4                  # Size of info panel border
TIMEBARBOR=12               # Margin for timer slider

# List structure of what tiles have open, used to decide if a ball can flow
openEnds={
    "N":["V","NEL","NWL","W", "BV", "PV"],
    "E":["H", "ST", "NEL", "SEL", "W", "BH", "PH"],
    "S":["V", "SEL", "SWL", "W", "BV", "PV"],
    "W":["H", "ST", "NWL", "SWL", "W", "BH", "PH"]
}

# Claculate the window size
WIDTH=(TILESIZE*TILESX)+(WINMARG*2)
HEIGHT=(TILESIZE*TILESY)+(WINMARG*2)+TOPBAR
#print(WIDTH,HEIGHT)
origin=(WINMARG, WINMARG+TOPBAR)
paused=False
nextCol="R"
showInfoPan=False

# Set up level data
# Default level name

# levelFile=os.path.join("levels","level1.csv")
# Process command line arguments
# Basic - If a second argument is supplied, assume this is the path to a level file
if(len(sys.argv)>1):
    # File supplied on command line, game is only single level
    levelList=[sys.argv[1]]
    curLevel=0
    maxLevels=1
else:
    # Load the level list
    curLevel=0          # Current level
    maxLevels=0 
    levelList=[]      
    with open(LEVEL_LIST_FILE, "r") as f:
        for l in f:
            levelList.append(os.path.join("levels", l.rstrip('\n')))
            maxLevels+=1
    #print(levelList)



# Start pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Bamclone")
# Init fonts
pygame.font.init()
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()

# Load in images
tImg = tileImages(TILESIZE, PWIDTH, BALLCOLS)

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

# Set up sounds
soundDir="sounds"
sounds={
    "woosh":pygame.mixer.Sound(os.path.join(soundDir, "punch-2-166695.mp3")),
    "dock":pygame.mixer.Sound(os.path.join(soundDir, "clank1-91862.mp3")),
    "explode":pygame.mixer.Sound(os.path.join(soundDir, "impact-152508.mp3")),
    "launch":pygame.mixer.Sound(os.path.join(soundDir, "sci-fi-glitch-sound-105730.wav")),
    "success":pygame.mixer.Sound(os.path.join(soundDir, "game-start-6104.wav")),
    "fail":pygame.mixer.Sound(os.path.join(soundDir, "failure-drum-sound-effect-2-7184.wav"))
}

# Create structure for the timer
ts = {
    "startTime":0,        # Time clock starts
    "endTime":0,          # Game over time
    "levelTime":LEVEL_TIME*1000,    # How long the level has
    "timeLeft":0,         # Remaining time
    "timerMask":(0,0,0,0),     # The size of the mask over the timer bar, calculated as a rect
    "nextUpdate":0,        # We don't update timers and do calculations every cycle of the loop as this is very frequent 
    "pauseStart":0         # Used to adjust time when the game is paused
}

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
                        elif(tiletype.startswith("PH") or tiletype.startswith("PV")):
                            # Painter, change the colour of the ball
                            self.changeColour(tiletype[3])
                        elif(tiletype.startswith("BH") or tiletype.startswith("BV")):
                            # Blocker, do we allow through or bounce?
                            blcol=tiletype.split(".")[1]
                            if(self.colour!=blcol):
                                self.direction=opposite[self.direction]
                                
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
                    sounds["launch"].play()
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

    def changeColour(self, c):
        # Change the ball to this colour
        self.colour=c
        self.image=ballImage[c]
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
                #if(nextTile["type"] in openEnds[o]):
                if(isEndOpen(nextTile["type"], o)):
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
            sounds["woosh"].play()

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
            sounds["explode"].play()
        else:
            self.docked[point]=ball
            self.numDocked+=1
            sounds["dock"].play()
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
                sounds["explode"].play()
                for p in self.docked:
                    self.docked[p].explode()
                    # Has this already been blown?
                    if(self.blown==False):
                        self.blown=True
                        BLOWN_WHEELS+=1
                        #print("BLOWN WHEELS=", BLOWN_WHEELS)
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
        global paused, showInfoPan, infPan, ts
        # print("Pause/play clicked?")
        paused=not paused
        if(paused):
            self.image=ctrlIcons["play"]
            infPan.setMsg("Paused")
            showInfoPan=True
            # Record start of pause
            ts["pauseStart"]=pygame.time.get_ticks()
        else:
            self.image=ctrlIcons["pause"]
            infPan.setMsg("")
            showInfoPan=False
            # Adjust level timer by adding the paused time to the start and end variables
            pt=pygame.time.get_ticks()-ts["pauseStart"]
            ts["startTime"]+=pt
            ts["endTime"]+=pt

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
        # Set the font
        if(len(self.msg)>12):
            font=fonts["infop_m"]
        else:
            font=fonts["infop"]
        if(self.msg!=""):
            textSurf=outlineText(self.msg, font, THEME["font"], THEME["dark"], 4)
            trect=textSurf.get_rect(center=(self.rect.width/2,self.rect.height/2))
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

    # Draw the timer bar
    screen.blit(timerBar, (WINMARG, WINMARG/2))
    # Mask out the elapsed time
    pygame.draw.rect(screen,BG,ts["timerMask"])

    # Do we display the infoPanel?
    if(showInfoPan):
        screen.blit(infPan.image, infPan.rect)
    pygame.display.flip()
# End of drawGameScreen()

def drawLobbyScreen():
    # Blits lobby components to the screen
    global lobScreen
    screen.blit(lobScreen["main"],(0,0))
    screen.blit(lobScreen["levelSel"], lobScreen["levelSel_rect"])
    pygame.display.flip()

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
            
def genTimerBar():
    # Generates the countdown timer bar
    # Calculate dimensions
    global timerBar, timerSlider
    marg=TOPBAR/5
    timerBar=(TILESIZE*TILESX-WINMARG-TOPBAR*2-marg, TOPBAR)
    b=TIMEBARBOR
    timerSlider=((b,b),(timerBar[0]-b*2,TOPBAR-b*2))
    img=genIcon(timerBar)

    # Generate the slider image as a transition of red, amber, green (with more green)
    simg=pygame.Surface((4,1))
    pygame.draw.line(simg, (200,0,0),(0,0),(0,0))
    pygame.draw.line(simg, (200,190,0),(1,0),(1,0))
    pygame.draw.line(simg, (0,200,0), (2,0),(3,0))
    # Stretch it
    simg = pygame.transform.smoothscale(simg, (timerSlider[1]))
    #pygame.draw.rect(img, (255,0,0), [(b,b),timerSlider])
    img.blit(simg, timerSlider[0])
    return img
# End of genTimerBar


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
    #print("Loading file", filename)
    lineCount=0
    with open(filename) as f:
        reader = csv.reader(f, skipinitialspace=True, delimiter=",")
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

def updateTimer():
    # Update the game timer if the game is not paused
    if(not paused):
        global ts,timerSlider
        t=pygame.time.get_ticks()
        if(t>ts["nextUpdate"]):
            ts["nextUpdate"]=t+100         # Update the timer every thenth of a second
            ts["timeLeft"]=ts["endTime"]-t
            # Calculate the size of the timer bar mask
            f=1-ts["timeLeft"]/ts["levelTime"]        # Fraction of time left
            # Calculate the length the bar should be
            l=math.floor((timerSlider[1][0]-timerSlider[0][0])*f)
            # Work out size of the mask over the timer
            ts["timerMask"]=(timerSlider[0][0]+WINMARG+timerSlider[1][0]-l,timerSlider[0][1]+WINMARG/2,l,timerSlider[1][1])
            #print(ts["timerMask"])
# End of updateTimer

def lobby():
    # Show a lobby/title screen
    global curLevel, lobScreen

    leaveLobby=0        # 0=stay,1=start,2=quit
    while leaveLobby==0:
        # Lobby handling loop
        clock.tick(FPS)

        event = pygame.event.poll()
        if event.type == pygame.QUIT:
            leaveLobby=2
        elif event.type == pygame.MOUSEBUTTONDOWN:
            #print("Click")
            # Have any icons been clicked?
            if(lobScreen["start_rect"].collidepoint(event.pos)):
                #print("Start clicked")
                leaveLobby=1
            elif(lobScreen["quit_rect"].collidepoint(event.pos)):
                #print("Quit clicked")
                leaveLobby=2
            elif(lobScreen["levelSel_rect"].collidepoint(event.pos)):
                # Level selection, change level counter
                if(event.button==1):
                    # Left, increase
                    curLevel+=1
                    if(curLevel>=maxLevels-1):
                        curLevel=maxLevels-1
                if(event.button==3):
                    # Right button clicked
                    curLevel-=1
                    if(curLevel<0):
                        curLevel=0
                # Regenerate icon
                (lobScreen["levelSel"],junkVar)=genLevelSel(bxmarg, bymarg, brad)

        drawLobbyScreen()
    # What did we exit with
    if(leaveLobby==2):
        print("Quitting")
        pygame.quit()
        quit()
# End of the lobby loop

def genLobbyScreen():
    # Generates components used for the lobby screen

    lobStruct={}

    msurf=pygame.Surface((WIDTH, HEIGHT))         # Main surface
    msurf.fill(THEME["bg"])
    pygame.draw.rect(msurf, THEME["main"], (WINMARG,WINMARG,WIDTH-WINMARG*2,HEIGHT-WINMARG*2))
    title=outlineText("BamClone",fonts["infop"],THEME["font"], THEME["dark"], 4)
    trect=title.get_rect()
    trect.center=(WIDTH/2,trect.height)
    msurf.blit(title,trect)
    lobStruct["main"]=msurf

    # Start game button
    ssurf=outlineText("Start game",fonts["infop_m"],THEME["font"], THEME["dark"], 4)
    srect=ssurf.get_rect()
    srect.center=(WIDTH/2,HEIGHT-WINMARG-300)
    msurf.blit(ssurf,srect)
    # Add an outline
    srect=srect.inflate(bxmarg, bymarg)
    pygame.draw.rect(msurf, THEME["dark"], srect, 4, border_radius=brad)    
    lobStruct["start_rect"]=srect       # Need record of dimensions for mouse detection

    # Make quit button
    qsurf=outlineText("Quit",fonts["infop_m"],THEME["font"], THEME["dark"], 4)
    qrect=qsurf.get_rect()
    qrect.center=(WIDTH/2,HEIGHT-WINMARG-150)
    msurf.blit(qsurf,qrect)
    # Add an outline
    qrect=qrect.inflate(bxmarg, bymarg)
    pygame.draw.rect(msurf, THEME["dark"], qrect, 4, border_radius=brad)
    lobStruct["quit_rect"]=qrect

    (lobStruct["levelSel"],lobStruct["levelSel_rect"])=genLevelSel(bxmarg, bymarg, brad)
    lobStruct["levelSel_rect"].center=(WIDTH/2,HEIGHT-WINMARG-450)
    #print(lobStruct["levelSel_rect"])
    return lobStruct
# End of genLobbyScreenS

def genLevelSel(bxmarg, bymarg, brad):
    # Generate a level select button. Dynamic, will change according to the selected level number
    global curLevel
    # Button surface
    btext="Level {:02d}".format(curLevel+1)
    ssurf=outlineText(btext,fonts["infop_m"],THEME["font"], THEME["dark"], 4)
    srect=ssurf.get_rect()
    #srect.center=((bxmarg+srect.width/2), (bymarg+srect.height)/2)

    # Add an outline
    srectbor=srect.inflate(bxmarg, bymarg)
    srectbor.center=(srectbor.width/2, srectbor.height/2)

    # Make surfae to paste it all to
    lsurf=pygame.Surface((srectbor.width, srectbor.height))
    lsurf.fill(THEME["main"])
    srect.center=(srectbor.width/2, srectbor.height/2)
    lsurf.blit(ssurf, srect)
    pygame.draw.rect(lsurf, THEME["dark"], srectbor, 4, border_radius=brad)   
    lrect=lsurf.get_rect()
    lrect.centery=(HEIGHT-WINMARG-400)
    return (lsurf, lrect)
# End of genLevelSel

    
# Explode test
def explodeTest():
    # Test explode function, explode all balls, except the one in the top ally
    for s in all_sprites:
        if(type(s).__name__=="Ball"):
            if(s.newBall==False):
                s.explode()    

def playLevel():
    # Main loop controlling playing an individual level
    global curLevel, levelList, all_sprites, ts, showInfoPan, BLOWN_WHEELS, NUM_WHEELS
    levelFile=levelList[curLevel]
    loadLevel(levelFile)

    #print("Starting level, NUM_WHEELS=", NUM_WHEELS)
    # Inital display
    drawGameScreen()

    # Add a ball to get us started
    nextCol=nextBall()
    all_sprites.add(Ball(nextCol))
    nextCol=nextBall()
    aTimer=-1          # Used for various timer purposes

    # Start the level timer
    ts["startTime"]=pygame.time.get_ticks()
    ts["endTime"]=ts["startTime"]+ts["levelTime"]

    # gameState:
    #   0 = running
    #   1 = finished, success
    #   2 = finished, failure/time out
    #   3 = user quit
    gameState=0
    sounds["launch"].play()
    while gameState==0:
        # Keep loop running at the right speed
        clock.tick(FPS)
        
        event = pygame.event.poll()
        if event.type == pygame.QUIT:
            gameState=3
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_ESCAPE:
                gameState=3
                print("Escape - quitting")
            elif event.key == pygame.K_e:
                explodeTest()
            elif event.key == pygame.K_w:
                # Test winning
                gameState=1
            elif event.key == pygame.K_f:
                # Test failure
                gameState=2
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

        # Update the game timer
        updateTimer()
        if(ts["timeLeft"]<=0):
            # Out of time
            gameState=2
        # Draw / render the scree
        drawGameScreen()

        # Check to see if all wheels are blown
        if(BLOWN_WHEELS==NUM_WHEELS):
            # Delay for a little to finish the ball explode annimation
            if(aTimer==-1):
                aTimer=pygame.time.get_ticks()+EXPTIME+300
            if(pygame.time.get_ticks()>aTimer):
                print("*** Level complete, well done! ***")
                gameState=1
    # End of level loop, process exit status
    moreLevels=False    # Assume we are done
    if(gameState==1):
        # Level completed successfully
        # Increase the level counter
        curLevel+=1

        # Have we played all levels?
        if(curLevel>=maxLevels):
            print("Game complete")
            infPan.setMsg("Game complete, score=9999")
        else:
            print("  Success!!!")
            infPan.setMsg("Success, score=9999")
            moreLevels=True # Keep playing
        showInfoPan=True
        drawGameScreen()
        sounds["success"].play()
        pygame.time.delay(3000)
        showInfoPan=False
    elif(gameState==2):
        infPan.setMsg("Out of time, score=9999")
        showInfoPan=True
        drawGameScreen()
        sounds["fail"].play()
        pygame.time.delay(3000)
        showInfoPan=False
    return moreLevels
# End of playLevel()

# ************* End of functions / Start of main code ******************

# Load fonts
fonts={
    "infop":pygame.font.SysFont(fontName, 128),
    "infop_m":pygame.font.SysFont(fontName, 96)
}

# Generate images
wheelImage = genWheelImage()
ballImage = genBalls()
explosion = exploImages()
ctrlIcons = genControlIcons()
timerBar = genTimerBar()

pButton = pauseButton()
all_sprites.add(pButton)

infPan=infoPanel()
lobScreen=genLobbyScreen()


# Main loop structure. An explicit quit is called on the lobby screen, so a while True is valid
while True:
    # Show lobby screen
    lobby()

    gameRunning=True
    while gameRunning:
        # Reset everything and load next level
        all_sprites = pygame.sprite.Group()
        BLOWN_WHEELS=0
        NUM_WHEELS=0
        gameRunning=playLevel()

# End of main loop

# We should never reach this line
pygame.quit()