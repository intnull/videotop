# Documentation and tutorial on gdata.youtube module
# http://code.google.com/apis/youtube/1.0/developers_guide_python.html
# http://www.webmonkey.com/2010/02/youtube_tutorial_lesson_2_the_data_api/

import gdata.youtube
import gdata.youtube.service
import webbrowser
import tempfile
import subprocess
import locale
import time

locale.setlocale(locale.LC_ALL, 'en_US')

class YouTubeClient:
    def __init__(self):
        self.yt_service = gdata.youtube.service.YouTubeService()
        self.max_results = 25
        self.last_search = None

    def search(self, search_terms, page=1):
        self.last_search = [search_terms, page]
        query = gdata.youtube.service.YouTubeVideoQuery()
        query.vq = search_terms
        query.start_index = (page - 1) * int(self.max_results) + 1 # query.start_index is 1 based
        query.max_results = self.max_results
        feed = self.yt_service.YouTubeQuery(query)
        return self.get_videos(feed)

    def get_videos(self, feed):
        videos = []
        for entry in feed.entry:
            new_video = YouTubeVideo(entry)
            videos.append(new_video)
        return videos

    def search_user(self, username):
        return self.get_videos(self.yt_service.GetYouTubeUserFeed(username=username))

    def get_related_videos(self, video):
        related_feed = self.yt_service.GetYouTubeRelatedVideoFeed(video_id=video.id)
        return self.get_videos(related_feed)

    def next_page(self):
        return self.search(self.last_search[0], self.last_search[1] + 1)

    def get_local_video(self, video_title):
        title = gdata.media.Title(text=video_title)
        group = gdata.media.Group(title=title)
        video_entry = gdata.youtube.YouTubeVideoEntry(media=group)
        return YouTubeVideo(video_entry)

class YouTubeVideo:
    last_streamed = None

    def __init__(self, entry):
        self.entry = entry
        self.title = entry.media.title.text
        try:
            self.url = entry.media.player.url
            self.duration = entry.media.duration.seconds
            self.description = entry.media.description.text
            self.author = entry.author[0].name.text
            self.published = entry.published.text.split('T')[0]
            self.id = entry.id.text.split('/')[-1]
        except:
            self.author = 'N/A' # dunno, local video
            self.duration = 'N/A'
            self.published = 'N/A'
            self.id = 'N/A'
        try:
            self.views = entry.statistics.view_count
        except AttributeError:
            self.views = 'N/A'
        try:
            self.rating = entry.rating.average
        except AttributeError:
            self.rating = 'N/A'
        self.download_process = None

    def open(self):
        webbrowser.open_new_tab(self.url)

    def download(self, destination=None):
        # TODO: replace this function by importing youtube-dl as a python module
        # max-quality=34 means 360p, 35: 480p, 22: 720p, 37: 1080p
        if destination:
            # streaming 360p
            output = '--output=' + destination
            max_quality = '--max-quality=34'
        else:
            # downloading 480p
            output = '--output=%(title)s.%(ext)s'
            max_quality = '--max-quality=35'
        command = ['youtube-dl', '--no-part', '--continue', max_quality, output, self.id]
        temp = tempfile.TemporaryFile()
        self.download_process = subprocess.Popen(command, stdout=temp, stderr=temp)

    def abort(self):
        try:
            self.download_process.kill()
            return 'aborted download ' + self.title
        except:
            return 'aborting download failed'

    def get_formatted_duration(self):
        try:
            m, s = divmod(int(self.duration), 60)
            h, m = divmod(m, 60)
            formatted_duration = "%d:%02d:%02d" % (h, m, s)
            return formatted_duration
        except:
            return self.duration # N/A

    def get_formatted_views(self):
        try:
            return locale.format('%d', int(self.views), grouping=True)
        except ValueError:
            return self.views

    def play(self, file=None):
        temp = tempfile.TemporaryFile()
        #fullscreen = '-fs'
        fullscreen = ''
        if file:
            subprocess.Popen(['mplayer', fullscreen, file], stdout=temp, stderr=temp, stdin=temp)
        else:
            file = self.title + '.flv'
            subprocess.Popen(['mplayer', fullscreen, file], stdout=temp, stderr=temp, stdin=temp)
            file = self.title + '.mp4'
            subprocess.Popen(['mplayer', fullscreen, file], stdout=temp, stderr=temp, stdin=temp)

    def stream(self):
        # TODO: replace this function with gstreamer
        streamfile = '/tmp/videotop'
        self.download(streamfile)
        if self.id != YouTubeVideo.last_streamed:
            # buffer video 10 seconds
            time.sleep(10)
        self.play(streamfile)
        YouTubeVideo.last_streamed = self.id
