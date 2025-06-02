import socket
import threading
import pickle
import queue
import time
from random import shuffle
from common import enums
from common import game


class Server:
    def __init__(self, host='0.0.0.0', port=5000):
        self.MIN_PLAYERS = 3
        self.host = host
        self.port = port
        self.users: list[tuple[socket.socket, str, game.Player]] = []
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.message_queue = queue.Queue()
        self.pending_actions = {}
        self.game_state = game.GameState()
        print(f"Server started at {self.host}:{self.port}")

    def send_to(self, conn, message):
        try:
            conn.sendall(pickle.dumps(message))
        except Exception as e:
            print(f"[ERROR] Failed to send message: {e}")

    def broadcast(self, sender_conn, message):
        for user_conn, _, _ in self.users:
            if user_conn != sender_conn:
                self.send_to(user_conn, message)

    def broadcast_all(self, message):
        for conn, _, _ in self.users:
            self.send_to(conn, message)

    def assign_roles(self):
        roles = [game.Mafioso(), game.Doctor(), game.Sheriff()]
        shuffle(roles)
        for player, role in zip(self.game_state.players, roles):
            player.role = role

    def handle_user(self, conn, addr):
        try:
            if self.game_state.phase != enums.Phase.LOBBY:
                self.send_to(conn, {'type': 'error', 'text': 'Game already in progress.'})
                conn.close()
                return

            self.send_to(conn, "Enter your name: ")
            name = pickle.loads(conn.recv(4096))
            player = game.Player(None, name, len(self.users))
            self.users.append((conn, name, player))
            self.game_state.add_player(player)

            join_msg = {'type': 'chat', 'text': f"{name} has joined the lobby."}
            self.broadcast(conn, join_msg)

            # Message reception loop only, not processing
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                msg = pickle.loads(data)
                self.message_queue.put((conn, msg))
        except Exception as e:
            print(f"[ERROR] Connection issue with {addr}: {e}")
        finally:
            self.remove_user(conn)

    def remove_user(self, conn):
        for user in self.users:
            if user[0] == conn:
                name = user[1]
                self.users.remove(user)
                self.broadcast(conn, {'type': 'chat', 'text': f"{name} has left the game."})
                conn.close()
                break

    def get_username(self, conn):
        for user_conn, name, _ in self.users:
            if user_conn == conn:
                return name
        return "Unknown"

    def get_player_by_conn(self, conn):
        for user_conn, _, player in self.users:
            if user_conn == conn:
                return player
        return None

    def get_expected_action(self, role):
        mapping = {
            game.Mafioso: enums.Action.ATTACK,
            game.Doctor: enums.Action.PROTECT,
            game.Sheriff: enums.Action.INVESTIGATE
        }
        for cls, action in mapping.items():
            if isinstance(role, cls):
                return action.value
        return enums.Action.NONE.value

    def resolve_night_actions(self):
        for player, target_id in self.pending_actions.items():
            try:
                target = self.game_state.players[target_id]
                player.role.ability(player, target)
            except Exception as e:
                print(f"[ERROR] Action failed: {e}")
        self.pending_actions.clear()

    def process_messages(self):
        while not self.message_queue.empty():
            conn, msg = self.message_queue.get()
            player = self.get_player_by_conn(conn)
            name = self.get_username(conn)

            if isinstance(msg, str):
                if msg == "/m":
                    user_list = ", ".join([f"<{u[1]}>" for u in self.users])
                    self.send_to(conn, {'type': 'chat', 'text': f"Active users: {user_list}"})
                else:
                    if self.game_state.phase != enums.Phase.DAY:
                        self.send_to(conn, {'type': 'error', 'text': 'Chat is only allowed during the DAY phase.'})
                    else:
                        self.broadcast(conn, {'type': 'chat', 'text': f"<{name}> {msg}"})

            elif isinstance(msg, dict):
                if msg.get("type") == "action" and self.game_state.phase == enums.Phase.NIGHT:
                    expected = self.get_expected_action(player.role)
                    if msg.get("action") == expected:
                        self.pending_actions[player] = msg["target"]
                        self.send_to(conn, {'type': 'info', 'text': 'Night action received.'})
                    else:
                        self.send_to(conn, {'type': 'error', 'text': 'Invalid night action.'})
                elif msg.get("type") == "chat":
                    if self.game_state.phase == enums.Phase.DAY:
                        self.broadcast(conn, {'type': 'chat', 'text': f"<{name}> {msg.get('text')}"})
                    else:
                        self.send_to(conn, {'type': 'error', 'text': 'Chat only allowed during DAY.'})

    def game_loop(self):
        print("Game loop started.")
        while True:
            self.process_messages()

            if self.game_state.phase == enums.Phase.LOBBY:
                if len(self.game_state.players) >= self.MIN_PLAYERS:
                    self.assign_roles()
                    self.broadcast_all({'type': 'chat', 'text': 'Game is starting!'})
                    for conn, _, player in self.users:
                        self.send_to(conn, {'type': 'role', 'role': player.role})
                    self.game_state.phase = enums.Phase.NIGHT

            elif self.game_state.phase == enums.Phase.NIGHT:
                self.broadcast_all({'type': 'phase', 'phase': self.game_state.phase})
                self.pending_actions.clear()

                # Wait for night actions (up to 20 seconds)
                start = time.time()
                while time.time() - start < 20:
                    self.process_messages()
                    time.sleep(0.1)

                self.resolve_night_actions()
                for player in self.game_state.players:
                    player.role.on_night_end(player)

                self.game_state.phase = enums.Phase.DAY

            elif self.game_state.phase == enums.Phase.DAY:
                self.broadcast_all({'type': 'phase', 'phase': self.game_state.phase})
                dead_players = [p.name for p in self.game_state.players if not p.alive]
                self.broadcast_all({'type': 'dead', 'players': dead_players})
                time.sleep(30)
                self.game_state.phase = enums.Phase.NIGHT

            time.sleep(0.1)  # prevent tight loop CPU burn

    def start(self):
        game_thread = threading.Thread(target=self.game_loop, daemon=True)
        game_thread.start()

        try:
            while True:
                conn, addr = self.server_socket.accept()
                print(f"Connection from {addr}")
                t = threading.Thread(target=self.handle_user, args=(conn, addr))
                t.start()
        except KeyboardInterrupt:
            print("Shutting down server.")
        finally:
            self.server_socket.close()


if __name__ == "__main__":
    Server().start()
