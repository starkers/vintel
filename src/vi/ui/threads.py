###########################################################################
#  Vintel - Visual Intel Chat Analyzer                                    #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
#                                                                         #
#  This program is free software: you can redistribute it and/or modify   #
#  it under the terms of the GNU General Public License as published by   #
#  the Free Software Foundation, either version 3 of the License, or      #
#  (at your option) any later version.                                    #
#                                                                         #
#  This program is distributed in the hope that it will be useful,        #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#  GNU General Public License for more details.                           #
#                                                                         #
#                                                                         #
#  You should have received a copy of the GNU General Public License      #
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

from PyQt4.QtCore import QThread
from PyQt4.QtCore import SIGNAL

from Queue import Queue
import time

from vi import evegate
from vi import koschecker
from vi.cache.cache import Cache

from vi.resources import resourcePath

class AvatarFindThread(QThread):

    def __init__(self):
        QThread.__init__(self)
        self.q = Queue()

    def addChatEntry(self, chatEntry, clearCache=False):
        try:
            if clearCache:
                cache = Cache()
                cache.remove_avatar(chatEntry.message.user)
            self.q.put(chatEntry)
        except Exception as e:
            print "An error in the AvatarFindThread: ", str(e)

    def run(self):
        cache = Cache()
        lastCall = 0
        wait = 300 # time between 2 requests in ms
        while True:
            try:
                chatEntry = self.q.get()
                charName = chatEntry.message.user
                avatar = None
                if charName == "VINTEL":
                    with open(resourcePath("vi/ui/res/logo_small.png"), "rb") as f:
                        avatar = f.read()
                if not avatar:
                    avatar = cache.getAvatar(charName)
                if not avatar:
                    diffLastCall = time.time() - lastCall
                    if diffLastCall < wait:
                        time.sleep((wait - diffLastCall) /1000.0)
                    avatar = evegate.getAvatarForPlayer(charName)
                    lastCall = time.time()
                    if avatar:
                        cache.putAvatar(charName, avatar)
                if avatar:
                    self.emit(SIGNAL("avatar_update"), chatEntry, avatar)
            except Exception as e:
                print "An error in the avatar-find-thread: ", str(e)


class PlayerFindThread(QThread):
    
    def __init__(self):
        QThread.__init__(self)
        self.q = Queue()
        
    def addChatEntry(self, chatEntry):
        try:
            self.q.put(chatEntry)
        except Exception as e:
            print "An error in the PlayerFindThread: ", str(e)
        
    def run(self):
        try:
            cache = Cache()
            while True:
                chatEntry = self.q.get()
                text = chatEntry.message.utext
                parts = text.split("  ")  # split@double-space (not in name, right?)
        except Exception as e:
            print "An error in the PlayerFindThread: ", str(e)



class KOSCheckerThread(QThread):
    
    def __init__(self):
        QThread.__init__(self)
        self.q = Queue()
        
    def addRequest(self, names, requestType, onlyKos = False):
        try:
            self.q.put((names, requestType, onlyKos))
        except Exception as e:
            print "An error in the PlayerFindThread: ", str(e)
        
    def run(self):
        while True:
            names, requestType, onlyKos = self.q.get()
            hasKos = False
            try:
                state = "ok"
                checkResult = koschecker.check(names)
                text = koschecker.resultToText(checkResult, onlyKos)
                for name, data in checkResult.items():
                    if data["kos"] in (koschecker.KOS, koschecker.RED_BY_LAST):
                        hasKos = True
                        break
            except Exception as e:
                state = "error"
                text = unicode(e)
            self.emit(SIGNAL("kos_result"), state, text, requestType, hasKos)

class MapStatisticsThread(QThread):
    
    def __init__(self):
        QThread.__init__(self)
        
    def run(self):
        try:
            statistics = evegate.getSystemStatistics()
            time.sleep(5)  # sleeping to prevent a "need 2 arguments"-error
            result = {"result": "ok", "statistics": statistics}
        except Exception as e:
            print "An error in the MapStatisticsThread: ", str(e)
            result = {"result": "error", "text": unicode(e)}
        self.emit(SIGNAL("statistic_data_update"), result)