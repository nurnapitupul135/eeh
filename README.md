Ringkasan
=========
Proyek ini membungkus krig-miner dalam image docker minimal dan menambahkan supervisor Python (app.py) untuk:
- Menyediakan healthcheck HTTP lokal (127.0.0.1:8080)
- Menangani sinyal SIGTERM/SIGINT dengan rapi
- Restart otomatis dengan backoff (konfigurasi lewat env)

Build
-----
docker build -t krig-miner-app:1.5.9 .

Run (contoh dengan flag keamanan yang direkomendasikan)
-------------------------------------------------------
docker run -d --name krig-miner \
  --read-only \
  --tmpfs /tmp:rw,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --pids-limit 200 \
  --memory 1g \
  --cpus 1.0 \
  --network bridge \
  -e MINER_URL="stratum+ssl://prl-sg.kryptex.network:8048" \
  -e MINER_USER="prl1pjp3jd7ue653f6zyrn9ewwu7lalw538kn5w2l4lekv0g3nxqlj23qnwg6g0/olehudin" \
  krig-miner-app:1.5.9

Kesehatan & debug
-----------------
- Healthcheck lokal: dari host Anda tidak bisa mengakses 127.0.0.1 dalam container; untuk memeriksa status: 
  - jalankan `docker logs -f krig-miner` untuk melihat output miner.
  - Atau expose port health jika mau (ubah HEALTH_HOST/HEALTH_PORT di Dockerfile / app.py).

Catatan keamanan penting
------------------------
1. Verifikasi binary: unduh checksum/GPG (jika tersedia) sebelum menjalankan. Saya tidak menambahkan pemeriksaan checksum otomatis karena file rilis upstream mungkin tidak menyediakan checksum/signature di URL yang sama.
2. Scan binary dengan AV/online-scanner bila perlu.
3. Jalankan di host terisolasi (VM) atau dengan pembatasan jaringan.
4. Untuk isolasi jaringan maksimal: gunakan --network=none dan konfigurasikan sidecar proxy yang hanya mengizinkan ke pool tertentu.
