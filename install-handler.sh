#!/bin/bash
NAMA=$1
DOMAIN=$2
LOGFILE="/root/log_install_${NAMA}.log"

# Install dependensi tanpa prompt interaktif
DEBIAN_FRONTEND=noninteractive apt install -y screen jq speedtest-cli wget curl openssh-server | tee ${LOGFILE}

# Ambil setup.sh jika belum ada
if [[ ! -f /root/setup.sh ]]; then
    wget -q https://raw.githubusercontent.com/kanggacor91/vip/main/setup.sh -O /root/setup.sh
    chmod +x /root/setup.sh
fi

# Jalankan setup.sh di dalam screen dengan input otomatis
screen -S install_${NAMA} -dm bash -c "export DEBIAN_FRONTEND=noninteractive; (echo -e '${NAMA}\n1\n${DOMAIN}'; yes y) | /root/setup.sh"

# Info ke user
echo "✅ Proses instalasi untuk $NAMA dimulai di screen: install_${NAMA}"
echo "ℹ️ Lihat log: screen -r install_${NAMA}  atau cek ${LOGFILE}"
