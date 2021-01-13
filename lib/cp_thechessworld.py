# Copyright (C) 2019-2020 Pychess
# Copyright (C) 2021 ecrucru
# https://github.com/ecrucru/chess-dl
# GPL version 3

from lib.const import CAT_DL
from lib.cp_interface import InternetGameInterface

import re


# TheChessWorld.com
class InternetGameThechessworld(InternetGameInterface):
    def get_identity(self):
        return 'TheChessWorld.com', CAT_DL

    def assign_game(self, url):
        return self.reacts_to(url, 'thechessworld.com')

    def download_game(self):
        # Check
        if self.id is None:
            return None

        # Find the links
        links = []
        if self.id.lower().endswith('.pgn'):
            links.append(self.id)
        else:
            # Download the page
            data = self.download(self.id)
            if data is None:
                return None

            # Finds the games
            rxp = re.compile(r".*pgn_uri:.*'([^']+)'.*", re.IGNORECASE)
            lines = data.split("\n")
            for line in lines:
                m = rxp.match(line)
                if m is not None:
                    links.append('https://www.thechessworld.com' + m.group(1))

        # Collect the games
        return self.download_list(links)

    def get_test_links(self):
        return [('https://thechessworld.com/articles/middle-game/typical-sacrifices-in-the-middlegame-sacrifice-on-e6/', True),     # 3 embedded games
                ('https://THECHESSWORLD.com/pgngames/middlegames/sacrifice-on-e6/Ivanchuk-Karjakin.pgn', True),                     # Direct link
                ('https://thechessworld.com/help/about/', False)]                                                                   # Not a game (about page)
