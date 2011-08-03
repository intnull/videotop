# Documentation and tutorial on gdata.youtube module
# http://code.google.com/apis/youtube/1.0/developers_guide_python.html
# http://www.webmonkey.com/2010/02/youtube_tutorial_lesson_2_the_data_api/

import gdata.youtube
import gdata.youtube.service
import webbrowser
import tempfile
import subprocess
import locale
import download_thread

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
        # query.start_index is 1 based
        query.start_index = (page - 1) * int(self.max_results) + 1
        query.max_results = self.max_results
        try:
            feed = self.yt_service.YouTubeQuery(query)
            return self.get_videos(feed)
        except gdata.service.RequestError:
            return []

    def get_videos(self, feed):
        videos = []
        for entry in feed.entry:
            new_video = YouTubeVideo(entry)
            videos.append(new_video)
        return videos

    def next_page(self):
        return self.search(self.last_search[0], self.last_search[1] + 1)

    def get_local_video(self, video_title):
        # replace html code &#47; with slashes
        video_title = video_title.replace('&#47;', '/')
        title = gdata.media.Title(text=video_title)
        group = gdata.media.Group(title=title)
        video_entry = gdata.youtube.YouTubeVideoEntry(media=group)
        return YouTubeVideo(video_entry)

class YouTubeVideo:
    downloads = []

    def __init__(self, entry):
        self.entry = entry
        self.title = entry.media.title.text
        # replace slashes with html code &#47;
        self.filename = self.title.replace('/', '&#47;')
        try:
            self.url = entry.media.player.url
            self.duration = entry.media.duration.seconds
            self.description = entry.media.description.text
            self.author = entry.author[0].name.text
            self.published = entry.published.text.split('T')[0]
        except:
            # dunno, local video
            self.author = 'N/A'
            self.duration = 'N/A'
            self.published = 'N/A'
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
        self.dl = download_thread.DownloadThread(self.filename, self.url)
        self.dl.start()
        YouTubeVideo.downloads.append(self)

    def abort(self):
        try:
            self.dl.kill()
            return 'Aborted downloading "' + self.title + '"'
        except:
            return 'Aborting downloading "' + self.title + '" failed'

    def get_formatted_duration(self):
        try:
            m, s = divmod(int(self.duration), 60)
            h, m = divmod(m, 60)
            formatted_duration = "%d:%02d:%02d" % (h, m, s)
            return formatted_duration
        except:
            return self.duration

    def get_formatted_views(self):
        try:
            return locale.format('%d', int(self.views), grouping=True)
        except ValueError:
            return self.views

    def play(self):
        temp = tempfile.TemporaryFile()
        file = self.filename + '.flv'
        subprocess.Popen(['mplayer', file], stdout=temp, stderr=temp, stdin=temp)
        file = self.filename + '.mp4'
        subprocess.Popen(['mplayer', file], stdout=temp, stderr=temp, stdin=temp)
