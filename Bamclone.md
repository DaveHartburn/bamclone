Bamclone
========

Tiles and levels
================

Levels are defined in a CSV text file, which should be 8x6 (or match the defined level size). Each element contains a code for the type of tile it is. The top bar should always be a horizontal line with 'south Ts' dropping down to the game play parts.

The following codes are used:

- B       Blank
- H       Horizontal pipe
- V       Vertical pipe
- ST      South T - The shorter bit of the T points north
        - A south T should be the only one, for top entry bar. No other makes sense
- NEL     L with the corners pointing north and east
- SEL     L with the corners pointing south and east
- SWL     L south west
- NWL     L north west
- W       A wheel
- BH.c    A horizontal barrier tile of colour c (c=R|G|B|Y)
- BV.c    A vertical barrier tile of colour c
- PH.c    A horizontal painter tile of colour c
- PV.c    A vertical painter tile of colour c

In the levels directory, the files "levelList" is a simple list of level files in the order they should be played. Use this to construct the main game play. Supplying a level on the command line overrides this list and plays the game as a single level game.

Classes and functions
=====================

class Ball:
  __init__(self, col)
  update(self)
  dock(self, whid, point)   # Docks a ball in a wheel at point specified
  setCoord(self, coord, docPoint)   # Called from wheel, sets the coordinates and point of wheel docked
  handleEvent(self, event)          # Handle mouse clicks
  explode(self)                     # Start the explosion in motion or continue the explosion

class Wheel:
  __init__(self, id)
  update(self)
  imageGen(self)    # Generates it's image and sets the docking position of any docked balls
  handleEvent(self, event)        # Handle mouse clicks
  slotEmpty(self, d)      # Returns true or false, if there is a ball docked at point d
  dockBall(self, ball, point)   # Dock the ball and return coordinates for docking point
  checkExit(self, point)        # Does this point contain a valid exit from the wheel?
  undock(self, point)           # Ball has been launched, drop reference to it
  setInvalid(self, point)       # Mark an exit point as invalid

class SouthT():
  __init__(self, id)
  isOpen(self)        # Return if the path is open / wheel at the end is free


Global functions:
  drawGameScreen()        # Draws the main game screen
  genWheelImage()         # Creates the wheel image on startup
  genBalls()              # Generate the ball images on startup
  genNextBallIcon()       # Generate the icon to show the next ball
  genIcon(size)           # Generate an icon of the supplied size
  exploImages()           # Loads in the explosion images
  loadLevel(l)            # Load a level from file 'l'
  checkSTopen()           # Checks if a tile is open to the south - is the associated wheel slot free?
  nextBall()              # Pick a random colour for the next ball
  LotherEnd(type, entry)  # Returns the exit direction for a corner based on the entry
  errorQuit(msg)          # Quit if we have an error
  launchNext()            # Launch the next ball and pick the one to come after
  findNextTile(coord, dir)    # Finds the next tile in a specified direction
  isEndOpen(tile type)    # True if the end is open, false if not, None if tile doesn't exist
  explodeTest()           # Test explode function, explode all balls, except the one in the top ally

To Do
=====
- [X] Save to github
- [X] Implement wheel graphic and class
    - [X] Rotate on click
- [X] Drop on south T if wheel is open
-   [X] Implement southT class
-   [X] Link each south T to a wheel
    - [X] Use more complex level for fuller test
  - [X] Make sure it blocks when outlet has docked ball
- [X] Balls dock on open slot
- [X] Balls rotate with wheel
- [X] Rotating wheel opens south T again
- [X] Implement nextTile function and strip repeated code
- [X] Allow loading of other levels with a command line parameter (for testing)
- [X] Wheels 'blow' on all balls of the same colour
- [X] Game over, win on all blown
- [X] Launch balls from wheel
-   [X] Do not allow if there is an immediate dead end
- [X] Balls explode on collision (in wheel)
  - [X] Test explode keypress
- [X] Middle detection going north
- [X] Middle detection going south
- [X] Turn corners
- [X] Bouncing of north dead end
- [X] Bouncing of south dead end
- [X] Random new ball on docking 
- [X] Display new ball colour in advance
- [X] Level timer
- [ ] Level designer
- [X] Painter blocks
- [X] Barrier blocks
- [X] Sound effects
- [ ] More levels
- [ ] Score
- [X] Lobby screen
- [X] Progression
- [X] Game pause (on screen button)
- [ ] Different tile colours/textures
- [ ] Level intro message
- [X] Level/game over message
- [ ] Difficulty

Bugs
----
- Balls don't quit sit snug when docking, until rotated
- In testing one wheel didn't blow. Suspect a ball dropped as I turned that wheel and it became a 'ghost' somewhere
  - Or could be down to exploded balls not clearing the wheel

Check in notes
--------------
- Created a third level, dlevel3.csv
- Allowed space before an element in a level file, to make them a bit more readable.
- Changed the blank template to include the spaces
- Created levelList file
- Level progression, can play through a series of multiple levels