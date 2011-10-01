#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import os
import errno
import urwid
import youtube_client

import socket # socket.gaierror
import subprocess # subprocess.CalledProcessError


class VideoButton(urwid.FlowWidget):
    clicked_buttons = []

    def __init__(self, video, index, color='index'):
        self.video = video
        self.index = index
        info = ('normal', ' (' + self.video.author + ', ' + self.video.rating + ', ' + self.video.duration + ')')
        self.title = urwid.Text([self.video.title, info])
        index = urwid.Text(('normal', ' ' + str(self.index) + '. '), align='right')
        index_width = 6
        self.display_widget = urwid.Columns([('fixed', index_width, index), self.title])
        self.display_widget = urwid.AttrMap(self.display_widget, color, 'focus')

    def rows(self, size, focus=False):
        return self.display_widget.rows(size, focus)

    def render(self, size, focus=False):
        return self.display_widget.render(size, focus)

    def selectable(self):
        return True

    def keypress(self, size, key):
        if key == 'enter':
            status_bar.set_text(' Downloading: "' + self.video.title + '"')

            # add download progress bar
            self.download_status = urwid.Text('Preparing download...')
            self.button = urwid.Pile([self.title, self.download_status])
            index = urwid.Text(('normal', ' ' + str(self.index) + '. '), align='right')
            index_width = 6
            self.display_widget = urwid.Columns([('fixed', index_width, index), self.button])
            self.display_widget = urwid.AttrMap(self.display_widget, 'downloaded', 'focus')
            self._invalidate()

            try:
                self.video.download()
                VideoButton.clicked_buttons.append(self)
            except AttributeError:
                status_bar.set_text(' Local videos do not support redownloading yet')
        elif key == 'o':
            self.display_widget.set_attr_map({None: 'opened'})
            status_bar.set_text(' Opening in browser: "' + self.video.title + '"')
            try:
                self.video.open()
            except AttributeError:
                status_bar.set_text(' Local videos do not support opening their YouTube site yet')
        elif key == 'p':
            status_bar.set_text(' Playing: "' + self.video.title + '"')
            if not self.video.play():
                status_bar.set_text(' You must download "' + self.video.title + '"' + ' first before you can play it')
        elif key == 's':
            self.display_widget.set_attr_map({None: 'streamed'})
            status_bar.set_text(' Streaming: "' + self.video.title + '"')
            loop.draw_screen()
            try:
                self.video.stream()
                status_bar.set_text(' Streamed: "' + self.video.title + '"')
            except AttributeError:
                status_bar.set_text(' Local videos do not support streaming yet')
            except subprocess.CalledProcessError:
                status_bar.set_text(' You probably lost your internet connection')
                main_frame.set_focus('body')
        elif key == 'a':
            status_bar.set_text(' ' + self.video.abort())
        else:
            return key


class CommandPrompt(urwid.Edit):

    def __init__(self):
        urwid.Edit.__init__(self, '')
        self.history = []
        self.history_offset = 0

    def clear(self):
        self.set_caption('')
        self.set_edit_text('')

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

            # add command to history
            self.history.append(command)
            self.history_offset = 0

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
                    else:
                        status_bar.set_text(' No results found for: "' + query + '"')
                    main_frame.set_focus('body')
                except IndexError:
                    status_bar.set_text(' Please also enter what to search for')
                    loop.draw_screen()
                    main_frame.set_focus('body')
                except socket.gaierror:
                    status_bar.set_text(' You probably lost your internet connection')
                    main_frame.set_focus('body')
            elif command[0] in ('videos', 'v'):
                self.clear()
                status_bar.set_text(' Listing downloaded videos')
                loop.draw_screen()
                sorted_video_list = sorted(listbox.get_downloaded_video_list())
                try:
                    pattern = command[1].lower()
                    pattern = pattern.encode('utf-8', 'ignore')
                    videos = [client.get_local_video(video) for video in sorted_video_list
                              if pattern in video.lower()]
                except IndexError:
                    videos = [client.get_local_video(video) for video in sorted_video_list]
                listbox.append(videos)
                main_frame.set_focus('body')
            elif command[0] == 'clear':
                self.clear()
                listbox.clear()
                main_frame.set_focus('body')
            elif command[0] == 'delete':
                self.clear()
                videobutton = listbox.get_focus()
                videobutton.video.abort()
                videofile = os.path.join(os.environ['HOME'], '.videotop/videos/' + videobutton.video.filename)
                extensions = ['.flv', '.mp4', '.webm']
                for ext in extensions:
                    try:
                        os.remove(videofile + ext)
                    except OSError:
                        pass
                videobutton.display_widget.set_attr_map({None: 'deleted'})
                videobutton.display_widget.set_focus_map({None: 'deleted_focus'})

                status_bar.set_text(' Deleted "' + videobutton.video.title + '"')
                main_frame.set_focus('body')
            elif command[0].isdigit():
                self.clear()
                index = listbox.get_real_index(int(command[0]))
                listbox.set_focus(index)
                main_frame.set_focus('body')
            elif command[0] in ('quit', 'q'):
                raise urwid.ExitMainLoop()
            else:
                status_bar.set_text(' Error: There is no command named "' + command[0] + '"')
                pass
        elif key in ('esc', 'ctrl x'):
            main_frame.set_focus('body')
            self.history_offset = 0
            self.clear()
        elif key in ('ctrl p', 'up'):
            if self.get_edit_text() not in self.history:
                self.current_command = self.get_edit_text()
            try:
                self.history_offset -= 1
                command = self.history[self.history_offset]
                self.set_edit_text(command)
                self.set_edit_pos(len(command))
            except IndexError:
                self.history_offset += 1
        elif key in ('ctrl n', 'down'):
            if self.get_edit_text() not in self.history:
                self.current_command = self.get_edit_text()
            try:
                self.history_offset += 1
                if self.history_offset == 0:
                    command = self.current_command
                elif self.history_offset < 0:
                    command = self.history[self.history_offset]
                else:
                    raise IndexError
                self.set_edit_text(command)
                self.set_edit_pos(len(command))
            except IndexError:
                self.history_offset -= 1
        else:
            return urwid.Edit.keypress(self, size, key)


