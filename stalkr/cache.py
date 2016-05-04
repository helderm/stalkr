import os
import requests

class UnknownExtensionException:
    def __init__(self, extension):
        self.extension = extension

    def __str__(self):
        return repr("{0}: unknown extension".format(self.extension))

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
            if extension[1:] not in self.extensions:
                raise UnknownExtensionException(extension[1:])
            filename = key + extension
            path = os.path.join(self.directory, filename)
            with open(path, "wb") as file:
                file.write(res.content)
            return True
        else:
            return False
