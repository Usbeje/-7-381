import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL
import requests
from bs4 import BeautifulSoup
import qrcode
from io import BytesIO
import cv2
import numpy as np

# Set up Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="5f06ca4ab67a412db2f5700dab170d8f", client_secret="a06ba618a97243dbb60c9ef34ff4f139"))

# Fungsi untuk memulai bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        ["🎶 Cari Lagu Spotify", "🔍 Baca QR Code", "➕ Buat QR Code", "❓ Tentang Bot"],
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
                release_date = track['album']['release_date']
                popularity = track['popularity']
                followers = sp.artist(track['artists'][0]['id'])['followers']['total']
                url = track['external_urls']['spotify']

                reply_text += (
                    f"🎵 {index + 1}. {track_name} - {artist_name}\n"
                    f"   Tanggal Rilis: {release_date}\n"
                    f"   Popularitas: {popularity}\n"
                    f"   Pengikut: {followers}\n"
                    f"   Link Spotify: {url}\n\n"
                )

            await update.message.reply_text(reply_text)
            await update.message.reply_text("Kirimkan nomor lagu yang ingin Anda cari di YouTube (1-5).")
            context.user_data['tracks'] = tracks
            context.user_data['mode'] = 'youtube_search'
        else:
            await update.message.reply_text("Maaf, lagu tidak ditemukan.")

async def handle_youtube_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'youtube_search':
        try:
            track_index = int(update.message.text) - 1
            tracks = context.user_data['tracks']
            track = tracks[track_index]
            track_name = track['name']
            artist_name = track['artists'][0]['name']

            await update.message.reply_text(
                f"Anda memilih lagu: {track_name} - {artist_name}\n"
                "Silakan masukkan nama dan judul lagu untuk mencari di YouTube."
            )
            context.user_data['track_info'] = f"{track_name} {artist_name}"
            context.user_data['mode'] = 'youtube_download'

        except (IndexError, ValueError):
            await update.message.reply_text("Nomor yang Anda masukkan tidak valid. Silakan coba lagi.")

async def handle_youtube_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'youtube_download':
        search_query = update.message.text
        youtube_url = search_youtube(search_query)

        if youtube_url:
            await update.message.reply_text(f"URL YouTube ditemukan: {youtube_url}")
            await update.message.reply_text("Sedang mendownload lagu, mohon tunggu...")
            file_name = f"{context.user_data['track_info']}.mp3"
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': file_name,
            }

            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.download([youtube_url])

                with open(file_name, 'rb') as audio_file:
                    await update.message.reply_audio(audio_file, caption=f"Lagu Anda: {context.user_data['track_info']}")
            except Exception as e:
                await update.message.reply_text(f"Gagal mendownload lagu: {e}")
        else:
            await update.message.reply_text("Maaf, tidak dapat menemukan URL YouTube.")

        context.user_data['mode'] = None

def search_youtube(query):
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all('a', href=True)

    for result in results:
        if '/watch?' in result['href']:
            return f"https://www.youtube.com{result['href']}"

    return None

# Fungsi untuk membuat QR Code
async def create_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    button = InlineKeyboardButton("Pratinjau Link", url="https://example.com")
    markup = InlineKeyboardMarkup([[button]])
    await update.message.reply_text("Berikut adalah link Anda:", reply_markup=markup)

# Fungsi untuk membaca QR Code
async def read_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Kirimkan gambar QR Code yang ingin dibaca.")
    context.user_data['mode'] = 'read_qr'

async def handle_photo_for_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'read_qr':
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = BytesIO()
        await file.download_to_memory(file_path)

        # Membaca QR Code menggunakan OpenCV
        file_path.seek(0)
        file_array = np.asarray(bytearray(file_path.read()), dtype=np.uint8)
        image = cv2.imdecode(file_array, cv2.IMREAD_COLOR)
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(image)

        if data:
            await update.message.reply_text(f"Isi QR Code: {data}")
        else:
            await update.message.reply_text("Tidak dapat membaca QR Code.")

        context.user_data['mode'] = None

# Fungsi tentang bot
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot ini adalah bot multi-fungsi gratis.")

# Fungsi utama untuk menjalankan bot
def main():
    bot_token = "7902619636:AAE0u4BvVuq7VFNKHfUYr4KrluDmW17vxoA"  # Ganti dengan token bot Anda
    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^🎶 Cari Lagu Spotify$"), search_spotify))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song_search))
    application.add_handler(MessageHandler(filters.Regex("^[1-5]$"), handle_youtube_search))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_download))
    application.add_handler(MessageHandler(filters.Regex("^➕ Buat QR Code$"), create_qr))
    application.add_handler(MessageHandler(filters.Regex("^🔍 Baca QR Code$"), read_qr))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_for_qr))
    application.add_handler(CommandHandler("about", about))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
