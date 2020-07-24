from typing import Union, List

from future.utils import string_types
from telegram import Update, Chat
from telegram.ext import CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import escape_markdown

from tg_bot import dispatcher
from tg_bot.modules.helper_funcs.handlers import CMD_STARTERS
from tg_bot.modules.helper_funcs.misc import is_module_loaded
from tg_bot.modules.translations.strings import tld

FILENAME = __name__.rsplit(".", 1)[-1]

# If module is due to be loaded, then setup all the magical handlers
if is_module_loaded(FILENAME):
    from tg_bot.modules.helper_funcs.chat_status import user_admin, is_user_admin
    from telegram.ext.dispatcher import run_async

    from tg_bot.modules.sql import disable_sql as sql

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []

    class DisableAbleCommandHandler(CommandHandler):
        def __init__(self, command, callback, admin_ok=False, **kwargs):
            super().__init__(command, callback, **kwargs)
            self.admin_ok = admin_ok
            if isinstance(command, string_types):
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)

        def check_update(self, update):
            if isinstance(update, Update) and update.effective_message:
                message = update.effective_message

                if message.text and len(message.text) > 1:
                       fst_word = message.text.split(None, 1)[0]
                       if len(fst_word) > 1 and any(fst_word.startswith(start) for start in CMD_STARTERS):
                            args = message.text.split()[1:]
                            command = fst_word[1:].split('@')
                            command.append(message.bot.username)

                            if not (command[0].lower() in self.command
                                        and command[1].lower() == message.bot.username.lower()):
                                return None

                            filter_result = self.filters(update)
                            if filter_result:
                                chat = update.effective_chat
                                user = update.effective_user
                                # disabled, admincmd, user admin
                                if sql.is_command_disabled(chat.id, command[0].lower()):
                                # check if command was disabled
                                    is_disabled = command[0] in ADMIN_CMDS and is_user_admin(chat, user.id)
                                    if not is_disabled:
                                        return None
                                    else:
                                        return args, filter_result

                                return args, filter_result
                            else:
                                return False


    class DisableAbleMessageHandler(MessageHandler):
         def __init__(self, pattern, callback, friendly="", **kwargs):
             super().__init__(pattern, callback, **kwargs)
             DISABLE_OTHER.append(friendly or pattern)
             self.friendly = friendly or pattern

         def check_update(self, update):
             if isinstance(update, Update) and update.effective_message:
                 chat = update.effective_chat
                 return self.filters(update) and not sql.is_command_disabled(chat.id, self.friendly)


    @run_async
    @user_admin
    def disable(update, context):
        chat = update.effective_chat  # type: Optional[Chat]
        args = context.args
        if len(args) >= 1:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chat.id, disable_cmd)
                update.effective_message.reply_text(tld(chat.id, "Disabled the use of `{}`").format(disable_cmd),
                                                    parse_mode='markdown')
            else:
                update.effective_message.reply_text(tld(chat.id, "That command can't be disabled"))

        else:
            update.effective_message.reply_text(tld(chat.id, "What should I disable?"))


    @run_async
    @user_admin
    def enable(update, context):
        chat = update.effective_chat  # type: Optional[Chat]
        args = context.args
        if len(args) >= 1:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chat.id, enable_cmd):
                update.effective_message.reply_text(tld(chat.id, "Enabled the use of `{}`").format(enable_cmd),
                                                    parse_mode='markdown')
            else:
                update.effective_message.reply_text(tld(chat.id, "Is that even disabled?"))

        else:
            update.effective_message.reply_text(tld(chat.id, "What should I enable?"))


    @run_async
    @user_admin
    def list_cmds(update, context):
        chat = update.effective_chat
        if DISABLE_CMDS + DISABLE_OTHER:
            result = ""
            for cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                result += " - `{}`\n".format(escape_markdown(cmd))
            update.effective_message.reply_text(tld(chat.id, "The following commands are toggleable:\n{}").format(result),
                                                parse_mode='markdown')
        else:
            update.effective_message.reply_text(tld(chat.id, "No commands can be disabled."))


    # do not async
    def build_curr_disabled(chat_id: Union[str, int]) -> str:
        disabled = sql.get_all_disabled(chat_id)
        if not disabled:
            return "No commands are disabled!"

        result = ""
        for cmd in disabled:
            result += " - `{}`\n".format(escape_markdown(cmd))
        return "The following commands are currently restricted:\n{}".format(result)


    @run_async
    def commands(update, context):
        chat = update.effective_chat
        update.effective_message.reply_text(build_curr_disabled(chat.id), parse_mode='markdown')


    def __stats__():
        return "{} disabled items, across {} chats.".format(sql.num_disabled(), sql.num_chats())


    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)


    def __chat_settings__(chat_id):
        return build_curr_disabled(chat_id)


    __mod_name__ = "CMD-Disable"

    __help__ = """
 - /cmds: check the current status of disabled commands

*Admin only:*
 - /enable <cmd name>: enable that command
 - /disable <cmd name>: disable that command
 - /listcmds: list all possible toggleable commands
    """

    DISABLE_HANDLER = CommandHandler("disable", disable, pass_args=True, filters=Filters.group)
    ENABLE_HANDLER = CommandHandler("enable", enable, pass_args=True, filters=Filters.group)
    COMMANDS_HANDLER = CommandHandler(["cmds", "disabled"], commands, filters=Filters.group)
    TOGGLE_HANDLER = CommandHandler("listcmds", list_cmds, filters=Filters.group)

    dispatcher.add_handler(DISABLE_HANDLER)
    dispatcher.add_handler(ENABLE_HANDLER)
    dispatcher.add_handler(COMMANDS_HANDLER)
    dispatcher.add_handler(TOGGLE_HANDLER)

else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleMessageHandler = MessageHandler
