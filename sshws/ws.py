#!/usr/bin/python3
import socket
import threading
import select
import sys
import time
import logging
import os
import hashlib
import base64
import errno  # Import errno
import requests  # Tambahkan ini untuk mengunduh file izin
from datetime import datetime  # Import datetime

# URL izin IP
IZIN_URL = "https://raw.githubusercontent.com/kanggacor91/izin/main/ip"

# Fungsi untuk mendapatkan IP server secara otomatis
def get_public_ip():
    try:
        response = requests.get('http://ipv4.icanhazip.com')
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "Failed to retrieve IP"
    except Exception as e:
        return f"Error: {str(e)}"
        
def get_server_ip():
    try:
        server_ip = get_public_ip()
        return server_ip
    except Exception as e:
        logging.error(f"Error getting server IP: {str(e)}")
        sys.exit("Tidak bisa mendapatkan IP server. Script dihentikan.")

# Fungsi untuk mengecek apakah IP ada dalam daftar izin dan cek masa aktif
def check_ip_in_izin(server_ip):
    try:
        response = requests.get(IZIN_URL)
        if response.status_code == 200:
            izin_ips = response.text.splitlines()
            for line in izin_ips:
                if server_ip in line:
                    print(f"IP ditemukan dalam izin: {line}")
                    
                    # Periksa apakah nilai izin berisi 'Lifetime'
                    if "Lifetime" in line:  # Periksa apakah "Lifetime" ada dalam baris
                        print(f"Akses diizinkan tanpa batas waktu (Lifetime).")
                        return True
                    
                    # Ambil tanggal dari izin jika bukan "Lifetime"
                    izin_date_str = line.split()[2]
                    try:
                        izin_date = datetime.strptime(izin_date_str, "%Y-%m-%d").date()
                        today = datetime.now().date()

                        # Cek apakah masa izin masih berlaku
                        if today >= izin_date:
                            logging.error(f"Masa berlaku IP {server_ip} telah berakhir pada {izin_date}. Script dihentikan.")
                            sys.exit(f"ERROR - Masa berlaku IP {server_ip} telah berakhir pada {izin_date}. Script dihentikan.")
                        else:
                            print(f"Akses diizinkan. Masa berlaku hingga {izin_date}.")
                    except ValueError:
                        logging.error(f"Tanggal tidak valid ditemukan untuk IP {server_ip}. Script dihentikan.")
                        sys.exit(f"ERROR - Tanggal tidak valid ditemukan untuk IP {server_ip}. Script dihentikan.")
                    return True
            else:
                logging.error(f"IP {server_ip} tidak ditemukan dalam izin. Script dihentikan.")
                sys.exit(f"IP {server_ip} tidak diizinkan. Script dihentikan.")
        else:
            logging.error(f"Gagal mengunduh daftar izin dari {IZIN_URL}. Status code: {response.status_code}")
            sys.exit("Gagal mengunduh daftar izin. Script dihentikan.")
    except Exception as e:
        logging.error(f"Error during IP check: {str(e)}")
        sys.exit("Gagal melakukan pengecekan IP. Script dihentikan.")


# Direktori dan file log
log_directory = "/var/log/proxy"
log_file = "proxy.log"

# Membuat direktori jika belum ada
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Path lengkap ke file log
log_path = os.path.join(log_directory, log_file)

