#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import os
import urwid
import youtube_client

class VideoButton(urwid.FlowWidget):
    def __init__(self, video, index):
        self.video = video
        self.index = urwid.Text(('index', str(index)))
        try:
            rounded_rating = str(round(float(self.video.rating), 1))
        except:
            rounded_rating = self.video.rating

        width = 30
        views = urwid.Text([('index', 'Views: '), self.video.views])
        rating = urwid.Text([('index', 'Rating: '), rounded_rating])
        author = urwid.Text([('index', 'Author: '), self.video.author, '\n'])
        button_info = urwid.Columns([('fixed', width, author), ('fixed', width, views), ('fixed', width, rating)])
        title = urwid.Text(self.video.title)
        button = urwid.Pile([title, button_info])

        index_width = int(len(str(index)) + 2)
        if index_width == 3:
            index_width += 1 # align the first 9 videos
        self.display_widget = urwid.Columns([('fixed', index_width, self.index), button])
        self.display_widget = urwid.AttrMap(self.display_widget, None, 'focus')
    def rows(self, size, focus=False):
        return self.display_widget.rows(size, focus)
    def render(self, size, focus=False):
        return self.display_widget.render(size, focus)
    def selectable(self):
        return True
    def keypress(self, size, key):
        if key == 'enter':
            self.display_widget.set_attr_map({None: 'downloaded'})
            status_bar.set_text('Downloading: ' + self.video.title)
            self.video.download()
        elif key == 'o':
            self.display_widget.set_attr_map({None: 'opened'})
            #self.button.set_focus_map({None: 'opened'})
            status_bar.set_text('Opening in browser: ' + self.video.title)
            self.video.open()
        elif key == 'p':
            status_bar.set_text('Playing: ' + self.video.title)
            self.video.play()
        elif key == 'a':
            status_bar.set_text(self.video.abort())
        else:
            return key

class CommandPrompt(urwid.Edit):
    def keypress(self, size, key):
        if key == 'enter' and not self.get_edit_text() == '':
            query = self.get_edit_text()
            self.set_edit_text('')
            status_bar.set_text('Searching for: ' + query)
            loop.draw_screen()
            search = client.search(query) # takes the most time
            listbox.append(search)
            status_bar.set_text(query)
            main_frame.set_focus('body')
        if key == 'ctrl x':
            main_frame.set_focus('body')
            self.set_caption('')
            self.set_edit_text('')
        else:
            return urwid.Edit.keypress(self, size, key)

class VideoListBox(urwid.WidgetWrap):
    def __init__(self):
        self.body = urwid.SimpleListWalker([])
        self.listbox = urwid.ListBox(self.body)
        urwid.WidgetWrap.__init__(self, self.listbox)
    def append(self, search):
        for video in search:
            new_button = VideoButton(video, int(len(self.body)) + 1)
            self.body.append(new_button)
            loop.draw_screen()
    def keypress(self, size, key):
        if key == ':':
            main_frame.set_focus('footer')
            command_prompt.set_caption(':')
        elif key == 'j':
            self.listbox.keypress(size, 'down')
        elif key == 'k':
            self.listbox.keypress(size, 'up')
        elif key == 'g':
            self.listbox.change_focus(size, 0)
        elif key == 'G':
            self.listbox.change_focus(size, len(self.body) - 1)
        elif key == 'ctrl d':
            position = self.listbox.get_focus()[1] + 5
            self.listbox.set_focus(position, 'above')
        elif key == 'ctrl u':
            position = self.listbox.get_focus()[1] - 5
            if position < 0:
                position = 0
            self.listbox.set_focus(position, 'below')
        elif key == 'ctrl r':
            status_bar.set_text('Cleared the screen.')
            self.body[:] = []
            main_frame.set_focus('footer')
        elif key == 'ctrl n':
            search = client.next_page()
            self.append(search)
        else:
            return self.listbox.keypress(size, key)

# change to .videotop directory
homepath = os.environ['HOME']
os.chdir(homepath + '/.videotop')

palette = [('focus', 'light red', 'black', 'standout'),
          ('status', 'white', 'dark blue'),
          ('opened', 'light blue', 'black'),
          ('downloaded', 'white', 'black'),
          ('index', 'dark cyan', 'black')]
listbox = VideoListBox()
command_prompt = CommandPrompt(':')
status_bar = urwid.Text('Press enter to search', align='left')
footer = urwid.Pile([urwid.AttrMap(status_bar, 'status'), command_prompt])
main_frame = urwid.Frame(listbox)
main_frame.set_footer(footer)
main_frame.set_focus('footer')
client = youtube_client.YouTubeClient()

def handle_input(input):
    if input in ('q', 'Q'):
        raise urwid.ExitMainLoop()
    if input == 'tab':
        if main_frame.focus_part == 'body':
            command_prompt.set_caption(':')
            main_frame.set_focus('footer')
        else:
            main_frame.set_focus('body')
    if input == 'm':
        video_list = os.listdir(os.getcwd())
        video_list = [os.path.splitext(video)[0] for video in video_list]
        videos = [client.get_local_video(video) for video in video_list]
        listbox.append(videos)

loop = urwid.MainLoop(main_frame, palette, unhandled_input=handle_input)
loop.run()
