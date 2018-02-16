# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
#
# """Simple Bot to reply to Telegram messages.
#
# This program is dedicated to the public domain under the CC0 license.
#
# This Bot uses the Updater class to handle the bot.
#
# First, a few handler functions are defined. Then, those functions are passed to
# the Dispatcher and registered at their respective places.
# Then, the bot is started and runs until we press Ctrl-C on the command line.
#
# Usage:
# Basic Echobot example, repeats messages.
# Press Ctrl-C on the command line or send a signal to the process to stop the
# bot.
# """
#
# from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# import logging
#
# # Enable logging
# logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#                     level=logging.INFO)
#
# logger = logging.getLogger(__name__)
#
#
# # Define a few command handlers. These usually take the two arguments bot and
# # update. Error handlers also receive the raised TelegramError object in error.
# def start(bot, update):
#     """Send a message when the command /start is issued."""
#     update.message.reply_text("Hello!\n Please enter Your Username for the mazak")
#
#
# def help(bot, update):
#     """Send a message when the command /help is issued."""
#     update.message.reply_text('Help!')
#
#
# def echo(bot, update):
#     """Echo the user message."""
#     update.message.reply_text(update.message.text)
#
#
# def error(bot, update, error):
#     """Log Errors caused by Updates."""
#     logger.warning('Update "%s" caused error "%s"', update, error)
#
#
# def main():
#     """Start the bot."""
#     # Create the EventHandler and pass it your bot's token.
#     updater = Updater("542695220:AAG4yTei4DTwTKdbHk4VD8wyVvsuAD8_qG8")
#
#     # Get the dispatcher to register handlers
#     dp = updater.dispatcher
#
#     # on different commands - answer in Telegram
#     dp.add_handler(CommandHandler("start", start))
#     dp.add_handler(CommandHandler("help", help))
#
#     # on noncommand i.e message - echo the message on Telegram
#     dp.add_handler(MessageHandler(Filters.text, echo))
#
#     # log all errors
#     dp.add_error_handler(error)
#
#     # Start the Bot
#     updater.start_polling()
#
#     # Run the bot until you press Ctrl-C or the process receives SIGINT,
#     # SIGTERM or SIGABRT. This should be used most of the time, since
#     # start_polling() is non-blocking and will stop the bot gracefully.
#     updater.idle()
#
#
# if __name__ == '__main__':
#     main()


