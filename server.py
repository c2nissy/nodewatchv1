import socket
import threading
import logging
import json
from datetime import datetime
import time
import os
import urllib.request

logfile = "nodewatch.log"
logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_public_ip():
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json") as response: ### easiest solution to get remote address
            data = json.load(response)
            return data['ip']
    except Exception as e:
        print(f"Error: {e}")
        exit()
        return None


class NodewatchControlServer:
    def __init__(self, host="0.0.0.0", port=5000, timeout=60):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.server_last_active = {}  
        self.server_stats = {}  # Stores system statistics for each server
        self.lock = threading.Lock()
        self.running = True

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            logging.info("Nodewatch Control Server started.")
            logging.info(f"CLIENT SETUP SCRIPT: sudo apt upgrade && sudo apt update &&  sudo apt install python3 && wget https://raw.githubusercontent.com/c2nissy/nodewatchv1/refs/heads/main/client.py && sleep 1 && python3 client.py {get_public_ip()} RenameMe")
            print(f"Nodewatch Control Server running on {self.host}:{self.port}")
            print(f"logfile: {logfile}")
            threading.Thread(target=self.monitor_servers, daemon=True).start()
            threading.Thread(target=self.display_online_servers, daemon=True).start()
            while self.running:
                try:
                    client_socket, client_address = server_socket.accept()
                    logging.info(f"Connection established with {client_address}")
                    threading.Thread(
                        target=self.handle_client, args=(client_socket, client_address), daemon=True
                    ).start()
                except KeyboardInterrupt:
                    self.running = False
                    print("\nShutting down server...")
                    logging.info("Nodewatch Control Server shutting down.")
                    break

    def handle_client(self, client_socket, client_address):
        with client_socket:
            while True:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    stats = json.loads(data.decode("utf-8"))
                    server_id = stats.get("server_id")
                    cpu_usage = stats.get("cpu_usage")
                    ram_usage = stats.get("ram_usage")
                    disk_usage = stats.get("disk_usage")

                    with self.lock:
                        self.server_last_active[server_id] = datetime.now()
                        self.server_stats[server_id] = {"cpu_usage": cpu_usage, "ram_usage": ram_usage, "disk_usage": disk_usage}

                    logging.info(f"Stats from {server_id}_{client_address}: CPU={cpu_usage}%, RAM={ram_usage}% DISK={disk_usage}%", )
                except (ConnectionResetError, json.JSONDecodeError):
                    logging.warning(f"Connection lost or invalid data from {client_address}")
                    break

    def monitor_servers(self):
        while self.running:
            time.sleep(10)
            now = datetime.now()
            inactive_servers = []

            with self.lock:
                for server_id, last_active in self.server_last_active.items():
                    if (now - last_active).seconds > self.timeout:
                        inactive_servers.append(server_id)

                for server_id in inactive_servers:
                    logging.warning(f"Server {server_id} is inactive.")
                    del self.server_last_active[server_id]
                    del self.server_stats[server_id]

    def display_online_servers(self):
        while self.running:
            time.sleep(30)  
            os.system("clear")
            print(f"Nodewatch Control Server running on {self.host}:{self.port}")
            print(f"logfile: {logfile}")
            with self.lock:
                if self.server_stats:
                    print("Online servers and their statuses:")
                    for server_id, stats in self.server_stats.items():
                        print(f"  [{server_id}] CPU: {stats['cpu_usage']}%, RAM: {stats['ram_usage']}%, DISK: {stats['disk_usage']}%")
                else:
                    print("No servers currently online.")

if __name__ == "__main__":
    # A nice and clean console :)
    os.system("clear")
    control_server = NodewatchControlServer(host="0.0.0.0", port=4554, timeout=120)
    control_server.start()
