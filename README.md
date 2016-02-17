InstaBot
========

This Instagram bot was developed with the purpose of making your Instagram profile more visible to people with similar interests.
The strategy is straight-forward, but effective. The bot will visit hashtag pages of your choice and select photos that meet a certain
criteria. Then the bot visits the owner of these photos and if the owner meets the 2nd criteria, the bot will like its first 10 photos
(you can choose how many photos).

Criterias:

1) The photo must have at least 5 likes or 1 comment, but less than 500 likes and 50 comments.

2) The owner of the photo must have at least 1000 followers and must also follows more than 1000 people. The bot also disregard people
with more than 50,000 followers, as these people most likely will not follow you just because you liked their photo.

Other considerations:

- This bot is polite, in the sense that it has some delay between Instagram requests. It tries to behave as a normal user.
- This bot doesn't use the Instagram API. It just needs your username and password. The API sucks for Sandbox users!

##Setup
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
LIKES_PER_USER: 10
LOG_FILE_PATH: null
```

- `CREDENTIALS`: Your login info.
- `TAGS`: Insert the hashtags you want to target, using the format shown above.
- `TOTAL_LIKES`: The number of likes you wish to make in one run of the bot. My suggestion is to not like more than 1000 per day, as
Instagram may suspect your activities and potentially delete your account.
- `LIKES_PER_USER`: Number of photos you want to like for each potential follower.
- `LOG_FILE_PATH`: Leave it `null` if you want it to just print to the console. Otherwise, specify a log path.

Then run:
```
python3 src/instabot.py
```