# -*- coding: utf-8 -*-
import tornado.ioloop
from tornado.web import Application, RequestHandler, HTTPError
from tornado.httpclient import AsyncHTTPClient
from tornado.options import define, options
from tornado.gen import coroutine
import json
import os
from py2neo import Graph, authenticate

from cache import Cache
import twitter
from tfidf import recommend
from topics import get_topics

base_url = 'http://' + os.getenv('OPENSHIFT_GEAR_DNS', 'localhost:8080')

# Image cache directory
cache_dir = '/var/tmp/stalkr'

class HomeHandler(RequestHandler):

    @coroutine
    def post(self):
        query = self.get_argument('q')
        client = AsyncHTTPClient()

        res = yield client.fetch(base_url + '/users/?q={q}'.format(q=query))
        res = json.loads(res.body)
        users = res['users']

        yield self.get(users=users)

    @coroutine
    def get(self, users=None):
        if not users:
            users = []

        self.render('index.html', title='Stalkr', items=users)


class MainHandler(RequestHandler):

    def initialize(self, db):
        self.db = db

    @coroutine
    def get(self):
        cypher = self.db.cypher
        query = self.get_argument('q')
        alpha = float(self.get_argument('a', 0.5))
        prtype = self.get_argument('t', 'rankb')
        limit = int(self.get_argument('l', 30))

        users = recommend(query, alpha=alpha, pr_type=prtype, limit=limit)
        tokens = get_topics(query)
        res = {'users': users, 'tokens': tokens}
        self.write(res)

class ImageHandler(RequestHandler):
    def initialize(self, directory):
        self.cache = Cache(directory)
        self.twitter_token = twitter.get_bearer()

    @coroutine
    def get(self, user_id=None):
        image = self.cache.get(user_id)
        if not image:
            print("ImageHandler: {0}: image not present in cache".format(user_id))
            url = twitter.get_user_profile_image_url(user_id, self.twitter_token)
            if url is not None:
                print("ImageHandler: {0}: resolved profile image URL: {1}".format(user_id, url))
                if self.cache.set(user_id, url):
                    print("ImageHandler: {0}: cached image".format(user_id))
                    # Successfully cached user image.
                    image = self.cache.get(user_id)
                else:
                    self.fatal("ImageHandler: {0}: failed to cache image".format(user_id))
            else:
                print("ImageHandler: {0}: failed to fetch profile image URL from Twitter".format(user_id))
                image = "./static/default.png"

        content_type = self.path_to_content_type(image)
        self.set_header("Content-Type", content_type)
        with open(image, "r") as f:
            self.write(f.read())

    def fatal(self, message):
        print(message)
        raise tornado.web.HTTPError(404)

    def path_to_content_type(self, path):
        _, extension = os.path.splitext(path)
        # Remove leading dot from extension.
        return "image/{0}".format(extension[1:])

def main():
    define("host", default="127.0.0.1", help="Host IP")
    define("port", default=8080, help="Port")
    define("neo4j_host_port", default='localhost:7474', help="Neo4j Host and Port")
    define("neo4j_user_pwd", default='neo4j:neo4j', help="Neo4j User and Password")
    tornado.options.parse_command_line()

    print('Connecting to Neo4j at {0}...'.format(options.neo4j_host_port))
    user = options.neo4j_user_pwd.split(':')[0]
    pwd = options.neo4j_user_pwd.split(':')[1]
    authenticate(options.neo4j_host_port, user, pwd)
    db = Graph('http://{0}/db/data/'.format(options.neo4j_host_port))

    template_dir = os.getenv('OPENSHIFT_REPO_DIR', os.path.dirname(__file__))
    template_dir = os.path.join(template_dir, 'templates')
    static_dir = os.getenv('OPENSHIFT_DATA_DIR', os.path.dirname(__file__))
    static_dir = os.path.join(static_dir, 'static')

    settings = {
        'static_path': static_dir,
        'template_path': template_dir
    }

    application = Application([
                                  (r'/image/([^/]*)', ImageHandler, dict(directory=cache_dir)),
                                  (r'/users/?', MainHandler, dict(db=db)),
                                  (r'/?', HomeHandler)
                              ],
                              **settings)

    print('Listening on {0}:{1}'.format(options.host, options.port))
    application.listen(options.port, options.host)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
