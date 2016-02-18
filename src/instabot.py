import yaml, requests, random, time, datetime, json, sys
from logger import Logger
from session import Session
from URL import URL

requests.packages.urllib3.disable_warnings()
WAIT_SERVER_RESPONSE_TIME = 10 # how long to wait for a server response // 10s a 30s

class InstaBot(object):

    def __init__(self, config_path, log_file_path=None):
        start_time = datetime.datetime.now()
        config = yaml.safe_load(open(config_path, "r"))
        username, password, tags, total_likes, likes_per_user = (config['CREDENTIALS']['USERNAME'], config['CREDENTIALS']['PASSWORD'],
                                                                 config['TAGS'], config['TOTAL_LIKES'], config['LIKES_PER_USER'])
        self.logger = Logger(username, log_file_path)
        self.logger.log('InstaBot v0.1 started at %s:' % (start_time.strftime("%d.%m.%Y %H:%M")))
        self.total_likes = total_likes + self.iround(min(total_likes/2, max(0, random.gauss(0, 100)))) # gaussian distribution: mu = 0, sig = 100, round to nearest int
        self.logger.log('InstaBot v0.1 will like ' + self.total_likes + ' photos in total'))
        self.likes_per_user = likes_per_user
        self.liked_photos = set()
        self.session = Session(username, password, self.logger)
        self.run(username, password, tags)
        self.session.logout()
        end_time = datetime.datetime.now()
        self.logger.log('InstaBot v0.1 stopped at %s:' % (end_time.strftime("%d.%m.%Y %H:%M")))
        self.logger.log('InstaBot v0.1 took ' + str(end_time-start_time) + ' in total')

    def get_html(self, url):
        time_between_requests = random.randint(2,5)
        self.logger.log('Fetching ' + url)
        response = requests.get(url, verify=False, timeout=WAIT_SERVER_RESPONSE_TIME)
        html = response.text
        time.sleep(time_between_requests)
        return html

    def get_data_from_html(self, html):
        try:
            finder_start = '<script type="text/javascript">window._sharedData = '
            finder_end = ';</script>'
            data_start = html.find(finder_start)
            data_end = html.find(finder_end, data_start+1)
            json_str = html[data_start+len(finder_start):data_end]
            data = json.loads(json_str)
            return data
        except json.decoder.JSONDecodeError as e:
            self.logger.log('Error parsing json string: ' + str(e))

    def get_recent_tag_photos(self, tag):
        url = URL.tag + tag
        photos = list()
        min_likes = 5
        max_likes = 500
        min_comments = 1
        max_comments = 50
        try:
            html = self.get_html(url)
            data = self.get_data_from_html(html)
            # get data from recent posts only
            photos_json = list(data['entry_data']['TagPage'][0]['tag']['media']['nodes']) 
            for photo_json in photos_json:
                photo_id = photo_json['code']
                likes = photo_json['likes']['count']
                comments = photo_json['comments']['count']
                if photo_id not in self.liked_photos and ((likes >= min_likes and likes <= max_likes) or (comments >= min_comments and comments <= max_comments)):
                    photos.append(photo_id)
                    if len(photos) == 10:
                        break
            # fill up rest of photos list with top posts, until list has 10 potential people to be liked
            if len(photos) < 10:
                photos_json = list(data['entry_data']['TagPage'][0]['tag']['top_posts']['nodes']) 
                for photo_json in photos_json:
                    photo_id = photo_json['code']
                    likes = photo_json['likes']['count']
                    comments = photo_json['comments']['count']
                    if photo_id not in self.liked_photos and ((likes >= min_likes and likes <= max_likes) or (comments >= min_comments and comments <= max_comments)):
                        photos.append(photo_id)
                        if len(photos) == 10:
                            break
        except (KeyError, IndexError) as e:
            self.logger.log('Error parsing url: ' + url + ' - ' + str(e))
            time.sleep(10)
        return photos

    def get_photo_owner(self, photo_id):
        try:
            photo_url = URL.photo + photo_id
            html = self.get_html(photo_url)
            data = self.get_data_from_html(html)
            owner_name = data['entry_data']['PostPage'][0]['media']['owner']['username']
            return owner_name
        except (KeyError, IndexError) as e:
            self.logger.log('Error parsing url: ' + photo_url + ' - ' + str(e))
            time.sleep(10)
            return None

    def get_recent_tag_owners(self, tag):
        photos_ids = self.get_recent_tag_photos(tag)
        owners_names = list()
        for photo_id in photos_ids:
            owner_name = self.get_photo_owner(photo_id)
            owners_names.append(owner_name)
        return owners_names

    # get owner recent photos only if he/she meets requirements
    def get_owner_recent_photos(self, owner_name):
        photos = list()
        min_followed_by = 300
        max_followed_by = 50000
        min_follows = 300
        max_follows = 7500 # instagram limit
        min_follow_ratio = 0.05
        max_follow_ratio = 4.0
        owner_url = URL.root + owner_name
        html = self.get_html(owner_url)
        try:
            data = self.get_data_from_html(html)
            follows = data['entry_data']['ProfilePage'][0]['user']['follows']['count']
            followed_by = data['entry_data']['ProfilePage'][0]['user']['followed_by']['count']
            if follows == 0:
                follows = 1
            follow_ratio = followed_by / follows
            if (follows >= min_follows and follows <= max_follows and
                followed_by >= min_followed_by and followed_by <= max_followed_by and
                follow_ratio >= min_follow_ratio and follow_ratio <= max_follow_ratio):
                self.logger.log('Fetching user [' + owner_name + '] photo urls. (Follows: ' + str(follows) + ', Followed By: ' + str(followed_by) + ', Ratio: ' + str(follow_ratio) + ')')
                photos_json = data['entry_data']['ProfilePage'][0]['user']['media']['nodes']
                log_str = 'Photo codes: '
                for i, photo_json in enumerate(photos_json):
                    if i == self.likes_per_user:
                        break
                    photo_id = photo_json['id']
                    photo_code = photo_json['code']
                    if photo_id not in self.liked_photos:
                        photos.append(photo_id)
                        log_str += photo_code + ' '
                self.logger.log(log_str)
                self.logger.log('Photo IDs: ' + str(photos))
            else:
                self.logger.log('User [' + owner_name + '] doesn\'t meet requirements. (Follows: ' + str(follows) + ', Followed By: ' + str(followed_by) + ')')
        except (KeyError, IndexError) as e:
            self.logger.log('Error parsing url: ' + url + ' - ' + str(e))
            time.sleep(10)
        return photos

    def get_photos_to_like_from_tag(self, tag):
        photos_to_like = list()
        recent_photos = self.get_recent_tag_photos(tag)
        for recent_photo in recent_photos:
            owner_name = self.get_photo_owner(recent_photo)
            if owner_name is not None:
                photos_to_like += self.get_owner_recent_photos(owner_name)
        return photos_to_like

    def get_photos_to_like(self, tags):
        photos_to_like = list()
        for tag in tags:
            self.logger.log('Finding photos with tag: #' + tag)
            photos_to_like += self.get_photos_to_like_from_tag(tag)
            self.logger.log('There are ' + str(len(photos_to_like)) + ' photos in the like queue')
        return photos_to_like

    def like(self, photo_id):
        if (self.session.login_status):
            url = (URL.like % photo_id)
            try:
                status = self.session.post(url)
            except:
                status = 0
                self.logger.log("Like failed: " + url)
            return status

    def iround(self, x):
        return int(round(x) - .5) + (x > 0) # round a number to the nearest integer

    def run(self, login, password, tags):
        likes = 0
        error_400 = 0
        error_400_to_ban = 3
        ban_sleep_time = 2*60*60
        while True:
            like_queue = self.get_photos_to_like(tags)
            if not self.session.login_status:
                self.session.login()
            while len(like_queue) > 0:
                self.logger.log('There are ' + str(len(like_queue)) + ' elements in the like queue')
                likes_per_cycle = self.iround(min(20, max(0, random.gauss(10, 2)))) # gaussian distribution: mu = 10, sig = 2, round to nearest int
                like_next, like_queue = like_queue[:likes_per_cycle], like_queue[likes_per_cycle:]
                for photo_id in like_next:
                    status = self.like(photo_id)
                    if status == 200:
                        self.liked_photos.add(photo_id)
                        likes += 1
                        if likes > self.total_likes:
                            self.logger.log('Success! Reached total number of likes. InstaBot is shutting down...')
                            return
                        error_400 = 0
                        self.logger.log('Total likes: ' + str(likes))
                    elif status == 400:
                        if error_400 < error_400_to_ban:
                            error_400 += 1
                            self.logger.log('Error 400 - # ' + str(error_400))
                        else:
                            self.logger.log('Error 400 - # ' + str(error_400) + '- You might have been banned. InstaBot will sleep for 2 hours...')
                            time.sleep(ban_sleep_time)
                    # sleep after one like (from 2s to 5s)
                    wait = random.randint(2,5)
                    time.sleep(wait)
                # sleep after liking cycle (from 25s to 50s)
                wait = random.randint(25,50)
                self.logger.log('Finished liking cycle. Sleeping for ' + str(wait) + ' seconds...')
                time.sleep(wait)
            # sleep after liking all tags (from 5min to 15min)
            wait = random.randint(5,15)*60
            self.logger.log('Finished liking tags. Sleeping for ' + str(int(wait/60)) + ' minutes...')
            time.sleep(wait)

if __name__ == "__main__":
    try:
        InstaBot('config/config.yml', sys.argv[1])
    except IndexError:
        InstaBot('config/config.yml')
    

