#!/usr/bin/python2

import threading
from subprocess import Popen, PIPE

class DownloadThread(threading.Thread):
    def __init__(self, title, url):
        threading.Thread.__init__(self)
        self.progress = 'Preparing download...\n'
        self.updated = True
        self.killed = False

        # create the youtube-dl subprocess
        file = title + '.%(ext)s'
        output = '--output=' + file
        max_quality = '--max-quality=35'
        command = ['youtube-dl', '--no-part', '--continue', max_quality, output, url]
        self.download_process = Popen(command, stdout=PIPE, universal_newlines=True)

    def kill(self):
        self.download_process.kill()
        self.killed = True

    def run(self):
        while self.progress != '':
            self.progress = self.download_process.stdout.readline()
            self.updated = True
        if self.killed:
            self.progress = 'Aborted downloading\n'
        else:
            self.progress = 'Finished downloading\n'
