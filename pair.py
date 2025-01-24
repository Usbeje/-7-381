from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import qrcode
from io import BytesIO
from pyzbar.pyzbar import decode
from PIL import Image
from yt_dlp import YoutubeDL
import requests
from bs4 import BeautifulSoup

# Set up Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="5f06ca4ab67a412db2f5700dab170d8f", client_secret="a06ba618a97243dbb60c9ef34ff4f139"))

# Fungsi untuk memulai bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        ["💬 Chat dengan AI", "🔍 Baca QR Code", "➕ Buat QR Code", "🎶 Cari Lagu Spotify"],
        ["❓ Tentang Bot"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Selamat datang di Bot AI Gratis! Pilih menu di bawah:",
        reply_markup=reply_markup,
    )

# Fungsi untuk mencari lagu di Spotify
async def search_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Kirimkan nama lagu yang ingin Anda cari di Spotify.")
    context.user_data['mode'] = 'search_spotify'

async def handle_song_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'search_spotify':
        song_name = update.message.text
        results = sp.search(q=song_name, limit=5, type="track")
        tracks = results['tracks']['items']
        
        if tracks:
            reply_text = "Hasil pencarian lagu:\n"
            for index, track in enumerate(tracks):
                track_name = track['name']
                artist_name = track['artists'][0]['name']
                url = track['external_urls']['spotify']
                popularity = track['popularity']
                album_name = track['album']['name']
                release_date = track['album']['release_date']

                reply_text += f"🎵 {index + 1}. {track_name} - {artist_name}\n"
                reply_text += f"   Album: {album_name}\n"
                reply_text += f"   Tanggal Rilis: {release_date}\n"
                reply_text += f"   Popularitas: {popularity}\n"
                reply_text += f"   Link Spotify: {url}\n\n"

            await update.message.reply_text(reply_text)
            await update.message.reply_text("Kirimkan nomor lagu yang ingin Anda download (1-5).")
            context.user_data['tracks'] = tracks  # Simpan track untuk di-download
            context.user_data['mode'] = 'download_song'
        else:
            await update.message.reply_text("Maaf, lagu tidak ditemukan.")

# Fungsi untuk mendownload lagu dari YouTube berdasarkan data Spotify
async def handle_download_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'download_song':
        try:
            track_index = int(update.message.text) - 1
            tracks = context.user_data['tracks']
            track = tracks[track_index]
            track_name = track['name']
            artist_name = track['artists'][0]['name']

            # Cari di YouTube menggunakan judul lagu dan artis
            search_query = f"{track_name} {artist_name} official audio"
            youtube_url = search_youtube(search_query)

            if not youtube_url:
                await update.message.reply_text("Maaf, tidak dapat menemukan lagu di YouTube.")
                return

            # Download dari YouTube menggunakan yt_dlp
            file_name = f"{track_name} - {artist_name}.mp3"
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': file_name,
            }

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])

            # Kirim file ke pengguna
            with open(file_name, 'rb') as audio_file:
                await update.message.reply_audio(audio_file, caption=f"Berikut adalah lagu: {track_name} - {artist_name}")

        except (IndexError, ValueError):
            await update.message.reply_text("Nomor yang Anda masukkan tidak valid. Silakan coba lagi.")
        except Exception as e:
            await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")

        # Reset mode ke menu utama
        context.user_data['mode'] = None
        await start(update, context)

# Fungsi untuk mencari URL YouTube
def search_youtube(query):
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all('a', href=True)

    for result in results:
        if '/watch?' in result['href']:
            return f"https://www.youtube.com{result['href']}"

    return None

# Fungsi untuk membuat QR Code (teks langsung ke link)
async def create_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Kirimkan teks yang ingin dijadikan tautan.")
    context.user_data['mode'] = 'create_qr'

async def handle_text_for_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'create_qr':
        text = update.message.text
        await update.message.reply_text(
            f"Berikut adalah tautan Anda: [Klik di sini]({text})",
            parse_mode="Markdown"
        )
        context.user_data['mode'] = None
        await start(update, context)

# Fungsi untuk membaca QR Code
async def read_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Kirimkan gambar QR Code yang ingin dibaca.")
    context.user_data['mode'] = 'read_qr'

async def handle_photo_for_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'read_qr':
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = await file.download_as_bytearray()

        # Membaca QR Code
        image = Image.open(BytesIO(file_path))
        decoded_data = decode(image)

        if decoded_data:
            result = decoded_data[0].data.decode('utf-8')
            await update.message.reply_text(f"Isi QR Code: {result}")
        else:
            await update.message.reply_text("Tidak dapat membaca QR Code.")

        context.user_data['mode'] = None
        await start(update, context)

# Fungsi untuk menampilkan informasi tentang bot
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Bot ini adalah bot multi-fungsi gratis yang memungkinkan Anda untuk:\n"
        "- 💬 Berbicara dengan AI (seperti ChatGPT)\n"
        "- 🔍 Membaca QR Code\n"
        "- ➕ Membuat QR Code\n"
        "- 🎶 Mencari dan mendownload lagu di Spotify\n"
        "\nSemua fitur ini sepenuhnya gratis!"
    )
    await start(update, context)

# Fungsi utama untuk menjalankan bot
def main():
    bot_token = "7902619636:AAE0u4BvVuq7VFNKHfUYr4KrluDmW17vxoA"  # Ganti dengan token bot Anda
    application = ApplicationBuilder().token(bot_token).build()

    # Tambahkan handler
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^➕ Buat QR Code$"), create_qr))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_for_qr))
    application.add_handler(MessageHandler(filters.Regex("^🎶 Cari Lagu Spotify$"), search_spotify))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song_search))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download_song))

    # Jalankan bot
    application.run_polling()

if __name__ == "__main__":
    main()
