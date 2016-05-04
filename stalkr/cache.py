import os
import requests

class Cache:
    extensions = ["gif", "jpeg", "jpg", "png"]

    def __init__(self, directory):
        self.directory = directory
        if not os.path.isdir(directory):
            os.mkdir(directory)

    def get(self, key):
        for extension in self.extensions:
            filename = key + "." + extension
            path = os.path.join(self.directory, filename)
            if os.path.isfile(path):
                return path
        return None

    def set(self, key, url):
        res = requests.get(url)
        if res.status_code == 200:
            _, extension = os.path.splitext(url)
            filename = key + extension
            path = os.path.join(self.directory, filename)
            with open(path, "wb") as file:
                file.write(res.content)
            return True
        else:
            return False
