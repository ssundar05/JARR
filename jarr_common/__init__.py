from blinker import signal


feed_creation = signal('feed_creation')
entry_parsing = signal('entry_parsing')
article_parsing = signal('article_parsing')
