DATETIME=$(date +"%Y%m%d%H%M%S")
ROOT_PATH=/Users/brunomacedo/code/side-projects/instagram/instabot
LOG_PATH=$ROOT_PATH/logs/
BOT_PATH=$ROOT_PATH/src/instabot.py
PYTHON_PATH=/Library/Frameworks/Python.framework/Versions/3.5/bin/python3
mkdir -p $LOG_PATH && cd $ROOT_PATH
echo "Saving log to $LOG_PATH"
$PYTHON_PATH -u $BOT_PATH $LOG_PATH &