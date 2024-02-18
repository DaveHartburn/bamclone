# bamclone
A Pygame clone of the old Archimedes game, Bambuzle by Kuldip S Pardesi and published by Arxe Systems.

This was a very addictive little game, based on a few simple concepts, and apparently was quite similar to Log!cal on the Amiga. There doesn't seem to be a lot of information about this out there and only a 2 level demo seems to exist. I have an original copy, but the disk has an error and I have been unable to play it on either an emulator or the original hardware.

For development details, see bamclone.md

Installing
----------

 * Clone repository to a local directory
 * Install Python v3.x
 * Install pygame libraries
   * On Debian and related distributions, `sudo apt install python3-pygame`
   * Also try `pip3 install pygame`
 * Run by either calling './bambclone.py' on a linux system if execute permissions are set
   * or `python3 bamclone.py`

Playing
-------

To complete each level, each wheel must be filled with four balls of the same colour. When that happens, all balls will explode and a gold token appears in the centre of the wheel. If the time runs out, you lose. When all wheels are blown and contain a token, the level is won.

Balls enter the top shoot from the left and will drop into the first available slot in a wheel. Wheels can be turned with a right mouse click. Balls can be ejected from a slot in a wheel with a left mouse click.

If a ball lands in a slot already occupied by another ball, both balls explode, clearing that slot. However, balls may pass each other on the same chute en-route to another wheel, essentially swapping places. You may also rotate a wheel while a ball is incoming.

Some tiles contain a coloured barrier. Only balls of that colour may pass the barrier. All other balls will be bounced back.

Other tiles are coloured painter blocks. Any ball passing through this block will be painted to the new colour.

Version
-------
0.4
* Can now play through a series of levels
* Sound added
* Has a bug where a wheel in which balls have collided doesn't blow
* Score is fixed at 9999
0.3
* Now has level timeout, game is fully playable but a bit quiet
0.2
* Playable without timer
* Fixed game crash issue listed in 0.1
* Can load other levels with command line argument
  
0.1 
* Basic level is playable.
* No timer, i.e. no lose condition
* Level complete - quits with command line message
* One wheel has south going dead end. Game will crash if taken

Credits
=======

Author: Dave Hartburn
Original concept: Kuldip S Pardesi

Explosion images from OpenGameArt
https://opengameart.org/
https://opengameart.org/content/explosions-0
Author: chabull

All sound effects also from opengamearg.org
