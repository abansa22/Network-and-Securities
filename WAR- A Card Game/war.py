"""
war card game client and server
"""
import asyncio
from collections import namedtuple
from enum import Enum
import logging
import random
import socket
import socketserver
import _thread
import sys
import selectors
import pickle

partner_clients = list()

"""
Namedtuples work like classes, but are much more lightweight so they end
up being faster. It would be a good idea to keep objects in each of these
for each game which contain the game's state, for instance things like the
socket, the cards given, the cards still available, etc.
"""
Game = namedtuple("Game", ["p1", "p2"])

class Command(Enum):
    """
    The byte values sent as the first byte of any message in the war protocol.
    """
    WANTGAME = 0
    GAMESTART = 1
    PLAYCARD = 2
    PLAYRESULT = 3


class Result(Enum):
    """
    The byte values sent as the payload byte of a PLAYRESULT message.
    """
    WIN = 0
    DRAW = 1
    LOSE = 2

def readexactly(sock, numbytes):
    """
    Accumulate exactly `numbytes` from `sock` and return those. If EOF is found
    before numbytes have been received, be sure to account for that here or in
    the caller.
    """
    
    data = b''
    while len(data) != numbytes:
        current = sock.recv(1)
        data += current
        if len(current) == 0 and len(data) != numbytes:
            print('ERROR OCURRED.')
            sock.close()
            return

    return data

def kill_game(c1, c2):
    """
    TODO: If either client sends a bad message, immediately nuke the game.
    """
    c1.close()
    c2.close()
    pass

def compare_cards(card1, card2):
    """
    TODO: Given an integer card representation, return -1 for card1 < card2,
    0 for card1 = card2, and 1 for card1 > card2
    """
    first_card = card1 % 13
    second_card = card2 % 13

    if first_card < second_card:
        return 2
    elif first_card == second_card:
        return 1
    else:
        return 0

def deal_cards():
    """
    TODO: Randomize a deck of cards (list of ints 0..51), and return two
    26 card "hands."
    """
    size_of_deck = 52
    deck = [index for index in range(size_of_deck)]
    random.shuffle(deck)
    first_hand_cards = []
    second_hand_cards = []

    while len(deck) > 0:
        dealt_card = deck.pop()
        if len(first_hand_cards) < 26:
            first_hand_cards.append(dealt_card)
        else:
            second_hand_cards.append(dealt_card)

    collective_hands = [first_hand_cards, second_hand_cards]
    return collective_hands

#*********************************#

def check_card(card, deck):
    if card not in deck:
        return False
    return True

#*********************************#


async def handle_game(first_client_socket, second_client_socket):
    """
    This is the main component of the game.
    first_client_socket and second_client_socket are 2 client sockets that connected as a pair
    They play the game here and the error checking is done here
    """

    deck_split = deal_cards()
    c1_cards = deck_split[0]
    c2_cards = deck_split[1]
    c1_used = [False] * 26
    c2_used = [False] * 26

    try:
        first_client_socket_data = await first_client_socket[0].readexactly(2)
        second_client_socket_data = await second_client_socket[0].readexactly(2)

        if(first_client_socket_data[1] != 0) or second_client_socket_data[1] != 0:
            print('ERROR! Entering zero for the first time is not allowed')
            kill_game(first_client_socket[1], second_client_socket[1])
            kill_game(first_client_socket[1].get_extra_info('socket'),
                      second_client_socket[1].get_extra_info('socket'))
            return

        first_client_socket[1].write(bytes(([Command.GAMESTART.value]+c1_cards)))
        second_client_socket[1].write(bytes(([Command.GAMESTART.value]+c2_cards)))

        total_turns_ingame = 0

        while total_turns_ingame < 26:

            first_client_socket_data = await first_client_socket[0].readexactly(2)
            second_client_socket_data = await second_client_socket[0].readexactly(2)

            # If first byte was 'play card'
            if first_client_socket_data[0] != 2 and second_client_socket_data[0] != 2:
                print('Error! Entering at 2 is not allowed by users.')
                kill_game(first_client_socket[1], second_client_socket[1])
                kill_game(first_client_socket[1].get_extra_info('socket'),
                          second_client_socket[1].get_extra_info('socket'))
                return

            # Check if card is in deck

            if check_card(first_client_socket_data[1], deck_split[0]) is False\
                    or check_card(second_client_socket_data[1], deck_split[1]) is False:
                print('Error! A clients card did not match card dealt')
                kill_game(first_client_socket[1], second_client_socket[1])
                kill_game(first_client_socket[1].get_extra_info('socket'),
                          second_client_socket[1].get_extra_info('socket'))
                return

            # If card was already used
            for x in range(0, 26):

                if first_client_socket_data[1] == c1_cards[x] or \
                        second_client_socket_data[1] == c2_cards[x]:

                    if first_client_socket_data[1] == c1_cards[x]:

                        if c1_used[x] is False:
                            c1_used[x] = True
                        else:
                            print('Error: Using the same card again is not allowed to the client')
                            kill_game(first_client_socket[1], second_client_socket[1])
                            kill_game(first_client_socket[1].get_extra_info('socket'),
                                      second_client_socket[1].get_extra_info('socket'))
                            return

                    if second_client_socket_data[1] == c2_cards[x]:
                        if c2_used[x] is False:
                            c2_used[x] = True
                        else:
                            print('Error: Using the same card again is not allowed to the client')
                            kill_game(first_client_socket[1], second_client_socket[1])
                            kill_game(first_client_socket[1].get_extra_info('socket'),
                                      second_client_socket[1].get_extra_info('socket'))
                            return

            # results for both client
            c1_result = compare_cards(first_client_socket_data[1], second_client_socket_data[1])
            c2_result = compare_cards(second_client_socket_data[1], first_client_socket_data[1])

            # Concat the command to send with the result
            c1_send_result = [Command.PLAYRESULT.value, c1_result]
            c2_send_result = [Command.PLAYRESULT.value, c2_result]

            # Write back to the client
            first_client_socket[1].write(bytes(c1_send_result))
            second_client_socket[1].write(bytes(c2_send_result))

            total_turns_ingame += 1

        # Close the connections
        kill_game(first_client_socket[1], second_client_socket[1])
        kill_game(first_client_socket[1].get_extra_info('socket'),
                  second_client_socket[1].get_extra_info('socket'))

    except ConnectionResetError:
        logging.error("ConnectionResetError")
        return 0
    except asyncio.streams.IncompleteReadError:
        logging.error("asyncio.streams.IncompleteReadError")
        return 0
    except OSError:
        logging.error("OSError")
        return 0

