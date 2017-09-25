from fbCollect import *

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
