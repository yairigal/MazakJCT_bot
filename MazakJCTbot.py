import os
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

import MazakFiles
from MazakFiles import LoginErrorExcpetion, log_to_mazak, get_grades, get_avereges, avereges_to_string, \
    get_test_confirmations, BlockedStudent, get_available_notebooks, get_notebook, get_grade, get_departments, \
    get_grade_sheet
import logging
import io
from datetime import datetime
import json

log_file = "log"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

with open("token", "r+") as token:
    TOKEN = token.read().strip('\n')

BACK, USERNAME, PASSWORD, CHOOSING, GRADES, AVGS, EXAM_CERTIFICATE, NOTEBOOKS, GRADES_SHEET_CHOOSE_DEP, GRADES_SHEET = range(
    10)

choosing_options = {
    BACK: "התנתק ❌",
    GRADES: "ציונים 💯",
    AVGS: "ממוצעים 📈",
    EXAM_CERTIFICATE: "אישור נבחן 📑",
    NOTEBOOKS: "מחברות 📓",
    GRADES_SHEET: "גליון ציונים 📜"
}

move_back = "חזור 🔙"


def start2(bot, update):
    reply_keyboard = [['Boy', 'Girl', 'Other']]

    update.message.reply_text(
        'Hi Please Enter The Username for the mazak:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return USERNAME


def start(bot, update):
    update_contacts(update)
    update.message.reply_text('אנא הכנס\י שם משתמש של המזק', reply_markup=ReplyKeyboardRemove())
    return USERNAME


def update_contacts(update):
    if not os.path.exists("contacts"):
        with open("contacts", "w+") as cts:
            cts.write("{}")
    with open("contacts", "r+") as cts:
        contacts = json.load(cts)
    contacts[update.message.from_user.id] = update.message.from_user.full_name
    with open("contacts", "w+") as cts:
        json.dump(contacts, cts)


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
    elif option == choosing_options[GRADES_SHEET]:
        user_data["dept"] = get_departments(log_to_mazak(user_data["username"], user_data["password"]))
        if len(user_data["dept"]) > 1:
            reply_keyboard = [[d["name"]] for d in user_data["dept"]]
            update.message.reply_text("אנא בחר\י מחלקה",
                                      reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
            return GRADES_SHEET_CHOOSE_DEP
        else:
            user_data["dept_code"] = user_data["dept"][0]["id"]
            reply_keyboard = [["עברית", "אנגלית"]]
            update.message.reply_text("אנא בחר\י שפה",
                                      reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                                       resize_keyboard=True))
            return GRADES_SHEET

    else:
        cancel(bot, update, user_data)


def choose_department(bot, update, user_data):
    user = update.message.from_user
    dept = update.message.text
    logger.info("%s selected grade %s", user.first_name, dept)
    user_data["dept_code"] = [item for item in user_data["dept"] if item["name"] == dept][0]["id"]
    reply_keyboard = [["עברית", "אנגלית"]]
    update.message.reply_text("אנא בחר\י שפה",
                              reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True,
                                                               resize_keyboard=True))
    return GRADES_SHEET


def grades_sheet(bot, update, user_data):
    user = update.message.from_user
    lang = update.message.text
    lang_name = lang
    if lang == "אנגלית":
        lang = 1
        lang_name = "Grades Sheet"
    else:
        lang = 0
        lang_name = "גליון ציונים"
    filename = "{} - {}.pdf".format(lang_name, str(datetime.today()).split()[0])
    update.message.reply_text("מוריד...", reply_markup=ReplyKeyboardRemove())
    notebook_file = io.BytesIO(
        get_grade_sheet(log_to_mazak(user_data["username"], user_data["password"]), user_data["dept_code"], lang))
    update.message.reply_document(notebook_file, filename=filename, timeout=200,
                                  one_time_keyboard=True)
    popup_choosing_keyboard(update, get_choosing_keyboard())
    return CHOOSING


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
    course_id = [item["actualCourseID"] for item in user_data["grades"] if
                 (item["courseName"] + " " + item["actualCourseFullNumber"]).replace(" ", "") == course.replace(" ",
                                                                                                                "")][0]
    final_grade = [item["finalGradeName"] for item in user_data["grades"] if
                   (item["courseName"] + " " + item["actualCourseFullNumber"]).replace(" ", "") == course.replace(" ",
                                                                                                                  "")][
        0]
    grade_parts = get_grade(log_to_mazak(user_data["username"], user_data["password"]), course_id)
    grade_message = MazakFiles.grade_to_string(grade_parts)
    grade_message.append("ציון סופי : {}".format(final_grade))
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
        [choosing_options[GRADES_SHEET],
         choosing_options[BACK]]
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

            NOTEBOOKS: [MessageHandler(Filters.text, notebooks, pass_user_data=True)],

            GRADES_SHEET: [MessageHandler(Filters.text, grades_sheet, pass_user_data=True)],

            GRADES_SHEET_CHOOSE_DEP: [MessageHandler(Filters.text, choose_department, pass_user_data=True)]

        },

        fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True),
                   MessageHandler('התנתק ❌', cancel, pass_user_data=True)],

        allow_reentry=True
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    #polling(updater)
    webhook(updater)
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def polling(updater):
    updater.start_polling()


def webhook(updater):
    updater.start_webhook(listen='127.0.0.1', port=5003, url_path='bots/' + TOKEN)
    updater.bot.set_webhook(url='https://nmontag.com/bots/' + TOKEN)


if __name__ == '__main__':
    main()
