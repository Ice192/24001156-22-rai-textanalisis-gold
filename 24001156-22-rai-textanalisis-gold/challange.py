import io
from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import re
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
import sqlite3
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app, template_file='swagger.yml')

# Membaca file abuse menggunakan pandas dengan encoding latin1
abuse_df = pd.read_csv('data/abusive.csv', header=None, encoding='latin1')
abuse_words = abuse_df[0].tolist()

# Membaca file singkatan menggunakan pandas tanpa header dengan encoding latin1
singkatan_df = pd.read_csv('data/new_kamusalay.csv', header=None, encoding='latin1')
singkatan_df.columns = ['singkatan', 'kepanjangan']

# Membuat dictionary singkatan
singkatan_dict = dict(zip(singkatan_df['singkatan'], singkatan_df['kepanjangan']))

# Inisialisasi Stemmer dari Sastrawi
factory = StemmerFactory()
stemmer = factory.create_stemmer()

# Membuat atau menghubungkan ke database SQLite
conn = sqlite3.connect('processed_tweets.db')
c = conn.cursor()

# Membuat tabel untuk menyimpan tweet yang telah diproses
c.execute('''
CREATE TABLE IF NOT EXISTS processed_tweets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_tweet TEXT,
    processed_tweet TEXT
)
''')

# Menyimpan perubahan dan menutup koneksi
conn.commit()
conn.close()

# Fungsi untuk membersihkan teks dari karakter yang di-encode, escape sequences, dan karakter Unicode
def clean_text(text):
    # Menghapus karakter yang di-encode dengan format \xHH
    pattern_encoded = re.compile(r'\\x[0-9A-Fa-f]{2}')
    text = pattern_encoded.sub('', text)
    
    # Menghapus escape sequences seperti \n, \t, dll.
    pattern_escape = re.compile(r'\\n|\\t')
    text = pattern_escape.sub(' ', text)
    
    # Membersihkan karakter Unicode
    text_cleaned = text.encode('latin1', 'ignore').decode('utf-8', 'ignore')

     # Konversi teks menjadi lowercase
    text_cleaned = text_cleaned.lower()
    
    return text_cleaned.strip()

# Fungsi untuk menghapus kata-kata abuse dengan stemming
def remove_abuse(text, abuse_words, stemmer):
    words = text.split()
    cleaned_words = []
    for word in words:
        stemmed_word = stemmer.stem(word)
        if stemmed_word.lower() not in abuse_words:
            cleaned_words.append(word)
    return ' '.join(cleaned_words)

# Fungsi untuk mengganti singkatan
def replace_singkatan(text, singkatan_dict):
    words = text.split()
    for i in range(len(words)):
        word_lower = words[i].lower()
        if word_lower in singkatan_dict:
            words[i] = singkatan_dict[word_lower]
    return ' '.join(words)

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint untuk data original file tweet.csv
@app.route('/original_tweets', methods=['GET'])
def original_tweets():
    conn = sqlite3.connect('processed_tweets.db')
    c = conn.cursor()
    c.execute('SELECT original_tweet FROM processed_tweets')
    original_tweets = [row[0] for row in c.fetchall()]
    conn.commit()
    conn.close()
    
    return jsonify({'original_tweets': original_tweets})

# Endpoint untuk memproses file tweet.csv
@app.route('/process_tweets_file', methods=['GET'])
def process_tweets_file():
    # Membaca file tweet.csv menggunakan pandas
    tweets_df = pd.read_csv('data/data.csv', encoding='latin1')
    
    # Inisialisasi list untuk hasil proses
    original_tweets = []
    cleaned_tweets = []
    
    # Menyimpan hasil ke database SQLite
    conn = sqlite3.connect('processed_tweets.db')
    c = conn.cursor()

    # Proses setiap tweet dalam file
    for tweet in tweets_df['Tweet']:
        original_tweet = tweet

        # Menghilangkan text non-ASCII (seperti emoji)
        tweet = clean_text(tweet)

        # Mengganti singkatan
        tweet_cleaned = replace_singkatan(tweet, singkatan_dict)
        
        # Menghapus kata-kata abuse
        tweet_cleaned = remove_abuse(tweet_cleaned, abuse_words, stemmer)
        
        # Tambahkan hasil ke list
        original_tweets.append(original_tweet)
        cleaned_tweets.append(tweet_cleaned)
        
        # Masukkan hasil ke tabel processed_tweets
        c.execute('INSERT INTO processed_tweets (original_tweet, processed_tweet) VALUES (?, ?)', (original_tweet, tweet_cleaned))

    conn.commit()
    conn.close()

    # Kembalikan hasil dalam format JSON
    return jsonify({
        'original_tweets': original_tweets,
        'cleaned_tweets': cleaned_tweets
    })

@app.route('/tweet_text', methods=['GET', 'POST'])
def tweet_form():
    if request.method == 'POST':
        tweet = request.form.get('tweet')
        
        # Simpan original tweet
        original_tweet = tweet
        
        # Bersihkan teks dari karakter yang di-encode, escape sequences, karakter Unicode, dan konversi ke lowercase
        tweet = clean_text(tweet)
        
        # Mengganti singkatan
        tweet = replace_singkatan(tweet, singkatan_dict)
        
        # Menghapus kata-kata abuse
        tweet = remove_abuse(tweet, abuse_words, stemmer)
        
        # Simpan ke database
        conn = sqlite3.connect('processed_tweets.db')
        c = conn.cursor()
        c.execute('INSERT INTO processed_tweets (original_tweet, processed_tweet) VALUES (?, ?)', (original_tweet, tweet))
        conn.commit()
        conn.close()
        
        return render_template('tweet_form.html', original_tweet=original_tweet, processed_tweet=tweet)
    
    return render_template('tweet_form.html')

@app.route('/upload_process', methods=['GET', 'POST'])
def upload_process():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and file.filename.endswith('.csv'):
            # Membaca file CSV yang diunggah
            tweets_df = pd.read_csv(file, encoding='latin1')
            
            # Inisialisasi list untuk hasil proses
            original_tweets = []
            cleaned_tweets = []
            
            # Proses setiap tweet dalam file
            for tweet in tweets_df['Tweet']:
                original_tweet = tweet

                # Menghilangkan text non-ASCII (seperti emoji)
                tweet = clean_text(tweet)

                # Mengganti singkatan
                tweet_cleaned = replace_singkatan(tweet, singkatan_dict)
                
                # Menghapus kata-kata abuse
                tweet_cleaned = remove_abuse(tweet_cleaned, abuse_words, stemmer)
                
                # Tambahkan hasil ke list
                original_tweets.append(original_tweet)
                cleaned_tweets.append(tweet_cleaned)
            
            # Buat DataFrame baru untuk hasilnya
            result_df = pd.DataFrame({
                'original_tweet': original_tweets,
                'cleaned_tweet': cleaned_tweets
            })
            
            # Simpan DataFrame ke CSV dalam memory
            output = io.BytesIO()
            result_df.to_csv(output, index=False)
            output.seek(0)
            
            # Kembalikan file CSV untuk didownload
            return send_file(output, mimetype='text/csv', download_name='processed_tweets.csv', as_attachment=True)
        
        else:
            return jsonify({'error': 'Invalid file format'}), 400
    
    return render_template('upload_file.html')

if __name__ == '__main__':
    app.run(debug=True)
