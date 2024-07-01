# Tweet Processing API

Tweet Processing API adalah aplikasi Flask yang digunakan untuk memproses tweet dengan membersihkan teks, mengganti singkatan, dan menghapus kata-kata yang mengandung penyalahgunaan (abusive).

## Fitur

- Memproses file CSV yang berisi tweet.
- Mengganti singkatan dalam tweet.
- Menghapus kata-kata abusive dari tweet.
- Menyimpan tweet asli dan yang telah diproses ke dalam database SQLite.
- Mengunggah file CSV dan mengembalikan hasilnya dalam format CSV.

## Persyaratan

- Python 3.6 atau lebih baru
- Flask
- Pandas
- Sastrawi
- flasgger

## Instalasi

1. Kloning repositori ini:

    ```bash
    git clone https://github.com/username/tweet-processing-api.git
    cd tweet-processing-api
    ```

2. Buat virtual environment dan aktifkan:

    ```bash
    python -m venv venv
    source venv/bin/activate   # Pada Windows: venv\Scripts\activate
    ```

4. Buat database SQLite dan tabel yang diperlukan:

    ```bash
    python
    >>> import sqlite3
    >>> conn = sqlite3.connect('processed_tweets.db')
    >>> c = conn.cursor()
    >>> c.execute('''
    CREATE TABLE IF NOT EXISTS processed_tweets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_tweet TEXT,
        processed_tweet TEXT
    )
    ''')
    >>> conn.commit()
    >>> conn.close()
    ```

## Penggunaan

1. Jalankan aplikasi Flask:

    ```bash
    flask run
    ```

2. Buka browser dan akses `http://localhost:5000` untuk mengakses aplikasi.

### Endpoint API

#### `GET /original_tweets`

Mengembalikan daftar tweet asli yang telah disimpan di database.

#### `GET /process_tweets_file`

Memproses file `tweet.csv` dan mengembalikan tweet asli dan yang telah dibersihkan dalam format JSON.

#### `POST /tweet_text`

Memproses tweet yang dimasukkan melalui form dan mengembalikan hasilnya.

#### `POST /upload_process`

Mengunggah file CSV berisi tweet, memprosesnya, dan mengembalikan hasil dalam format CSV.

url -X POST -F "tweet=Ini adalah contoh tweet untuk diuji" http://localhost:5000/tweet_text