#**********************************************************************#

async def pair_clients(reader, writer):

    for clients in partner_clients :
        if clients[1] is None:
            clients[1] = (reader, writer)
            await handle_game(clients[0], clients[1])
            clients[0][1].close()
            clients[1][1].close()
            partner_clients .remove(clients)
            return

    partner_clients .append([(reader, writer), None])

#*********************************************************************#

def serve_game(host, port):
    """
    TODO: Open a socket for listening for new connections on host:port, and
    perform the war protocol to serve a game of war between each client.
    This function should run forever, continually serving clients.
    """
    loop = asyncio.get_event_loop()
    co_routine = asyncio.start_server(pair_clients, host, port, loop=loop)

    server = loop.run_until_complete(co_routine)

    # Serve requests 
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close 
    server.close()
    loop.run_until_complete(server.wait_closed())

    loop.close()


async def limit_client(host, port, loop, sem):
    """
    Limit the number of clients currently executing.
    You do not need to change this function.
    """
    async with sem:
        return await client(host, port, loop)

async def client(host, port, loop):
    """
    Run an individual client on a given event loop.
    You do not need to change this function.
    """
    try:
        reader, writer = await asyncio.open_connection(host, port, loop=loop)
        # send want game
        writer.write(b"\0\0")
        card_msg = await reader.readexactly(27)
        myscore = 0
        for card in card_msg[1:]:
            writer.write(bytes([Command.PLAYCARD.value, card]))
            result = await reader.readexactly(2)
            if result[1] == Result.WIN.value:
                myscore += 1
            elif result[1] == Result.LOSE.value:
                myscore -= 1
        if myscore > 0:
            result = "won"
        elif myscore < 0:
            result = "lost"
        else:
            result = "drew"
        logging.debug("Game complete, I %s", result)
        writer.close()
        return 1
    except ConnectionResetError:
        logging.error("ConnectionResetError")
        return 0
    except asyncio.streams.IncompleteReadError:
        logging.error("asyncio.streams.IncompleteReadError")
        return 0
    except OSError:
        logging.error("OSError")
        return 0

def main(args):
    """
    launch a client/server
    """
    host = args[1]
    port = int(args[2])
    if args[0] == "server":
        try:
            serve_game(host, port)
        except KeyboardInterrupt:
            pass
        return
    else:
        loop = asyncio.get_event_loop()

    if args[0] == "client":
        loop.run_until_complete(client(host, port, loop))
    elif args[0] == "clients":
        sem = asyncio.Semaphore(1000)
        num_clients = int(args[3])
        clients = [limit_client(host, port, loop, sem)
                   for x in range(num_clients)]
        async def run_all_clients():
            """
            use `as_completed` to spawn all clients simultaneously
            and collect their results in arbitrary order.
            """
            completed_clients = 0
            for client_result in asyncio.as_completed(clients):
                completed_clients += await client_result
            return completed_clients
        res = loop.run_until_complete(
            asyncio.Task(run_all_clients(), loop=loop))
        logging.info("%d completed clients", res)

    loop.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])