class VideoListBox(urwid.WidgetWrap):
    def __init__(self):
        self.latest_search = None
        self.latest_search_position = None
        self.body = urwid.SimpleListWalker([])
        self.listbox = urwid.ListBox(self.body)
        urwid.WidgetWrap.__init__(self, self.listbox)
        self.dividers = 0

    def get_downloaded_video_list(self):
        video_list = os.listdir(os.getcwd())
        video_list = [os.path.splitext(video)[0] for video in video_list]
        return video_list

    def append(self, search):
        # add separator if listbox not empty
        if len(self.body):
            self.body.append(urwid.Divider('-'))
            self.dividers += 1

        downloaded_videos = self.get_downloaded_video_list()
        for video in search:
            if video.filename in downloaded_videos:
                color = 'downloaded'
            else:
                color = 'video'
            index = int(len(self.body)) - self.dividers + 1
            new_button = VideoButton(video, index, color)
            self.body.append(new_button)

        # move cursor to the first video of the search
        search_begin = len(self.body) - len(search)
        self.set_focus(search_begin)

    def get_real_index(self, index):
        # get the real index ignoring divider widgets
        for i in range(len(self.body)):
            try:
                buttonindex = self.body[i].index
                if index == buttonindex:
                    index = i
                    break
            except AttributeError:
                pass
        return index

    def clear(self):
        status_bar.set_text(' Cleared the screen')
        self.body[:] = []
        self.dividers = 0

    def set_focus(self, position):
        self.listbox.set_focus(position)

    def get_focus(self):
        return self.listbox.get_focus()[0]

    def search(self, pattern):
        # ignore case
        pattern = pattern.lower()
        pattern = pattern.encode('utf-8', 'ignore')

        results = []
        for i in range(len(self.body)):
            try:
                title = self.body[i].video.title.lower()
                if pattern in title:
                    results.append(i)
            except AttributeError:
                # ignore divider widgets
                pass

        self.latest_search = results
        self.latest_search_position = 0
        try:
            first_result = self.latest_search[self.latest_search_position]
            self.set_focus(first_result)
        except:
            status_bar.set_text(' Error, could not find pattern "' + pattern + '"')
            self.latest_search = None
            self.latest_search_position = None
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
            try:
                self.listbox.change_focus(size, 0)
            except AttributeError:
                pass
        elif key == 'G':
            try:
                self.listbox.change_focus(size, len(self.body) - 1)
            except AttributeError:
                pass
        elif key == 'ctrl d':
            try:
                position = self.listbox.get_focus()[0].index + 5
                position = self.get_real_index(position)
                self.listbox.set_focus(position, 'above')
            except TypeError:
                pass
        elif key == 'ctrl u':
            try:
                position = self.listbox.get_focus()[0].index - 5
                if position < 0:
                    position = 0
                position = self.get_real_index(position)
                self.listbox.set_focus(position, 'below')
            except TypeError:
                pass
        elif key == 'ctrl r':
            self.clear()
        elif key == 'ctrl n':
            try:
                status_bar.set_text(' Listing next videos please wait...')
                loop.draw_screen()
                search = client.next_page()
                status_bar.set_text('')
                self.append(search)
            except TypeError:
                status_bar.set_text(' You need to search for something before you do that!')
            except socket.gaierror:
                status_bar.set_text(' You probably lost your internet connection')
                main_frame.set_focus('body')
        elif key == 'n':
            try:
                self.latest_search_position += 1
                self.listbox.set_focus(self.latest_search[self.latest_search_position])
            except IndexError:
                self.latest_search_position = 0
                self.listbox.set_focus(self.latest_search[self.latest_search_position])
            except TypeError:
                pass
        elif key == 'N':
            try:
                self.latest_search_position -= 1
                self.listbox.set_focus(self.latest_search[self.latest_search_position])
            except IndexError:
                self.latest_search_position = len(self.latest_search) - 1
                self.listbox.set_focus(self.latest_search[self.latest_search_position])
            except TypeError:
                pass
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
                    button.download_status.set_text(('downloading', video.dl.progress.rstrip()))
    main_loop.set_alarm_in(0.5, update)


def main():
    # create the download directory if it doesn't already exist
    home_dir = os.environ['HOME']
    download_dir = os.path.join(home_dir, '.videotop/videos')
    try:
        os.makedirs(download_dir)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
    os.chdir(download_dir)

    palette = [('focus', 'light red', 'black', 'standout'),
              ('status', 'white', 'dark blue'),
              ('opened', 'light blue', 'black'),
              ('streamed', 'light blue', 'black'),
              ('bold', 'white', 'black', 'bold'),
              ('downloaded', 'light green', 'black'),
              ('downloading', 'light blue', 'black'),
              ('video', 'dark cyan', 'black'),
              ('deleted', 'dark gray', 'black'),
              ('deleted_focus', 'dark red', 'black'),
              ('normal', 'light gray', 'black')]

    global listbox
    global command_prompt
    global status_bar
    global main_frame
    global client
    global loop

    listbox = VideoListBox()
    command_prompt = CommandPrompt()
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
