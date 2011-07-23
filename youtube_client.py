# Documentation and tutorial on gdata.youtube module
# http://code.google.com/apis/youtube/1.0/developers_guide_python.html
# http://www.webmonkey.com/2010/02/youtube_tutorial_lesson_2_the_data_api/

import gdata.youtube
import gdata.youtube.service
import webbrowser
import subprocess
import tempfile

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

    def next_page(self):
        return self.search(self.last_search[0], self.last_search[1] + 1)

    def get_local_video(self, video_title):
        title = gdata.media.Title(text=video_title)
        group = gdata.media.Group(title=title)
        video_entry = gdata.youtube.YouTubeVideoEntry(media=group)
        return YouTubeVideo(video_entry)

class YouTubeVideo:
    def __init__(self, entry):
        self.title = entry.media.title.text
        try:
            self.url = entry.media.player.url
            self.duration = entry.media.duration.seconds
            self.description = entry.media.description.text
            self.author = entry.author[0].name.text
        except:
            self.author = 'N/A' # dunno, local video
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

    def download(self):
        # max-quality=34 means 360p, 35: 480p, 22: 720p, 37: 1080p
        command = ['youtube-dl', '--no-part', '--continue', '--max-quality=35', '--output=%(title)s.%(ext)s', self.url]
        temp = tempfile.TemporaryFile()
        self.download_process = subprocess.Popen(command, stdout=temp, stderr=temp)

    def abort(self):
        try:
            self.download_process.kill()
            return 'aborted download ' + self.title
        except:
            return 'aborting download failed'

    def play(self):
        temp = tempfile.TemporaryFile()
        self.file = self.title + '.flv'
        subprocess.Popen(['mplayer', '-fs', self.file], stdout=temp, stderr=temp)
        self.file = self.title + '.mp4'
        subprocess.Popen(['mplayer', '-fs', self.file], stdout=temp, stderr=temp)
