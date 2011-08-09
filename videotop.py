#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import errno
import urwid
import youtube_client


class VideoButton(urwid.FlowWidget):
    clicked_buttons = []

    def __init__(self, video, index, color='index'):
        self.video = video
        self.index = index
        index = urwid.Text(('normal', ' ' + str(self.index) + '. '), align='right')
        try:
            rounded_rating = str(round(float(self.video.rating), 1))
        except:
            rounded_rating = self.video.rating

        youtube_username_max_len = 20
        duration = self.video.get_formatted_duration()
        views = self.video.get_formatted_views()
        views = urwid.Text([('normal', 'Views: '), ('bold', views)])
        rating = urwid.Text([('normal', 'Rating: '), ('bold', rounded_rating)])
        author = urwid.Text([('normal', 'Author: '), ('bold', self.video.author)])
        duration = urwid.Text([('normal', 'Duration: '), ('bold', duration)])
        published = urwid.Text([('normal', 'Published: '), ('bold', self.video.published)])
        button_info = urwid.Columns([('fixed', 20, views),
                                     ('fixed', 16, rating),
                                     ('fixed', 22, duration),
                                     ('fixed', 26, published),
                                     ('fixed', youtube_username_max_len + 8, author)])
        title = urwid.Text(self.video.title)
        self.empty_line = urwid.Text('')
        self.button = urwid.Pile([title, button_info, self.empty_line])

        index_width = 6
        self.display_widget = urwid.Columns([('fixed', index_width, index), self.button])
        self.display_widget = urwid.AttrMap(self.display_widget, color, 'focus')

    def rows(self, size, focus=False):
        return self.display_widget.rows(size, focus)

    def render(self, size, focus=False):
        return self.display_widget.render(size, focus)

    def selectable(self):
        return True

    def keypress(self, size, key):
        if key == 'enter':
            self.display_widget.set_attr_map({None: 'downloaded'})
            status_bar.set_text(' Downloading: "' + self.video.title + '"')
            self.video.download()
            VideoButton.clicked_buttons.append(self)
        elif key == 'o':
            self.display_widget.set_attr_map({None: 'opened'})
            status_bar.set_text(' Opening in browser: "' + self.video.title + '"')
            self.video.open()
        elif key == 'p':
            status_bar.set_text(' Playing: "' + self.video.title + '"')
            self.video.play()
        elif key == 'a':
            status_bar.set_text(' ' + self.video.abort())
        else:
            return key


class CommandPrompt(urwid.Edit):
    def clear(self):
        self.set_caption('')
        self.set_edit_text('')

    def get_downloaded_video_list(self):
        video_list = os.listdir(os.getcwd())
        video_list = [os.path.splitext(video)[0] for video in video_list]
        return video_list

    def keypress(self, size, key):
        if key == 'backspace':
            if self.edit_text == '':
                self.set_caption('')
                loop.draw_screen()
                main_frame.set_focus('body')
            else:
                return urwid.Edit.keypress(self, size, key)
        elif key == 'enter' and not self.get_edit_text() == '':
            if self.caption == '/':
                pattern = self.get_edit_text()
                self.clear()
                listbox.search(pattern)
                return
            command = self.get_edit_text()
            command = command.split(' ', 1)
            if command[0] in ('search', 's'):
                try:
                    self.clear()
                    query = command[1]
                    status_bar.set_text(' Searching for: "' + query + '"')
                    loop.draw_screen()
                    search = client.search(query)
                    if search != []:
                        listbox.append(search)
                        status_bar.set_text(' ' + query)
                    else:
                        status_bar.set_text(' Please also enter what to search for')
                        loop.draw_screen()
                    main_frame.set_focus('body')
                except IndexError:
                    status_bar.set_text(' Please also enter what to search for')
                    loop.draw_screen()
                    main_frame.set_focus('body')
            elif command[0] in ('videos', 'v'):
                self.clear()
                status_bar.set_text(' Listing downloaded videos')
                loop.draw_screen()
                sorted_video_list = sorted(self.get_downloaded_video_list())
                videos = [client.get_local_video(video) for video in sorted_video_list]
                listbox.append(videos, color='downloaded')
                main_frame.set_focus('body')
            elif command[0] == 'clear':
                self.clear()
                listbox.clear()
                main_frame.set_focus('body')
            elif command[0].isdigit():
                self.clear()
                video_focus = int(command[0]) - 1
                listbox.set_focus(video_focus)
                main_frame.set_focus('body')
            elif command[0] in ('quit', 'q'):
                raise urwid.ExitMainLoop()
            else:
                status_bar.set_text(' Error: There is no command named "' + command[0] + '"')
                pass
        elif key in ('esc', 'ctrl x'):
            main_frame.set_focus('body')
            self.clear()
        else:
            return urwid.Edit.keypress(self, size, key)


