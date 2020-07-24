import html
from typing import List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import run_async, CommandHandler, Filters
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, BAN_STICKER, LOGGER, OWNER_ID
from tg_bot.modules.disable import DisableAbleCommandHandler
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_ban_protected, can_restrict, \
    is_user_admin, is_user_in_chat, is_user_creator
from tg_bot.modules.helper_funcs.extraction import extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.translations.strings import tld

@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def ban(update, context):
    chat = update.effective_chat  
    user = update.effective_user  
    message = update.effective_message
    args = context.args

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(tld(chat.id, "You don't seem to be referring to a user."))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(tld(chat.id, "I can't seem to find this user"))
            return ""
        else:
            raise
    
    if is_user_creator(chat, user_id, member):
        message.reply_text(tld(chat.id, "I can't ban chat creator, u trying to ban guy who promoted uh nice try ;_;"))
        return ""
    
    if user_id == OWNER_ID:
        message.reply_text(tld(chat.id, "Not gonna do that he is my Boss!"))
        return ""

    if user_id == 777000:
        message.reply_text(tld(chat.id, "I'm not going to ban telegram."))
        return ""
    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(tld(chat.id, "I really wish I could ban admins..."))
        return ""

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "I'm not gonna BAN myself, are you crazy?"))
        return ""

    log = "<b>{}:</b>" \
          "\n#BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id)
        context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text(tld(chat.id, "Banned!"))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text('Banned!', quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text(tld(chat.id, "Banned!."))

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_ban(update, context):
    chat = update.effective_chat  
    user = update.effective_user  
    message = update.effective_message
    args = context.args  

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text(tld(chat.id, "You don't seem to be referring to a user."))
        return ""
    
    if user_id == OWNER_ID:
        return ""
    
    if user_id == 777000:
        message.reply_text(tld(chat.id, "I'm not going to ban telegram."))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(tld(chat.id, "I can't seem to find this user"))
            return ""
        else:
            raise

    if is_user_creator(chat, user_id, member):
        message.reply_text(tld(chat.id, "I can't ban chat creator, u trying to ban guy who promoted u nice try ;__;"))
        return ""
        
    if is_user_ban_protected(chat, user_id, member):
        message.reply_text(tld(chat.id, "I really wish I could ban admins..."))
        return ""

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "I'm not gonna BAN myself, are you crazy?"))
        return ""

    if not reason:
        message.reply_text(tld(chat.id, "You haven't specified a time to ban this user for!"))
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    bantime = extract_time(message, time_val)

    if not bantime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP BANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title),
                                     mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name),
                                     member.user.id,
                                     time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        chat.kick_member(user_id, until_date=bantime)
        context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text("Banned! User will be banned for {}.".format(time_val))
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("Banned! User will be banned for {}.".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR banning user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Banned! User will be banned for {}.".format(time_val))

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def kick(update, context):
    chat = update.effective_chat  
    user = update.effective_user  
    message = update.effective_message 
    args = context.args 

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""
    
    if user_id == OWNER_ID:
        message.reply_text(tld(chat.id, "Insufficient rights to perform this action."))
        return ""
    
    if user_id == 777000:
        message.reply_text(tld(chat.id, "I'm not going to kick telegram."))
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(tld(chat.id, "I can't seem to find this user"))
            return ""
        else:
            raise

    if is_user_creator(chat, user_id, member):
        message.reply_text(tld(chat.id, "I can't kick chat creator, u trying to kick the guy who have full rights in this chat."))
        return ""
        
    if is_user_ban_protected(chat, user_id):
        message.reply_text(tld(chat.id, "I really wish I could kick admins..."))
        return ""

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "Yeahhh I'm not gonna do that"))
        return ""

    res = chat.unban_member(user_id)  # unban on current user = kick
    if res:
        context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
        message.reply_text(tld(chat.id, "Kicked!"))
        log = "<b>{}:</b>" \
              "\n#KICKED" \
              "\n<b>Admin:</b> {}" \
              "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name),
                                                           member.user.id)
        if reason:
            log += "\n<b>Reason:</b> {}".format(reason)

        return log

    else:
        message.reply_text(tld(chat.id, "Kicked!"))

    return ""


@run_async
@bot_admin
@can_restrict
def kickme(update, context):
    chat = update.effective_chat
    user_id = update.effective_message.from_user.id
    member = update.effective_chat.get_member(user_id)
    if user_id == OWNER_ID:
        update.effective_message.reply_text(tld(chat.id, "I can't kick My Master"))
        return
    if is_user_creator(update.effective_chat, user_id, member):
        update.effective_message.reply_text(tld(chat.id, "I wish i could kick the person who created this chat."))
        return
    if is_user_admin(update.effective_chat, user_id):
        update.effective_message.reply_text(tld(chat.id, "I wish I could... but you're an admin."))
        return

    res = update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        update.effective_message.reply_text(tld(chat.id, "No problem no need of noobs like uh."))
    else:
        update.effective_message.reply_text(tld(chat.id, "Huh? I can't :/"))


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def unban(update, context):
    message = update.effective_message  
    user = update.effective_user  
    chat = update.effective_chat  
    args = context.args

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text(tld(chat.id, "I can't seem to find this user"))
            return ""
        else:
            raise

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "How would I unban myself if I wasn't here...?"))
        return ""
    
    if is_user_creator(chat, user_id, member):
        return ""

    if is_user_in_chat(chat, user_id):
        message.reply_text(tld(chat.id, "Why are you trying to unban someone that's already in the chat?"))
        return ""

    chat.unban_member(user_id)
    message.reply_text(tld(chat.id, "Yep, this user can join again!"))

    log = "<b>{}:</b>" \
          "\n#UNBANNED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                       mention_html(user.id, user.first_name),
                                                       mention_html(member.user.id, member.user.first_name),
                                                       member.user.id)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    return log


__help__ = """
 - /kickme: kicks the user who issued the command

*Admin only:*
 - /ban <userhandle>: bans a user. (via handle, or reply)
 - /tban <userhandle> x(m/h/d): bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unban <userhandle>: unbans a user. (via handle, or reply)
 - /kick <userhandle>: kicks a user, (via handle, or reply)
"""

__mod_name__ = "Bans"

BAN_HANDLER = CommandHandler("ban", ban, pass_args=True, filters=Filters.group)
TEMPBAN_HANDLER = CommandHandler(["tban", "tempban"], temp_ban, pass_args=True, filters=Filters.group)
KICK_HANDLER = CommandHandler("kick", kick, pass_args=True, filters=Filters.group)
UNBAN_HANDLER = CommandHandler("unban", unban, pass_args=True, filters=Filters.group)
KICKME_HANDLER = DisableAbleCommandHandler("kickme", kickme, filters=Filters.group)

dispatcher.add_handler(BAN_HANDLER)
dispatcher.add_handler(TEMPBAN_HANDLER)
dispatcher.add_handler(KICK_HANDLER)
dispatcher.add_handler(UNBAN_HANDLER)
dispatcher.add_handler(KICKME_HANDLER)
