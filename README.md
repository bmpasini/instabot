InstaBot
========

This Instagram bot was developed with the purpose of making your Instagram profile more visible to people with similar interests.
The bot will visit hashtag pages of your choice and select photos that meet a certain condition. Then, it visits the owner of
these photos and if the person meets a 2nd condition, the bot will like its first `n` photos.

Conditions:

1) The photo must have at least 5 likes or 1 comment, but less than 500 likes and 50 comments.

2) The owner of the photo must have at least 300 followers and follow more than 300 people. The bot disregard people with more than
50,000 followers, as these people most likely will not follow you just because you liked their photo. The bot doesn't follow people
with a followed_by / follows ratio greater than 4.0 or lower than 0.05.

Other features:

- The bot is polite, as it has delays between Instagram requests. It aims to behave as a normal user would.
- The bot does not use their bullshit API. It just needs a username and password.

## Setup
Clone this repository:
```
git clone https://github.com/bmpasini/InstaBot.git
```
Run the following command to install the dependencies:
```
sudo pip install -r config/dependencies.txt
```

Modify the `config/config.yml` file to customize your bot, example:
```
CREDENTIALS:
  USERNAME: 'USERNAME'
  PASSWORD: 'PASSWORD'
TAGS: [ 'soccer', 'food', 'dog' ]
TOTAL_LIKES: 1000
LIKES_PER_USER: 7
```

- `CREDENTIALS`: Your login info.
- `TAGS`: Insert the hashtags you want to target, using the format shown above.
- `TOTAL_LIKES`: The number of likes you wish to make in one run of the bot. My suggestion is to not choose a value greater than 1000, as
Instagram may suspect your activities and delete your account.
- `LIKES_PER_USER`: Number of photos you want to like for each potential follower.

Then run:
```
python3 src/instabot.py
```

You may also pass in the path of a log file, for a personalized log:

```
python3 src/instabot.py <log_file_path>
```