# Konfigurasi logging
logging.basicConfig(filename=log_path, level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Log tambahan ke console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

# Listen
LISTENING_ADDR = '127.0.0.1'
if sys.argv[1:]:
    LISTENING_PORT = sys.argv[1]
else:
    LISTENING_PORT = 10015

# Pass
PASS = ''

# CONST
BUFLEN = 8192
TIMEOUT = 60
DEFAULT_HOST = '127.0.0.1:143'
GUID = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
RESPONEE_FILE_PATH = "/etc/handeling"

# Default values
DEFAULT_RESPONEE = 'Switching Protocols'
DEFAULT_COLOR = 'green'

# Try to read the response and color from the file, otherwise use default values
try:
    with open(RESPONEE_FILE_PATH, 'r') as file:
        lines = file.readlines()  # Read all lines from the file
        
        # Get values from lines
        line1 = lines[0].strip() if len(lines) > 0 else ''
        line2 = lines[1].strip() if len(lines) > 1 else ''

        # Determine RESPONEE based on the logic provided
        if line1 and line2:  # Both lines have data
            RESPONEE = f"<b><font color='{line2}'>{line1}</font></b>"
        elif not line1 and line2:  # Line 1 is empty, line 2 has data
            RESPONEE = DEFAULT_RESPONEE
        elif line1 and not line2:  # Line 1 has data, line 2 is empty
            RESPONEE = f"<b><font color='{DEFAULT_COLOR}'>{line1}</font></b>"
        else:  # Both lines are empty
            RESPONEE = DEFAULT_RESPONEE

except FileNotFoundError:
    logging.error(f"Response file not found at {RESPONEE_FILE_PATH}, using default response.")
    RESPONEE = DEFAULT_RESPONEE
except Exception as e:
    logging.error(f"Error reading response file: {str(e)}, using default response.")
    RESPONEE = DEFAULT_RESPONEE


class Server(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.running = False
        self.host = host
        self.port = port
        self.threads = []
        self.threadsLock = threading.Lock()

    def run(self):
        logging.info(f"Server listening on {self.host}:{self.port}")
        self.soc = socket.socket(socket.AF_INET)
        self.soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.soc.settimeout(2)
        intport = int(self.port)
        self.soc.bind((self.host, intport))
        self.soc.listen(0)
        self.running = True

        try:
            while self.running:
                try:
                    c, addr = self.soc.accept()
                    c.setblocking(1)
                    logging.info(f"Accepted connection from {addr}")
                except socket.timeout:
                    continue

                conn = ConnectionHandler(c, self, addr)
                conn.start()
                self.addConn(conn)
        finally:
            self.running = False
            self.soc.close()

    def addConn(self, conn):
        try:
            self.threadsLock.acquire()
            if self.running:
                self.threads.append(conn)
        finally:
            self.threadsLock.release()

    def removeConn(self, conn):
        try:
            self.threadsLock.acquire()
            if conn in self.threads:
                self.threads.remove(conn)
        finally:
            self.threadsLock.release()

    def close(self):
        try:
            self.running = False
            self.threadsLock.acquire()

            threads = list(self.threads)
            for c in threads:
                c.close()
        finally:
            self.threadsLock.release()

class ConnectionHandler(threading.Thread):
    def __init__(self, socClient, server, addr):
        threading.Thread.__init__(self)
        self.clientClosed = False
        self.targetClosed = True
        self.client = socClient
        self.client_buffer = b''  # Buffer diubah menjadi bytes
        self.server = server
        self.addr = addr
        self.method = None
        
    def close(self):
        try:
            if not self.clientClosed:
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
                logging.info(f"Closed client connection from {self.addr}")
        except Exception as e:
            logging.error(f"Error closing client connection: {str(e)}")
        finally:
            self.clientClosed = True

        try:
            if not self.targetClosed:
                self.target.shutdown(socket.SHUT_RDWR)
                self.target.close()
                logging.info(f"Closed target connection for {self.addr}")
        except Exception as e:
            logging.error(f"Error closing target connection: {str(e)}")
        finally:
            self.targetClosed = True

    def run(self):
        try:
            self.client_buffer = self.client.recv(BUFLEN)
            if not self.client_buffer:
                logging.error(f"No data received from {self.addr}")
                return

            # Decode buffer ke str untuk pencarian header
            buffer_str = self.client_buffer.decode('utf-8')

            # Periksa apakah client mengirimkan permintaan WebSocket
            upgrade_header = self.findHeader(buffer_str, 'Upgrade')
            connection_header = self.findHeader(buffer_str, 'Connection')
            websocket_key = self.findHeader(buffer_str, 'Sec-WebSocket-Key')

            # Cek apakah header ada
            if upgrade_header and connection_header and websocket_key:
                logging.info(f"WebSocket headers are present. Proceeding with connection.")
                # Dapatkan path dari header X-Real-Host
                path = self.findHeader(buffer_str, 'X-Real-Host') or DEFAULT_HOST
                self.method_CONNECT(path)  # Panggil method CONNECT
            else:
                logging.info(f"Missing WebSocket headers from {self.addr}, adding default WebSocket headers.")

                # Jika tidak ada header WebSocket, tambahkan header default
                if not upgrade_header:
                    upgrade_header = 'websocket'
                
                if not connection_header:
                    connection_header = 'Upgrade'

                if not websocket_key:
                    # Generate a default WebSocket key
                    websocket_key = base64.b64encode(os.urandom(16)).decode('utf-8')
                
                # Menghasilkan `Sec-WebSocket-Accept` berdasarkan `Sec-WebSocket-Key`
                websocket_accept = self.calculate_websocket_accept(websocket_key)

                # Mengirimkan respons WebSocket upgrade
                response = (f"HTTP/1.1 101 {RESPONEE}\r\n"
                            f"Upgrade: websocket\r\n"
                            f"Connection: Upgrade\r\n"
                            f"Sec-WebSocket-Accept: {websocket_accept}\r\n"
                            f"\r\n")

                self.client.sendall(response.encode('utf-8'))
                logging.info(f"Sent WebSocket handshake response to {self.addr}")
                
                # Dapatkan path dari header X-Real-Host
                path = self.findHeader(buffer_str, 'X-Real-Host') or DEFAULT_HOST
                self.method_CONNECT(path)  # Panggil method CONNECT
                
        except Exception as e:
            logging.error(f"Error handling connection from {self.addr}: {str(e)}")
        finally:
            self.close()
            self.server.removeConn(self)

    def findHeader(self, head, header):
        """Find a specific header in the HTTP request."""
        headers = head.split('\r\n')
        for h in headers:
            if h.lower().startswith(header.lower() + ':'):
                return h.split(':', 1)[1].strip()
        return ''

    def calculate_websocket_accept(self, key):
        """Menghitung `Sec-WebSocket-Accept` berdasarkan `Sec-WebSocket-Key`."""
        accept_key = key + GUID
        sha1_result = hashlib.sha1(accept_key.encode('utf-8')).digest()
        accept_value = base64.b64encode(sha1_result).decode('utf-8')
        return accept_value

    def send_data_in_chunks(self, sock, data):
        """Send data in chunks to avoid exceeding buffer limits."""
        total_sent = 0
        while total_sent < len(data):
            try:
                sent = sock.send(data[total_sent:total_sent + BUFLEN])  # Mengirim sesuai ukuran BUFLEN
                if sent == 0:
                    raise RuntimeError("Socket connection broken")
                total_sent += sent
            except Exception as e:
                logging.error(f"Error sending data in chunks: {str(e)}")
                raise e

    def method_CONNECT(self, path):
        logging.info(f"CONNECT {path} from {self.addr}")

        self.method = 'CONNECT'

        if not path:
            logging.error("No path provided for CONNECT")
            return

        self.connect_target(path)
        self.target.setblocking(0)
        self.client.setblocking(0)

        # Mengelola komunikasi antara client dan target
        while True:
            try:
                r, w, e = select.select([self.client, self.target], [], [])
                if self.client in r:
                    data = self.client.recv(BUFLEN)
                    if data:
                        logging.debug(f"Received from client: {data}")  # Log data dari klien
                        if data.startswith(b"HTTP/") or data.startswith(b" HTTP/"):
                            logging.debug(f"Received from client: {data}")  # Log data dari klien
                            continue
                        self.send_data_in_chunks(self.target, data)  # Kirim data dengan pemecahan
                    else:
                        logging.warning(f"No data received from client: {self.addr}, possible remote send corrupt MAC")
                        break

                if self.target in r:
                    data = self.target.recv(BUFLEN)
                    if data:
                        logging.debug(f"Received from target: {data}")  # Log data dari target
                        self.send_data_in_chunks(self.client, data)  # Kirim data dengan pemecahan
                    else:
                        logging.warning(f"No data received from target: {self.addr}")
                        break
            except Exception as e:
                if e.errno == errno.EAGAIN or e.errno == errno.EWOULDBLOCK:
                    continue  # Ignore the non-blocking error
                logging.error(f"Error during communication: {str(e)}")
                break

        self.close()

    def connect_target(self, host):
        target_host, target_port = host.split(':')
        target_port = int(target_port)
        logging.info(f"Connecting to target {target_host}:{target_port}")
        soc_family = socket.AF_INET6 if ':' in target_host else socket.AF_INET
        self.target = socket.socket(soc_family)
        self.target.settimeout(TIMEOUT)
        self.target.connect((target_host, target_port))
        self.targetClosed = False

def main():
    # Mendapatkan IP server
    server_ip = get_server_ip()
    
    # Memeriksa apakah IP ada di file izin
    if not check_ip_in_izin(server_ip):
        sys.exit("IP tidak diizinkan, menghentikan script.")

    server = None  # Inisialisasi server sebelum try-except
    try:
        # Pastikan LISTENING_PORT dan LISTENING_ADDR terdefinisi
        if 'LISTENING_PORT' not in globals() or 'LISTENING_ADDR' not in globals():
            raise ValueError("LISTENING_PORT atau LISTENING_ADDR belum diatur.")
        
        port = int(LISTENING_PORT)
        server = Server(LISTENING_ADDR, port)
        server.start()

        while True:
            time.sleep(60)

    except KeyboardInterrupt:
        logging.info("Server dihentikan oleh pengguna.")
    except ValueError as ve:
        logging.error(f"Konfigurasi salah: {str(ve)}")
    except Exception as e:
        logging.error(f"Server mengalami kesalahan: {str(e)}")
    finally:
        if server is not None:
            server.close()
            logging.info("Server ditutup dengan baik.")


if __name__ == '__main__':
    main()

