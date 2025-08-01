#!/bin/bash

NAMA=$1
DOMAIN=$2
LOGFILE="/root/log_install_${NAMA}.log"
LOCKFILE="/tmp/setup_install.lock"
IZIN_URL="https://raw.githubusercontent.com/kanggacor91/izin/main/ip"
IPVPS=$(curl -s https://ipv4.icanhazip.com)
SCREEN_NAME="install_${NAMA}"
if screen -ls | grep -q "\.install_"; then
    for PID in $(pgrep -f "SCREEN.*setup.sh"); do
        if ps -p $PID -o args= | grep -q "/root/setup.sh"; then
            echo "⛔ Install.sh masih berjalan di screen. Tidak boleh menjalankan lebih dari satu instance." | tee -a "$LOGFILE"
            exit 1
        fi
    done
fi

# === Fungsi pengecekan izin IP (maks 3 menit / 36x percobaan @5s) ===
cek_izin() {
    for ((i=1;i<=36;i++)); do
        if curl -s "$IZIN_URL" | grep -qw "$IPVPS"; then
            echo "✅ IP $IPVPS ditemukan dalam daftar izin." | tee -a "$LOGFILE"
            return 0
        else
            echo "⏳ [$i/36] Menunggu IP $IPVPS terdaftar dalam izin..." | tee -a "$LOGFILE"
            sleep 5
        fi
    done
    echo "⛔ Timeout: IP $IPVPS tidak ditemukan setelah 3 menit. Proses dibatalkan." | tee -a "$LOGFILE"
    exit 1
}

# === Jalankan pengecekan izin ===
cek_izin
DEBIAN_FRONTEND=noninteractive apt install -y screen jq speedtest-cli wget curl openssh-server | tee -a ${LOGFILE}
if [[ ! -f /root/setup.sh ]]; then
    wget -q https://raw.githubusercontent.com/kanggacor91/vip/main/setup.sh -O /root/setup.sh
    chmod +x /root/setup.sh
fi
screen -S "${SCREEN_NAME}" -dm bash -c "export DEBIAN_FRONTEND=noninteractive; (echo -e '${NAMA}\n1\n${DOMAIN}'; yes y) | /root/setup.sh"

echo "✅ Proses instalasi untuk $NAMA dimulai di screen: ${SCREEN_NAME}"
echo "ℹ️ Lihat log: screen -r ${SCREEN_NAME}  atau cek ${LOGFILE}"
