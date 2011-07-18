# WARNING
This program is still under heavy development!

# DESCRIPTION
**Videotop** is an open source command line browser for online videos, written in python with vim-like keybindings.

It uses the following external python modules:
 
* [urwid][1] to provide an ncurses frontend.
* [gdata][2] and [youtube-dl][3] to search for and download youtube videos.
* (optional) [mplayer][4] to play the downloaded videos.

[1]: http://excess.org/urwid/
[2]: http://code.google.com/apis/youtube/1.0/developers_guide_python.html
[3]: http://rg3.github.com/youtube-dl/
[4]: http://www.mplayerhq.hu/

# USAGE
If you are already familiar with vim the controls should be pretty intuitive.
There are two different modes: command mode and browse mode.
Press TAB to toggle between the two.

In command mode you can search for videos by hitting enter.
This will generate a list of videos and switch to browse mode.

In browse mode you can download the videos by hitting **ENTER** and play them by hitting **p**.
You can also open the youtube page by hitting **o**. To list more videos of your previous search hit **CTRL n** and to clear the video list hit **CTRL r**.