class VideoListBox(urwid.WidgetWrap):
    def __init__(self):
        self.latest_search = None
        self.latest_search_position = None
        self.body = urwid.SimpleListWalker([])
        self.listbox = urwid.ListBox(self.body)
        urwid.WidgetWrap.__init__(self, self.listbox)

    def append(self, search, color='video'):
        downloaded_videos = command_prompt.get_downloaded_video_list()
        for video in search:
            if video.filename in downloaded_videos:
                color = 'downloaded'
            else:
                color = 'video'
            new_button = VideoButton(video, int(len(self.body)) + 1, color)
            self.body.append(new_button)

    def clear(self):
        status_bar.set_text(' Cleared the screen')
        self.body[:] = []

    def set_focus(self, position):
        self.listbox.set_focus(position)

    def get_focus(self):
        return self.listbox.get_focus()[0]

    def search(self, pattern):
        # ignore case
        pattern = pattern.lower()
        video_list = [video_button.video.title.lower() for video_button in self.body]
        index_list = []
        for video in video_list:
            if pattern in video:
                index_list.append(video_list.index(video))
        self.latest_search = index_list
        self.latest_search_position = 0
        try:
            first_result = self.latest_search[self.latest_search_position]
            self.set_focus(first_result)
        except:
            status_bar.set_text(' Error, could not find pattern "' + pattern + '"')
        main_frame.set_focus('body')

    def keypress(self, size, key):
        if key == ':':
            main_frame.set_focus('footer')
            command_prompt.set_caption(':')
        if key == '/':
            main_frame.set_focus('footer')
            command_prompt.set_caption('/')
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
            self.clear()
        elif key == 'ctrl n':
            search = client.next_page()
            self.append(search)
        elif key == 'n':
            try:
                self.latest_search_position += 1
                self.listbox.set_focus(self.latest_search[self.latest_search_position])
            except IndexError:
                self.latest_search_position = 0
                self.listbox.set_focus(self.latest_search[self.latest_search_position])
        elif key == 'N':
            try:
                self.latest_search_position -= 1
                self.listbox.set_focus(self.latest_search[self.latest_search_position])
            except IndexError:
                self.latest_search_position = len(self.latest_search) - 1
                self.listbox.set_focus(self.latest_search[self.latest_search_position])
        else:
            return self.listbox.keypress(size, key)


def update(main_loop, user_data):
    # shows download progress of each video every half a second
    for video in youtube_client.YouTubeVideo.downloads:
        if video.dl.updated:
            video.dl.updated = False
            # search corresponding buttons and update download status
            for button in VideoButton.clicked_buttons:
                if button.video == video:
                    button.empty_line.set_text(('downloading', video.dl.progress))
    main_loop.set_alarm_in(0.5, update)


def main():
    # create the download directory if it doesn't exist already
    home_dir = os.environ['HOME']
    download_dir = os.path.join(home_dir, '.videotop/videos')
    try:
        os.makedirs(download_dir)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    # change to download directory
    os.chdir(download_dir)

    palette = [('focus', 'light red', 'black', 'standout'),
              ('status', 'white', 'dark blue'),
              ('opened', 'light blue', 'black'),
              ('bold', 'white', 'black', 'bold'),
              ('downloaded', 'light green', 'black'),
              ('downloading', 'light blue', 'black'),
              ('video', 'dark cyan', 'black'),
              ('normal', 'light gray', 'black')]

    global listbox
    global command_prompt
    global status_bar
    global main_frame
    global client
    global loop

    listbox = VideoListBox()
    command_prompt = CommandPrompt('')
    welcome_message = ' Type ":s Monty Python<Enter>" to search for "Monty Python" videos on YouTube'
    status_bar = urwid.Text(welcome_message, align='left')
    footer = urwid.Pile([urwid.AttrMap(status_bar, 'status'), command_prompt])
    main_frame = urwid.Frame(listbox)
    main_frame.set_footer(footer)
    client = youtube_client.YouTubeClient()

    loop = urwid.MainLoop(main_frame, palette)
    loop.set_alarm_in(0, update)
    loop.run()

    # cancel all downloads
    for video in youtube_client.YouTubeVideo.downloads:
        video.dl.kill()


if __name__ == '__main__':
    main()
