import yaml, requests, random, time, datetime, json
from logger import Logger
from session import Session
from URL import URL

requests.packages.urllib3.disable_warnings()
TIME_BETWEEN_REQUESTS = 2 # seconds
WAIT_SERVER_RESPONSE_TIME = 10 # how long to wait for a server response // 10s a 30s

class InstaBot(object):

    def __init__(self, config_path):
        start_time = datetime.datetime.now()
        config = yaml.safe_load(open(config_path, "r"))
        username, password, tags, total_likes, likes_per_user, log_file_path = (config['CREDENTIALS']['USERNAME'], config['CREDENTIALS']['PASSWORD'],
                                                                                config['TAGS'], config['TOTAL_LIKES'], config['LIKES_PER_USER'], config['LOG_FILE_PATH'])
        self.logger = Logger(username, log_file_path)
        self.logger.log('InstaBot v0.1 started at %s:' % (start_time.strftime("%d.%m.%Y %H:%M")))
        self.total_likes = total_likes
        self.likes_per_user = likes_per_user
        self.session = Session(username, password, self.logger)
        self.run(username, password, tags)
        self.session.logout()

    def get_html(self, url):
        self.logger.log('Fetching: ' + url)
        response = requests.get(url, verify=False, timeout=WAIT_SERVER_RESPONSE_TIME)
        html = response.text
        time.sleep(TIME_BETWEEN_REQUESTS)
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
                if (likes >= min_likes and likes <= max_likes) or (comments >= min_comments and comments <= max_comments):
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
                    if (likes >= min_likes and likes <= max_likes) or (comments >= min_comments and comments <= max_comments):
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
            self.logger.log('Error parsing url: ' + url + ' - ' + str(e))
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
        min_followed_by = 1000
        max_followed_by = 50000
        min_follows = 1000
        max_follows = 100000000
        owner_url = URL.root + owner_name
        html = self.get_html(owner_url)
        try:
            data = self.get_data_from_html(html)
            follows = data['entry_data']['ProfilePage'][0]['user']['follows']['count']
            followed_by = data['entry_data']['ProfilePage'][0]['user']['followed_by']['count']
            if follows >= min_follows and follows <= max_follows and followed_by >= min_followed_by and followed_by <= max_followed_by:
                self.logger.log('Fetching user [' + owner_name + '] photo urls. (Follows: ' + str(follows) + ', Followed By: ' + str(followed_by) + ')')
                photos_json = data['entry_data']['ProfilePage'][0]['user']['media']['nodes']
                log_str = 'Photo codes: '
                for i, photo_json in enumerate(photos_json):
                    if i == self.likes_per_user:
                        break
                    photos.append(photo_json['id']) # 'id' and not 'code'
                    log_str += photo_json['code'] + ' '
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
            photos_to_like += self.get_owner_recent_photos(owner_name)
        return photos_to_like

    def get_photos_to_like(self, tags):
        photos_to_like = list()
        for tag in tags:
            self.logger.log('Finding photos with tag: #' + tag)
            photos_to_like += self.get_photos_to_like_from_tag(tag)
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

    def run(self, login, password, tags):
        likes = 0
        likes_per_cycle = 30
        error_400 = 0
        error_400_to_ban = 3
        ban_sleep_time = 2*60*60
        while True:
            like_queue = self.get_photos_to_like(tags)
            if not self.session.login_status:
                self.session.login()
            while len(like_queue) > 0:
                like_next, like_queue = like_queue[:likes_per_cycle], like_queue[likes_per_cycle:]
                for photo_id in like_next:
                    status = self.like(photo_id)
                    if status == 200:
                        likes += 1
                        if likes > self.total_likes:
                            self.logging.log('Success! Reached total number of likes. InstaBot is shutting down...')
                            return None
                        error_400 = 0
                        self.logger.log('Total likes: ' + str(likes))
                    elif status == 400:
                        if error_400 < error_400_to_ban:
                            error_400 += 1
                            self.logger.log('Error 400 - # ' + str(error_400))
                        else:
                            self.logger.log('Error 400 - # ' + str(error_400) + '- You might have been banned. InstaBot will sleep for 2 hours.')
                            time.sleep(ban_sleep_time)
                    # sleep after one like (from 1s to 3s)
                    wait = random.randint(1,3)
                    time.sleep(wait)
                # sleep after liking cycle (from 45s to 75s)
                wait = random.randint(45,75)
                self.logger.log('Finished liking cycle. Sleeping for ' + wait + ' seconds...')
                time.sleep(wait)
            # sleep after liking all tags (from 20min to 40min)
            wait = random.randint(20,40)*60
            self.logger.log('Finished liking tags. Sleeping for ' + wait/60 + ' minutes...')
            time.sleep(wait)

if __name__ == "__main__":
    bot = InstaBot('../config/config.yml')
