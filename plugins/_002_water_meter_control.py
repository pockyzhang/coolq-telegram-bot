from telegram.ext import MessageHandler, Filters, ConversationHandler, CommandHandler
import global_vars
import json
from pathlib import Path
from utils import get_plugin_priority
import logging
import telegram


logger = logging.getLogger("CTBPlugin." + __name__)
logger.debug(__name__ + " loading")


global_vars.create_variable('filter_list', {'keywords': [], 'channels': []})


def load_data():
    logger.debug("Begin loading water meter config")
    json_file = Path('./plugins/conf/' + __name__ + '.json')
    if json_file.is_file():
        global_vars.filter_list = json.load(open('./plugins/conf/' + __name__ + '.json', 'r'))
        logger.debug("Water meter config loaded")


def save_data():
    json.dump(global_vars.filter_list,
              open('./plugins/conf/' + __name__ + '.json', 'w'),
              ensure_ascii=False,
              indent=4)


load_data()


def add_keyword(bot: telegram.Bot,
                update: telegram.Update,
                args: list):
    if update.message.chat_id not in global_vars.admin_list['TG']:
        return

    if len(args) == 0:
        update.message.reply_text('Usage: /add_keyword keyword1 keyword2 ...')
        return
    for keyword in args:
        logger.debug('keyword: ' + keyword)
        if keyword in global_vars.filter_list['keywords']:
            update.message.reply_text('Keyword: "' + keyword + '" already in list')
            continue
        global_vars.filter_list['keywords'].append(keyword)
    update.message.reply_text('Done.')
    save_data()

CHANNEL = range(1)


def begin_add_channel(bot: telegram.Bot,
                      update: telegram.Update):
    if update.message.chat_id not in global_vars.admin_list['TG']:
        return

    update.message.reply_text('Please forward me message from channels:')
    return CHANNEL


def add_channel(bot: telegram.Bot,
                update: telegram.Update):
    if update.message.forward_from_chat:
        if update.message.forward_from_chat.type != 'channel':  # it seems forward_from_chat can only be channels
            update.message.reply_text(
                'Message type error. Please forward me a message from channel, or use /cancel to stop')
            return
        if update.message.forward_from_chat.id not in global_vars.filter_list['channels']:
            global_vars.filter_list['channels'].append(update.message.forward_from_chat.id)
            save_data()
            update.message.reply_text('Okay, please send me another, or use /cancel to stop')
        else:
            update.message.reply_text('Already in list. Send me another or use /cancel to stop')
        return CHANNEL
    else:
        if update.message.text == '/cancel':
            update.message.reply_text('Done.')
            return ConversationHandler.END
        else:
            update.message.reply_text(
                'Message type error. Please forward me a message from channel, or use /cancel to stop')
            return CHANNEL


def cancel_add_channel(bot: telegram.Bot, update: telegram.Update):
    update.message.reply_text('Done.')
    return ConversationHandler.END

conv_handler = ConversationHandler(
        entry_points=[CommandHandler(command='begin_add_channel',
                                     callback=begin_add_channel,
                                     filters=Filters.private)],

        states={
            CHANNEL: [MessageHandler(Filters.all & Filters.private, add_channel)]
        },

        fallbacks=[CommandHandler(command='cancel',
                                  callback=cancel_add_channel,
                                  filters=Filters.private)]
    )


global_vars.dp.add_handler(conv_handler,
                           group=get_plugin_priority(__name__))
global_vars.dp.add_handler(CommandHandler(command='add_keyword',
                                          callback=add_keyword,
                                          filters=Filters.private,
                                          pass_args=True),
                           group=get_plugin_priority(__name__))
logger.debug(__name__ + " loaded")