# !/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple Bot to reply to Telegram messages
# This program is dedicated to the public domain under the CC0 license.
"""
This Bot uses the Updater class to handle the bot.

First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

import MazakFiles
from MazakFiles import LoginErrorExcpetion, log_to_mazak, get_grades, get_avereges, avereges_to_string, \
    get_test_confirmations, BlockedStudent, get_available_notebooks, get_notebook, get_grade
import logging
import io
import sys

log_file = "log"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

with open("token","r+") as token:
    TOKEN = token.read().strip('\n')

BACK, USERNAME, PASSWORD, CHOOSING, GRADES, AVGS, EXAM_CERTIFICATE, NOTEBOOKS = range(8)

choosing_options = {
    BACK: "התנתק ❌",
    GRADES: "ציונים 💯",
    AVGS: "ממוצעים 📈",
    EXAM_CERTIFICATE: "אישור נבחן 📑",
    NOTEBOOKS: "מחברות 📓"
}

move_back = "חזור 🔙"


def start2(bot, update):
    reply_keyboard = [['Boy', 'Girl', 'Other']]

    update.message.reply_text(
        'Hi Please Enter The Username for the mazak:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return USERNAME


def start(bot, update):
    update.message.reply_text('אנא הכנס\י שם משתמש של המזק', reply_markup=ReplyKeyboardRemove())
    return USERNAME


def username(bot, update, user_data):
    user = update.message.from_user
    user_data["username"] = update.message.text
    logger.info("%s entered username", user.first_name)
    update.message.reply_text('אנא הכנס\י סיסמא של המזק')
    return PASSWORD


def password(bot, update, user_data):
    user = update.message.from_user
    user_data["password"] = update.message.text
    logger.info("%s entered password", user.first_name)
    try:
        log_to_mazak(user_data["username"], user_data["password"])
    except Exception as e:
        if type(e) == LoginErrorExcpetion:
            update.message.reply_text("שם המשתמש או הסיסמא אינם נכונים אנא נסה שוב")
            update.message.reply_text("אנא הכנס\י שם משתמש של המזק")
            return USERNAME
        else:
            update.message.reply_text(str(e))
            return ConversationHandler.END

    popup_choosing_keyboard(update, get_choosing_keyboard())
    return CHOOSING


def choosing(bot, update, user_data):
    user = update.message.from_user
    option = update.message.text
    logger.info("%s choosed %s", user.first_name, option)
    if option == choosing_options[AVGS]:
        avgs(update, user_data)
        return CHOOSING
    elif option == choosing_options[GRADES]:
        user_data["grades"] = get_grades(log_to_mazak(user_data["username"], user_data["password"]))[::-1]
        reply_keyboard = get_grades_keyboard(user_data)
        update.message.reply_text("אנא בחר\י קורס",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return GRADES
    elif option == choosing_options[EXAM_CERTIFICATE]:
        send_confirms_files(update, user_data)
    elif option == choosing_options[NOTEBOOKS]:
        user_data["notebooks"] = get_available_notebooks(log_to_mazak(user_data["username"], user_data["password"]))[
                                 ::-1]
        reply_keyboard = get_notebooks_keyboard(user_data)
        update.message.reply_text("אנא בחר\י מחברת",
                                  reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return NOTEBOOKS
    else:
        cancel(bot, update, user_data)


def get_notebooks_keyboard(user_data):
    reply_keyboard = [[move_back]]
    reply_keyboard += [["{} - {}".format(item["courseName"], item["testTimeTypeName"])] for item in
                       user_data["notebooks"]]
    return reply_keyboard


def get_grades_keyboard(user_data):
    reply_keyboard = [[move_back]]
    reply_keyboard += [[item["courseName"] + " " + item["actualCourseFullNumber"]] for item in user_data["grades"]]
    return reply_keyboard


def notebooks(bot, update, user_data):
    user = update.message.from_user
    course = update.message.text
    if course == move_back:
        popup_choosing_keyboard(update, get_choosing_keyboard())
        return CHOOSING
    logger.info("%s selected notebook %s", user.first_name, course)
    notebook = [item for item in user_data["notebooks"] if
                "{} - {}".format(item["courseName"], item["testTimeTypeName"]) == course][0]
    filename = "{} - {}".format(notebook["courseName"], notebook["testTimeTypeName"]) + ".pdf"
    update.message.reply_text("מוריד את המחברת..", reply_markup=ReplyKeyboardRemove())
    notebook_file = io.BytesIO(get_notebook(log_to_mazak(user_data["username"], user_data["password"]), notebook["id"]))
    update.message.reply_document(notebook_file, filename=filename, timeout=200,
                                  reply_markup=ReplyKeyboardMarkup(get_notebooks_keyboard(user_data),
                                                                   one_time_keyboard=True))
    return NOTEBOOKS


def avgs(update, user_data):
    reslt = avereges_to_string(get_avereges(log_to_mazak(user_data["username"], user_data["password"])))
    for item in reslt:
        update.message.reply_text(item)

    popup_choosing_keyboard(update, get_choosing_keyboard())
    return CHOOSING


def send_confirms_files(update, user_data):
    update.message.reply_text("מוריד את הקבצים...")
    try:
        reslt = get_test_confirmations(log_to_mazak(user_data["username"], user_data["password"]))
    except Exception as e:
        if type(e) is BlockedStudent:
            update.message.reply_text("המשתמש חסום, אי אפשר להוריד אישור נבחן")
            popup_choosing_keyboard(update, get_choosing_keyboard())
            return CHOOSING
    for file in reslt:
        update.message.reply_document(io.BytesIO(file[0]), filename=file[1])

    popup_choosing_keyboard(update, get_choosing_keyboard())
    return CHOOSING


def grades(bot, update, user_data):
    user = update.message.from_user
    course = update.message.text
    if course == move_back:
        popup_choosing_keyboard(update, get_choosing_keyboard())
        return CHOOSING
    logger.info("%s selected grade %s", user.first_name, course)
    course_id = [item["actualCourseID"] for item in user_data["grades"] if (item["courseName"] + " " + item["actualCourseFullNumber"]).replace(" ","") == course.replace(" ","")][0]
    grade_parts = get_grade(log_to_mazak(user_data["username"], user_data["password"]), course_id)
    grade_message = MazakFiles.grade_to_string(grade_parts)
    for part in grade_message[:-1]:
        update.message.reply_text(part)
    update.message.reply_text(grade_message[-1],
                              reply_markup=ReplyKeyboardMarkup(get_grades_keyboard(user_data), one_time_keyboard=True))
    return GRADES


def popup_choosing_keyboard(update, keyboard):
    reply_keyboard = keyboard
    update.message.reply_text("בחר\י אופציה",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                               resize_keyboard=True))


def get_choosing_keyboard():
    reply_keyboard = [
        [choosing_options[GRADES], choosing_options[AVGS], choosing_options[EXAM_CERTIFICATE],
         choosing_options[NOTEBOOKS]],
        [choosing_options[BACK]]
    ]
    return reply_keyboard


def grade_to_string(grade):
    return grade["courseName"] + "\n" \
           + "ציון סופי: " + str(grade["finalGradeName"]) + "\n" \
           + "נקודות זכות: " + str(grade["effectiveCredits"])


def cancel(bot, update, user_data):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('להתראות!',
                              reply_markup=ReplyKeyboardRemove())
    user_data["grades"] = []
    user_data["username"] = ""
    user_data["password"] = ""
    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={

            USERNAME: [MessageHandler(Filters.text, username, pass_user_data=True)],

            PASSWORD: [MessageHandler(Filters.text, password, pass_user_data=True)],

            GRADES: [MessageHandler(Filters.text, grades, pass_user_data=True)],

            CHOOSING: [MessageHandler(Filters.text, choosing, pass_user_data=True)],

            NOTEBOOKS: [MessageHandler(Filters.text, notebooks, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True),
                   MessageHandler('התנתק ❌', cancel, pass_user_data=True)],

        allow_reentry=True
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    #updater.start_polling()
    updater.start_webhook(listen='127.0.0.1', port=5000, url_path='bots/'+TOKEN)
    updater.bot.set_webhook(webhook_url='https://nmontag.com/bots/'+TOKEN,
                             certificate=open('/etc/letsencrypt/live/nmontag.com/fullchain.pem', 'rb'))

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
