import facebook
import requests
import os.path
import sys
import time
import sqlite3
from datetime import datetime
import configparser

####################################################################


class fb_database:
    def __init__(self, name):
        self.name = name
        self.fresh = not os.path.isfile(name+".db")
        self.conn = sqlite3.connect(name + '.db')
        self.c = self.conn.cursor()
        if self.fresh:
            self.c.execute('''CREATE TABLE posts (post_id TEXT, date TEXT, message TEXT)''') 
            self.c.execute('''CREATE TABLE comments (post_id TEXT, comment_id TEXT, date TEXT, message TEXT, user_id INTEGER, user_name TEXT)''') 
            self.c.execute('''CREATE TABLE log  (last_update TEXT, page_nr INT, post_nr INT, next_page TEXT)''') 
            self.page_nr = 0
            self.post_nr = 0
            self.last_update = ""
            print("\nSet up new database\n")
        else:
            self.c.execute('''SELECT count(*) FROM log''')
            self.fresh = int(self.c.fetchone()[0])==0
            self.c.execute('''SELECT page_nr FROM log ORDER BY page_nr DESC LIMIT 1''')
            self.page_nr = int(self.c.fetchone()[0])
            self.c.execute('''SELECT post_nr FROM log ORDER BY page_nr DESC LIMIT 1''')
            self.post_nr = int(self.c.fetchone()[0])
            print("\nConnected to existing database\n")

    def __get__(self):
        print(self.name)

    def append_post(self, post):
        if 'message' in post:
            try:
                message = post['message'].decode('utf8')
                row = [post['id'], post['created_time'], message]
            except:  
                row = [post['id'], post['created_time'], post['message']]
        else:
            row = [post['id'], post['created_time'], ""]
        i = self.c.executemany('''INSERT INTO posts VALUES (?,?,?)''', (row,))
        self.fresh = False


    def append_comment(self, post, comment):
        try:
            message = comment['message'].decode('utf8')
            row = [post['id'], comment['id'], comment['created_time'], message, comment['from']['id'], comment['from']['name']]
        except:
            if 'name' in comment['from']:
                row = [post['id'], comment['id'], comment['created_time'], comment['message'], comment['from']['id'], comment['from']['name']]
            else:
                row = [post['id'], comment['id'], comment['created_time'], comment['message'], comment['from']['id'], '']
        i = self.c.executemany('''INSERT INTO comments VALUES (?,?,?,?,?,?)''', (row,))

    def log(self, posts):
        row = [str(datetime.now())[:19], self.page_nr, self.post_nr, posts['paging']['next']]
        i = self.c.executemany('''INSERT INTO log VALUES (?,?,?,?)''', (row,))

    def is_fresh(self):
        return self.fresh

    def get_page_nr(self):
        return self.page_nr

    def inc_page_nr(self):
        self.page_nr=self.page_nr + 1

    def get_post_nr(self):
        return self.post_nr

    def inc_post_nr(self):
        self.post_nr= self.post_nr + 1

    def total_posts(self):
            self.c.execute('''SELECT count(*) FROM posts''')
            return self.c.fetchone()[0]

    def total_comments(self):
            self.c.execute('''SELECT count(*) FROM comments''')
            return self.c.fetchone()[0]

    def get_next_page(self):
            self.c.execute('''SELECT next_page FROM log ORDER BY page_nr DESC LIMIT 1''')
            return self.c.fetchone()[0]

    def delete_db_file(self):
        if os.path.isfile(self.name+".db"):
            os.remove(self.name+".db")

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def create_graph_object(appid, appsecret):
    graph = facebook.GraphAPI()
    access_token = graph.get_app_access_token(app_id=appid, app_secret=appsecret)
    graph = facebook.GraphAPI(access_token)
    return graph

################################################################################

if __name__ == "__main__":

    conf = configparser.ConfigParser()
    conf.read('config')

    print('\nStart collect from: ' + conf.get('query', 'user') + '\n\n')

    db = fb_database(conf.get('query', 'user'))
    graph = create_graph_object(conf.get('Facebook.app.credentials', 'app_id'), conf.get('Facebook.app.credentials', 'app_secret'))
    profile = graph.get_object(conf.get('query', 'user'))
    date_limit = datetime.strptime(conf.get('query','date_limit'), '%Y-%m-%d')

    if db.is_fresh():
        posts = graph.get_connections(profile['id'], 'posts')
    else:
        posts = requests.get(db.get_next_page()).json()
        
    post_date = datetime.strptime(posts['data'][len(posts['data'])-1]['created_time'], '%Y-%m-%dT%H:%M:%S+0000')



    while post_date > date_limit:

        db.inc_page_nr()
        print("\nPage "+ str(db.get_page_nr())+ "  " + str(datetime.now())[:19], "\n" )

        for post in posts['data']:
            db.inc_post_nr()
            db.append_post(post=post)
            print(" Post " + str(db.get_post_nr())+ " from: " + post['created_time'][:19], sep="", end="")
            post_date = datetime.strptime(post['created_time'], '%Y-%m-%dT%H:%M:%S+0000')


            try:
                comments = graph.get_all_connections(post['id'], 'comments')

            except:
                print("Unexpected error:" + sys.exc_info()[0])
                time.sleep(60)
                graph = create_graph_object()

            cnr=0
            for comment in comments:
                db.append_comment(post, comment)
                cnr+=1

            print(". Fetched "+ str(cnr)+" comments.") 
        db.commit()
        try:
            posts = requests.get(posts['paging']['next']).json()
            db.log(posts)

        except KeyError:
            print("\nReached first page.")
            break

        except:
            print("Unexpected error:" + sys.exc_info()[0])
            time.sleep(60)
            graph = create_graph_object()
            
    db.close()
    print("\n Finished retrieving all posts and comments.\n")
