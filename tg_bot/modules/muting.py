import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram import ChatPermissions
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER, OWNER_ID
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict, is_user_creator
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable
from tg_bot.modules.helper_funcs.handlers import CustomCommandHandler
from tg_bot.modules.translations.strings import tld


@run_async
@bot_admin
@user_admin
@loggable
def mute(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(tld(chat.id, "You'll need to either give me a username to mute, or reply to someone to be muted."))
        return ""
    
    if user_id == OWNER_ID:
        message.reply_text(tld(chat.id, "-_- I'm not going to mute my master"))
        return ""

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "I'm not muting myself!"))
        return ""
    if user_id == 777000:
        message.reply_text(tld(chat.id, "I'm Not going to mute tg ;__;"))
        return ""

    member = chat.get_member(int(user_id))

    if member:
        if is_user_creator(chat, user_id, member=member):
            message.reply_text(tld(chat.id, "I can't mute chat creator ;_; ."))
            
        if is_user_admin(chat, user_id, member=member):
            message.reply_text(tld(chat.id, "Afraid I can't stop an admin from talking!"))

        elif member.can_send_messages is None or member.can_send_messages:
            context.bot.restrict_chat_member(chat.id, user_id, permissions=ChatPermissions(can_send_messages=False))
            message.reply_text(tld(chat.id, "Muted!"))
            return "<b>{}:</b>" \
                   "\n#MUTE" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {}".format(html.escape(chat.title),
                                              mention_html(user.id, user.first_name),
                                              mention_html(member.user.id, member.user.first_name))

        else:
            message.reply_text(tld(chat.id, "This user is already muted!"))
    else:
        message.reply_text(tld(chat.id, "This user isn't in the chat!"))

    return ""


@run_async
@bot_admin
@user_admin
@loggable
def unmute(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text(tld(chat.id, "You'll need to either give me a username to unmute, or reply to someone to be unmuted."))
        return ""

    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(chat, user_id, member=member):
            message.reply_text(tld(chat.id, "This is an admin, what do you expect me to do?"))
            return ""

        elif member.status != 'kicked' and member.status != 'left':
            if member.can_send_messages and member.can_send_media_messages \
                    and member.can_send_other_messages and member.can_add_web_page_previews:
                message.reply_text(tld(chat.id, "This user already has the right to speak."))
                return ""
            else:
                context.bot.restrict_chat_member(chat.id, int(user_id),
                                         permissions=ChatPermissions(
                                          can_send_messages=True,
                                          can_send_media_messages=True,
                                          can_send_other_messages=True,
                                          can_add_web_page_previews=True))
                message.reply_text(tld(chat.id, "Unmuted!"))
                return "<b>{}:</b>" \
                       "\n#UNMUTE" \
                       "\n<b>Admin:</b> {}" \
                       "\n<b>User:</b> {}".format(html.escape(chat.title),
                                                  mention_html(user.id, user.first_name),
                                                  mention_html(member.user.id, member.user.first_name))
    else:
        message.reply_text(tld(chat.id, "This user isn't even in the chat, unmuting them won't make them talk more than they "
                           "already do!"))

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(update, context) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
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

    if is_user_admin(chat, user_id, member):
        message.reply_text(tld(chat.id, "I really wish I could mute admins..."))
        return ""

    if user_id == context.bot.id:
        message.reply_text(tld(chat.id, "I'm not gonna MUTE myself, are you crazy?"))
        return ""

    if not reason:
        message.reply_text(tld(chat.id, "You haven't specified a time to mute this user for!"))
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP MUTED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        if member.can_send_messages is None or member.can_send_messages:
            context.bot.restrict_chat_member(chat.id, user_id, until_date=mutetime, permissions=ChatPermissions(can_send_messages=False))
            message.reply_text(tld(chat.id, "Muted for {}!").format(time_val))
            return log
        else:
            message.reply_text(tld(chat.id, "This user is already muted."))

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text(tld(chat.id, "Muted for {}!").format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR muting user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text(tld(chat.id, "Muted for {}!").format(time_val))

    return ""


__help__ = """
*Admin only:*
 - /mute <userhandle>: silences a user. Can also be used as a reply, muting the replied to user.
 - /tmute <userhandle> x(m/h/d): mutes a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
 - /unmute <userhandle>: unmutes a user. Can also be used as a reply, muting the replied to user.
"""

__mod_name__ = "Muting"

MUTE_HANDLER = CustomCommandHandler("mute", mute, pass_args=True, filters=Filters.group)
UNMUTE_HANDLER = CustomCommandHandler("unmute", unmute, pass_args=True, filters=Filters.group)
TEMPMUTE_HANDLER = CustomCommandHandler(["tmute", "tempmute"], temp_mute, pass_args=True, filters=Filters.group)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)
