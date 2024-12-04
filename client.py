import socket
import time
import json
import psutil
import sys
import os

c2 = sys.argv[1]
try: server_name = sys.argv[2] if sys.argv[2] != "RenameMe" else "Server"
except: server_name = "Server"

def delete_self():
    script_path = os.path.abspath(__file__)
    try:
        os.remove(script_path)
        print(f"Scheduled deletion of: {script_path}")
    except Exception as e:
        print(f"Failed to delete the script: {e}")
        
class NodewatchClient:
    def __init__(self, server_host, server_port, server_id, heartbeat_interval=30):
        self.server_host = server_host
        self.server_port = server_port
        self.server_id = server_id
        self.heartbeat_interval = heartbeat_interval

    def get_system_stats(self):
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        return {"cpu_usage": cpu_usage, "ram_usage": ram_usage, "disk_usage": disk_usage}

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((self.server_host, self.server_port))
            print(f"Connected to Nodewatch Control Server at {self.server_host}:{self.server_port}")

            while True:
                try:
                    stats = self.get_system_stats()
                    stats["server_id"] = self.server_id
                    client_socket.sendall(json.dumps(stats).encode("utf-8"))
                    print(f"Sent stats: {stats}")
                    time.sleep(self.heartbeat_interval)
                except KeyboardInterrupt:
                    print("\nClient shutting down...")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break

if __name__ == "__main__":
    client = NodewatchClient(
        server_host=c2, server_port=4554, server_id=server_name, heartbeat_interval=60
    )
    delete_self()
    client.start()
