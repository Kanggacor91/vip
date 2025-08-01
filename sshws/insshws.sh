#!/bin/bash
# Proxy For Edukasi & Imclass
file_path="/etc/handeling"

# Cek apakah file ada
if [ ! -f "$file_path" ]; then
    # Jika file tidak ada, buat file dan isi dengan dua baris
    echo -e "KanggacorVPn\nBlue" | sudo tee "$file_path" > /dev/null
    echo "File '$file_path' berhasil dibuat."
else
    # Jika file ada, cek apakah isinya kosong
    if [ ! -s "$file_path" ]; then
        # Jika file ada tetapi kosong, isi dengan dua baris
        echo -e "KanggacorVPn\nBlue" | sudo tee "$file_path" > /dev/null
        echo "File '$file_path' kosong dan telah diisi."
    else
        # Jika file ada dan berisi data, tidak lakukan apapun
        echo "File '$file_path' sudah ada dan berisi data."
    fi
fi
# Link Hosting Kalian
rm -- "$0"
curl -sS ipv4.icanhazip.com > /usr/bin/.ipvps
REPOws="https://raw.githubusercontent.com/Diah082/Ws-Epro/refs/heads/main/"
wget -O /usr/bin/ws "${REPOws}ws"
wget -O /usr/bin/config.conf "${REPOws}config.conf"
wget -O /etc/systemd/system/ws.service "${REPOws}ws.service"
chmod +x /usr/bin/ws
systemctl daemon-reload
systemctl enable ws.service
systemctl start ws.service
systemctl restart ws.service

