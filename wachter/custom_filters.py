from telegram.ext import BaseFilter


class FilterAdded(BaseFilter):                                         # filter for message, that bot was added to group
    def filter(self, message):
        if len(message.new_chat_members) == 0 or message.new_chat_members[-1].is_bot:
            return False
        return True


filter_added = FilterAdded()
