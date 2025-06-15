#!/bin/bash
NAMA=$1
DOMAIN=$2
LOGFILE="/root/log_install_${NAMA}.log"

# Install dependensi
apt install -y screen jq speedtest-cli wget curl | tee ${LOGFILE}

# Ambil setup.sh jika belum ada
if [[ ! -f /root/setup.sh ]]; then
    wget -q https://raw.githubusercontent.com/kanggacor91/vip/main/setup.sh -O /root/setup.sh
    chmod +x /root/setup.sh
fi

# Jalankan setup.sh di dalam screen
screen -S install_${NAMA} -dm bash -c "echo -e '${NAMA}\n1\n${DOMAIN}\ny' | /root/setup.sh" | tee -a ${LOGFILE}

# Info ke user
echo "✅ Proses instalasi untuk $NAMA dimulai di screen: install_${NAMA}"
echo "ℹ️ Lihat log: screen -r install_${NAMA}  atau cek ${LOGFILE}"
