Perbaikan pada Dockerfile:
- Menambahkan langkah yang lebih robust di stage builder untuk memastikan:
  - file arsip didownload dan diekstrak,
  - direktori hasil ekstraksi dideteksi,
  - binary krig-miner dicari di dalam hasil ekstraksi dan dipindahkan ke /opt/krig-miner/krig-miner,
  - build gagal dengan pesan jelas jika binary tidak ditemukan.
- Menyesuaikan COPY di stage runtime agar mengambil binary dari /opt/krig-miner/krig-miner.

Langkah selanjutnya:
1. Build image:
   docker build -t krig-miner-app:1.5.9 .

2. Jika build sukses, tag & push ke registry Anda:
   docker tag krig-miner-app:1.5.9 100927124398.dkr.ecr.us-east-2.amazonaws.com/palimpangin:latest
   docker push 100927124398.dkr.ecr.us-east-2.amazonaws.com/palimpangin:latest

Catatan: saya menambahkan "findutils" di builder agar perintah find tersedia pada beberapa base image.
