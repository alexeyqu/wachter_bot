from telegram.ext import BaseFilter


class FilterBotAdded(BaseFilter):  # filter for message, that bot was added to group
    def filter(self, message):
        if message.new_chat_members[-1].is_bot:
            return False
        return True


filter_bot_added = FilterBotAdded()
