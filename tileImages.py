# tileImages
# Used to create the tile images. These are generated on the fly rather than drawn, to give that retro feel
import pygame
import math

TILEBG=(160,160,120)
TILEBOR=6
TILESTUD=6             # Outer radius of the tile studs. 0 to remove

# Pipes
PIPEBORDER=3            # How wide
PBORCOL=(50,50,50)
PEDGECOL=(100,100,100)
PMIDCOL=(230,230,230)

class tileImages():

    def __init__(self, ts, pipew, cols):
        print("Starting tile generation")
        self.ts=ts          # Set the tile size
        self.pipew=pipew
        self.tileList={}    # Store the tiles
        # Generate the unknown tile
        self.tileList["UNK"]=self.unkTile()
        self.tileList["B"]=self.genBlank(TILEBG)
        self.pipes=self.genPipes()
        #print(self.pipes)

        # Create horizontal pipe
        img=pygame.Surface.copy(self.tileList["B"])
        img.blit(self.pipes["H"], (0,0))
        self.tileList["H"]=img

        # Create vertical pipe
        img=pygame.Surface.copy(self.tileList["B"])
        img.blit(self.pipes["V"], (0,0))
        self.tileList["V"]=img

        # Create North East L
        img=pygame.Surface.copy(self.tileList["B"])
        img.blit(self.pipes["C"], (0,0))
        self.tileList["NEL"]=img
        # Create North West L
        img=pygame.Surface.copy(self.tileList["B"])
        cnw=pygame.transform.flip(self.pipes["C"],True,False)
        img.blit(cnw, (0,0))
        self.tileList["NWL"]=img
        # Create South East L
        img=pygame.Surface.copy(self.tileList["B"])
        cse=pygame.transform.flip(self.pipes["C"],False, True)
        img.blit(cse, (0,0))
        self.tileList["SEL"]=img
        # Create South West L
        img=pygame.Surface.copy(self.tileList["B"])
        csw=pygame.transform.flip(self.pipes["C"],True,True)
        img.blit(csw, (0,0))
        self.tileList["SWL"]=img

        # Create South T
        img=pygame.Surface.copy(self.tileList["B"])
        img.blit(self.pipes["T"], (0,0))
        self.tileList["ST"]=img
        
        # Create W (a cross without the wheel)
        img=pygame.Surface.copy(self.tileList["B"])
        img.blit(self.pipes["W"], (0,0))
        self.tileList["W"]=img

        # Create painter blocks
        for c in cols:
            #print("Generating painter ", c)
            # Make alpha colour
            pc=cols[c]+(16, )
            #print(pc)
            img=pygame.Surface.copy(self.tileList["B"])
            pimg=pygame.Surface((ts,ts), pygame.SRCALPHA)
            pimg.set_alpha(128)
            pygame.draw.rect(pimg,cols[c],(TILEBOR,TILEBOR,ts-TILEBOR*2,ts-TILEBOR*2))
            img.blit(pimg,(0,0))
            vimg=img.copy()
            img.blit(self.pipes["H"], (0,0))
            vimg.blit(self.pipes["V"], (0,0))
            self.tileList["PH.{}".format(c)]=img
            self.tileList["PV.{}".format(c)]=vimg
        
        # Creater blockers
        for c in cols:
            img=pygame.Surface.copy(self.tileList["B"])
            himg=pygame.Surface.copy(self.tileList["B"])
            barimg=pygame.Surface((ts,ts), pygame.SRCALPHA)
            #barimg.set_alpha(128)
            w=ts/5          # Width of barrier
            p=ts-TILEBOR    # Number of points
            f=4             # Wave frequency
            a=5          # Wave amplitude
            hl=3        # Thickness of highlight
            for i in range(TILEBOR,p+1):
                j=i/p*2*math.pi
                y=(ts/2-w/2)+(a*math.cos(j*f))
                pygame.draw.rect(barimg,cols[c],(i,y,1,w))
                # Add highlights
                darkCol=self.colorInc(cols[c],-20)
                baseC=pygame.Color(cols[c])
                lightCol=baseC.lerp((255,255,255),0.5)
                pygame.draw.rect(barimg,lightCol,(i,y,1,hl))
                pygame.draw.rect(barimg,darkCol,(i,y+w-hl,1,hl))
            # Make a vertical stripe (to be applied to horizontal)
            horizbar=pygame.transform.rotate(barimg,90)
            # Create the vertical image
            img.blit(barimg,(0,0))
            img.blit(self.pipes["V"], (0,0))
            self.tileList["BV.{}".format(c)]=img
            # Create the horizontal image
            himg.blit(horizbar,(0,0))
            himg.blit(self.pipes["H"], (0,0))
            self.tileList["BH.{}".format(c)]=himg

    # End of init, and tile creation

    def unkTile(self):
        # An unknown tile, returned when we don't know what is being asked for
        tile=pygame.Surface((self.ts,self.ts))
        tile.fill((255,0,0))
        return tile
    
    def getTile(self, tname):
        # Return a tile by name
        if tname in self.tileList:
            return self.tileList[tname]
        else:
            #print("Unknown tile "+tname)
            return self.tileList["UNK"]
        
    def genBlank(self, bgcol):
        # Generate the blank tile, which is used as the background for the others
        # Colour supplied to make the painter tiles
        tile=pygame.Surface((self.ts, self.ts))
        tile.fill(bgcol)
        # Draw border
        darkCol=self.colorInc(bgcol, -20)
        lightCol=self.colorInc(bgcol, 20)
        vdarkCol=self.colorInc(bgcol, -40)

        for i in range(0,TILEBOR):
            # Dark border bottom and right
            pygame.draw.line(tile, darkCol, (i,self.ts-i),(self.ts,self.ts-i))
            pygame.draw.line(tile, darkCol, (self.ts-i,i),(self.ts-i,self.ts))
            # Light border top and left
            pygame.draw.line(tile, lightCol, (0,i),(self.ts-i,i))
            pygame.draw.line(tile, lightCol, (i,0),(i,self.ts-i))

        # Draw studs on it
        tileOff=TILESTUD*2.5
        studList=[(tileOff,tileOff), (self.ts-tileOff,tileOff), (self.ts-tileOff, self.ts-tileOff), (tileOff, self.ts-tileOff)]
        if(TILESTUD!=0):
            for coord in studList:
                # Outer circle very dark
                pygame.draw.circle(tile, vdarkCol, coord, TILESTUD)
                # Inner stud dark
                pygame.draw.circle(tile, darkCol, coord, TILESTUD-2)
                # Light colour to do a shine arc
                sx=coord[0]
                sy=coord[1]
                # Calculate the bounding rectangle
                rad=TILESTUD-4
                rect=[sx-rad, sy-rad, rad*2, rad*2]
                #pygame.draw.rect(tile,(0,255,0),rect)
                #
                pygame.draw.arc(tile, lightCol, rect,math.pi/2,math.pi,1)

        return tile
    
    def colorInc(self, col, p):
        # Increases a colour by p percent (can be negative)
        # Assumes the colour is a list of 3 integers
        newL=[0,0,0]    # Define the colour as a list first
        
        for i in range(0,3):
            n=col[i]*(1+p/100)
            # Ensure we are in the bounds
            n=min(255,n)
            n=max(0,n)
            newL[i]=n
        #print(col, newCol)
        return tuple(newL)
    
    def genPipes(self):
        # Generate a list of pipe components
        pipes={}
        # Create basic horizontal pipe
        psurf=pygame.Surface((self.ts,self.ts), pygame.SRCALPHA, 32)
        tilemid=(self.ts-self.pipew)/2
        pygame.draw.rect(psurf,PBORCOL,[0,tilemid,self.ts,self.pipew])

        # Create a horizontal pipe
        # Make small surfae then use smoothscale to produce gradient
        hpipe=pygame.Surface((1,3))
        pygame.draw.line(hpipe,PEDGECOL,(0,0),(0,0))
        pygame.draw.line(hpipe,PMIDCOL,(0,1),(0,1))
        pygame.draw.line(hpipe,PEDGECOL,(0,2),(0,2))
        # Stretch it
        hpipe = pygame.transform.smoothscale(hpipe, (self.ts, self.pipew-PIPEBORDER*2))
        # Add it to the horizontal tile
        psurf.blit(hpipe,(0,tilemid+PIPEBORDER))

        pipes["H"]=psurf
        pipes["V"]=pygame.transform.rotate(psurf, 90)

        # Create a mitre, used to contruct corners
        # Start with horizontal pipe and delete part of it
        mit=pygame.Surface.copy(psurf)
        pygame.draw.polygon(mit, pygame.SRCALPHA, [(0,0),(self.ts,0),(0,self.ts)])
        # Make a vertical one in the same way. Add a little so we don't get a gap
        adj=1      # Amount to adjust by
        hmit=pygame.Surface.copy(pipes["V"])
        pygame.draw.polygon(hmit, pygame.SRCALPHA, [(self.ts,self.ts),(self.ts,adj),(adj,self.ts)])

        # Create a north east corner
        cor=pygame.Surface((self.ts,self.ts), pygame.SRCALPHA, 32)
        cor.blit(mit,(0,0))
        cor.blit(hmit,(0,0))
        pipes["C"]=cor

        # Create a point, used to make Ts and crossroads (for wheel)
        pnt=pygame.transform.rotate(mit, -90)
        t=pygame.Surface((self.ts,self.ts), pygame.SRCALPHA, 32)
        pygame.draw.polygon(pnt, pygame.SRCALPHA, [(0,0),(self.ts,0),(0,self.ts)])
        t.blit(pipes["H"],(0,0))
        t.blit(pnt,(0,0))
        pipes["T"]=t
        
        # Wheel tile is based on a cross, the wheel part is added later as a sprite and object
        w=pygame.Surface.copy(t)
        pnts=pygame.transform.flip(pnt,False,True)
        w.blit(pnts,(0,0))
        pipes["W"]=w

        return pipes



# End of class tileImages