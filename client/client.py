import socket
import threading
import pickle
import os


class GameClient:
    COLORS = {
        "RED": "\\033[91m",
        "GREEN": "\\033[92m",
        "YELLOW": "\\033[93m",
        "BLUE": "\\033[94m",
        "CYAN": "\\033[96m",
        "RESET": "\\033[0m"
    }

    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.messages = []
        self.username = None
        self.role = None
        self.alive = True
        self.current_phase = None

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def colorize(self, text, color):
        return f"{self.COLORS.get(color, self.COLORS['RESET'])}{text}{self.COLORS['RESET']}"

    def receive_messages(self):
        while self.running:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                message = pickle.loads(data)
                self.handle_message(message)
            except Exception as e:
                print(self.colorize(f"[ERROR] Error receiving message: {e}", "RED"))
                self.running = False
                break

    def handle_message(self, message):
        if isinstance(message, dict):
            msg_type = message.get("type", "info")

            if msg_type == "info":
                print(self.colorize(f"[INFO] {message.get('text')}", "CYAN"))

            elif msg_type == "role":
                role = message.get("role")
                if role:
                    self.role = role
                    print(self.colorize(f"[ROLE] You are a {role.name}!", "GREEN"))
                    print(self.colorize(role.description, "YELLOW"))

            elif msg_type == "phase":
                phase = message.get("phase", "").name.upper()
                self.current_phase = phase
                print(self.colorize(f"\\n[PHASE] {phase} phase has begun.", "BLUE"))

            elif msg_type == "error":
                print(self.colorize(f"[ERROR] {message.get('text')}", "RED"))

            elif msg_type == "result":
                print(self.colorize(f"[RESULT] {message.get('text')}", "YELLOW"))

            elif msg_type == "dead":
                dead_list = message.get("players", [])
                print(self.colorize(f"[DEATH REPORT] Dead players: {', '.join(dead_list) or 'None'}", "RED"))
                if self.username in dead_list:
                    self.alive = False
                    print(self.colorize("[GAME OVER] You have died. You can no longer act.", "RED"))

            elif msg_type == "chat":
                text = message.get("text", "")
                self.messages.append(text)
                self.render_messages()

        elif isinstance(message, str):
            self.messages.append(message)
            self.render_messages()

        elif isinstance(message, list):
            self.messages = message
            self.render_messages()

    def get_action_type(self):
        if not self.role or not hasattr(self.role, "name"):
            return None
        return {
            "mafioso": "attack",
            "doctor": "protect",
            "sheriff": "investigate"
        }.get(self.role.name.lower(), None)

    def render_messages(self):
        self.clear_screen()
        print(self.colorize("---  Chat Messages  ---", "YELLOW"))
        for msg in self.messages[-10:]:
            print(msg)
        print("> ", end="", flush=True)

    def send_messages(self):
        while self.running:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue

                if user_input.lower() == "/quit":
                    print(self.colorize("[INFO] Disconnecting...", "CYAN"))
                    self.running = False
                    break

                if user_input.startswith("/t") and self.current_phase == "NIGHT" and self.alive:
                    parts = user_input.split()
                    if len(parts) == 2 and parts[1].isdigit():
                        action_type = self.get_action_type()
                        if action_type:
                            self.client_socket.sendall(pickle.dumps({
                                "type": "action",
                                "action": action_type,
                                "target": int(parts[1])
                            }))
                            print(self.colorize("[ACTION] Night action sent.", "GREEN"))
                            continue
                    print(self.colorize("[ERROR] Invalid format. Use /t <target_id>", "RED"))
                    continue

                self.client_socket.sendall(pickle.dumps({"type": "chat", "text": user_input}))
            except Exception as e:
                print(self.colorize(f"[ERROR] Error sending message: {e}", "RED"))
                break

    def start(self):
        try:
            print(self.colorize("[INFO] Connecting to the serverside...", "CYAN"))
            self.client_socket.connect((self.host, self.port))
            prompt = pickle.loads(self.client_socket.recv(4096))
            print(prompt)
            self.username = input("> ").strip()
            self.client_socket.sendall(pickle.dumps(self.username))

            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            self.send_messages()
        except Exception as e:
            print(self.colorize(f"[ERROR] Connection error: {e}", "RED"))
        finally:
            self.running = False
            self.client_socket.close()
            print(self.colorize("[INFO] Disconnected from serverside.", "CYAN"))


if __name__ == "__main__":
    GameClient().start()