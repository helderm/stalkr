# -*- coding: utf-8 -*-
import tornado.ioloop
from tornado.web import Application, RequestHandler, HTTPError
from tornado.httpclient import AsyncHTTPClient
from tornado.options import define, options
from tornado.gen import coroutine
import json
import os
from py2neo import Graph, authenticate

base_url = 'http://' + os.getenv('OPENSHIFT_GEAR_DNS', 'localhost:8080')


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
    def get(self, uuid=None):
        cypher = self.db.cypher
        query = self.get_argument('q')

        users = []

        # TODO: implement the recommender algorithm
        query = 'MATCH (u:User) RETURN u ORDER BY u.screen_name LIMIT {0}'.format(20)
        cursor = cypher.execute(query)

        for res in cursor:
            user = {'username': res['u']['screen_name']}
            users.append(user)

        res = {'status': 0,
                'users': users}

        self.write(res)


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

    application = Application([(r'/users/?', MainHandler, dict(db=db)),
                               (r'/?', HomeHandler)], **settings)

    print('Listening on {0}:{1}'.format(options.host, options.port))
    application.listen(options.port, options.host)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
