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



To Do

- [ ] Save to github
- [X] Implement wheel graphic and class
    - [X] Rotate on click
- [X] Drop on south T if wheel is open
-   [X] Implement southT class
-   [X] Link each south T to a wheel
    - [ ] Use more complex level for fuller test
  - [ ] Make sure it blocks when outlet has docked ball
- [ ] Balls dock on open
    - [X] North
    - [ ] South
    - [ ] East
    - [ ] West
- [X] Balls rotate with wheel
- [X] Rotating wheel opens south T again
- [ ] Allow loading of other levels with a command line parameter (for testing)
- [ ] Wheels 'blow' on all balls of the same colour
- [ ] Launch balls from wheel
-   [ ] Do not allow if there is an immediate dead end
- [ ] Balls explode on collision (in wheel)
- [X] Middle detection going north
- [X] Middle detection going south
- [ ] Turn corners
- [ ] Bouncing of north dead end
- [ ] Bouncing of south dead end
- [X] Random new ball on docking 
- [ ] Display new ball colour in advance
- [ ] Level timer
- [ ] Level designer
- [ ] Painter blocks
- [ ] Barrier blocks
- [ ] Sound effects
- [ ] More levels
- [ ] Score
- [ ] Loading screen
- [ ] Progression
- [ ] Lives?