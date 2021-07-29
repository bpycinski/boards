# Copyright (C) 2019-2020 Pychess
# Copyright (C) 2021 ecrucru
# https://github.com/ecrucru/boards
# GPL version 3
import itertools
import time

import bs4
import selenium.common.exceptions
from selenium import webdriver

from typing import Optional, List, Tuple
from lib.const import BOARD_CHESS, METHOD_HTML, CHESS960, TYPE_TOURNAMENT
from lib.bp_interface import InternetGameInterface

import re
import chess


# Chess24.com
class InternetGameChess24(InternetGameInterface):
    def __init__(self):
        InternetGameInterface.__init__(self)
        self.regexes.update({'url': re.compile(r'^https?:\/\/chess24\.com\/[a-z]+\/(analysis|game|download-game|watch/live-tournaments)\/([a-z0-9\-_]+)[\/\?\#]?', re.IGNORECASE)})

    def get_identity(self) -> Tuple[str, int, int]:
        return 'Chess24.com', BOARD_CHESS, METHOD_HTML

    def assign_game(self, url: str) -> bool:
        m = self.regexes['url'].match(url)
        if m is not None:
            gid = str(m.group(2))
            if str(m.group(1)).lower() == 'watch/live-tournaments':
                self.url_type = TYPE_TOURNAMENT
                self.id = gid
                return True
            elif len(gid) == 22:
                self.id = gid
                return True
        return False


    def download_tournament(self, tournament_id):
        driver = webdriver.Chrome()
        driver.implicitly_wait(20)
        first_page = True
        round_id = 1
        match_id = 1
        game_id = 10
        # for game_id in itertools.count(start=1):
        while True:
            url = f'https://chess24.com/en/watch/live-tournaments/{tournament_id}/{round_id}/{match_id}/{game_id}'
            print(url)
            driver.get(url)
            time.sleep(5)
            print('1')
            if first_page:
                driver.find_element_by_xpath('//*[@id="data-consent-opt-in-all"]').click()
                print('2')
                driver.find_element_by_class_name('toggleNotationTable').click()
                print('3')
                first_page = False
            # check if it is not in other language
            if re.search('No games in this round', driver.find_element_by_class_name('currentGame').text):
                match_id += 1
                game_id = 1
            try:
                moves = driver.find_element_by_class_name("extension-item.Moves").text
                print('4')
            except selenium.common.exceptions.NoSuchElementException:
                print('NoSuchElementException')
                break
            if not len(moves):
                print('Empty moves')
                break
            print(moves)

            # page = self.download(url, userAgent=True)  # Else HTTP 403 Forbidden
            # soup = bs4.BeautifulSoup(page, "html.parser")
            # moves = soup.find_all(class_="extension-item Moves")

            print(f'downloaded game #{game_id}')
            game_id += 1
        pass

    def download_game(self) -> Optional[str]:
        # Download the page
        if self.id is None:
            return None
        # In case of a tournament, handle it separately
        if self.url_type == TYPE_TOURNAMENT:
            return self.download_tournament(self.id)
        url = 'https://chess24.com/en/game/%s' % self.id
        page = self.download(url, userAgent=True)  # Else HTTP 403 Forbidden
        if page is None:
            return None

        # Extract the JSON of the game
        lines = page.split("\n")
        for line in lines:
            line = line.strip()
            pos1 = line.find('.initGameSession({')
            pos2 = line.find('});', pos1)
            if -1 in [pos1, pos2]:
                continue

            # Read the game from JSON
            bourne = self.json_loads(line[pos1 + 17:pos2 + 1])
            chessgame = self.json_field(bourne, 'chessGame')
            moves = self.json_field(chessgame, 'moves')
            if '' in [chessgame, moves]:
                continue

            # Build the header of the PGN file
            game = {}
            game['_moves'] = ''
            game['_url'] = url
            game['Event'] = self.json_field(chessgame, 'meta/Event')
            game['Site'] = self.json_field(chessgame, 'meta/Site')
            game['Date'] = self.json_field(chessgame, 'meta/Date')
            game['Round'] = self.json_field(chessgame, 'meta/Round')
            game['White'] = self.json_field(chessgame, 'meta/White/Name')
            game['WhiteElo'] = self.json_field(chessgame, 'meta/White/Elo')
            game['Black'] = self.json_field(chessgame, 'meta/Black/Name')
            game['BlackElo'] = self.json_field(chessgame, 'meta/Black/Elo')
            game['Result'] = self.json_field(chessgame, 'meta/Result')

            # Build the PGN
            board = chess.Board(chess960=True)
            head_complete = False
            for move in moves:
                # Info from the knot
                kid = self.json_field(move, 'knotId')
                if kid == '':
                    break
                kmove = self.json_field(move, 'move')

                # FEN initialization
                if kid == 0:
                    kfen = self.json_field(move, 'fen')
                    if kfen == '':
                        break
                    try:
                        board.set_fen(kfen)
                    except Exception:
                        return None
                    game['Variant'] = CHESS960
                    game['SetUp'] = '1'
                    game['FEN'] = kfen
                    head_complete = True
                else:
                    if not head_complete:
                        return None

                    # Execution of the move
                    if kmove == '':
                        break
                    try:
                        kmove = chess.Move.from_uci(kmove)
                        game['_moves'] += board.san(kmove) + ' '
                        board.push(kmove)
                    except Exception:
                        return None

            # Rebuild the PGN game
            return self.rebuild_pgn(game)
        return None

    def get_test_links(self) -> List[Tuple[str, bool]]:
        return [('https://chess24.com/en/game/DQhOOrJaQKS31LOiOmrqPg#anchor', True),    # Game with anchor
                ('https://chess24.com/en/watch/live-tournaments/carlsen-caruana-world-chess-championship-2018', True),  # Live tournament
                ('https://CHESS24.com', False)]                                         # Not a game (homepage)


if __name__ == '__main__':
    bp = InternetGameChess24()
    bp.assign_game('https://chess24.com/en/watch/live-tournaments/carlsen-caruana-world-chess-championship-2018')
    bp.download_game()
