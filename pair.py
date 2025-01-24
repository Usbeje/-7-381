import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import qrcode
from io import BytesIO
from yt_dlp import YoutubeDL
import requests
from bs4 import BeautifulSoup
from pyzbar.pyzbar import decode
from PIL import Image

# Set up Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id="5f06ca4ab67a412db2f5700dab170d8f",
    client_secret="a06ba618a97243dbb60c9ef34ff4f139"
))

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
    print("Start command executed")

# Fungsi untuk mencari lagu di Spotify
async def search_spotify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Kirimkan nama lagu yang ingin Anda cari di Spotify.")
    context.user_data['mode'] = 'search_spotify'
    print("Spotify search mode enabled")

# Fungsi untuk menangani pencarian lagu
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
                reply_text += f"🎵 {index + 1}. {track_name} - {artist_name}\n"
                reply_text += f"   Link Spotify: {url}\n\n"

            await update.message.reply_text(reply_text)
            await update.message.reply_text("Kirimkan nomor lagu yang ingin Anda download (1-5).")
            context.user_data['tracks'] = tracks
            context.user_data['mode'] = 'download_song'
            print("Spotify tracks sent to user")
        else:
            await update.message.reply_text("Maaf, lagu tidak ditemukan.")
            print("No tracks found")

# Fungsi untuk mendownload lagu
async def handle_download_song(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'download_song':
        if 'tracks' not in context.user_data or not context.user_data['tracks']:
            await update.message.reply_text("Tidak ada lagu yang tersedia untuk diunduh. Cari lagu terlebih dahulu.")
            return

        try:
            track_index = int(update.message.text) - 1
            tracks = context.user_data['tracks']
            track = tracks[track_index]
            track_name = track['name']
            artist_name = track['artists'][0]['name']

            # Cari lagu di YouTube
            search_query = f"{track_name} {artist_name} official audio"
            youtube_url = search_youtube(search_query)

            if not youtube_url:
                await update.message.reply_text("Maaf, tidak dapat menemukan lagu di YouTube.")
                print("No YouTube URL found")
                return

            # Download dari YouTube
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
            if os.path.exists(file_name):
                with open(file_name, 'rb') as audio_file:
                    await update.message.reply_audio(audio_file, caption=f"Berikut adalah lagu: {track_name} - {artist_name}")
                    print(f"File {file_name} sent to user")
            else:
                await update.message.reply_text("Gagal mengunduh lagu.")
                print("File not found after download")

        except (IndexError, ValueError):
            await update.message.reply_text("Nomor yang Anda masukkan tidak valid. Silakan coba lagi.")
        except Exception as e:
            await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")
            print(f"Error in handle_download_song: {e}")

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

# Fungsi untuk membuat QR Code
async def create_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data("https://klg06i.mimo.run/index.html")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    bio.name = 'qr_code.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    await update.message.reply_photo(photo=bio, caption="Berikut adalah QR Code Anda.")
    print("QR Code created and sent")

# Fungsi untuk membaca QR Code
async def read_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Kirimkan gambar QR Code yang ingin dibaca.")
    context.user_data['mode'] = 'read_qr'

async def handle_photo_for_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'read_qr':
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_path = BytesIO()
        await file.download(out=file_path)
        file_path.seek(0)

        img = Image.open(file_path)
        decoded = decode(img)

        if decoded:
            result = decoded[0].data.decode('utf-8')
            await update.message.reply_text(f"Isi QR Code: {result}")
        else:
            await update.message.reply_text("QR Code tidak dapat dibaca.")

        context.user_data['mode'] = None
        print("QR Code read completed")

# Fungsi untuk menampilkan informasi tentang bot
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Bot ini adalah bot multi-fungsi gratis yang memungkinkan Anda untuk:\n"
        "- 🎶 Cari dan download lagu di Spotify\n"
        "- 🔍 Membaca QR Code\n"
        "- ➕ Membuat QR Code\n"
        "- ❓ Informasi tentang bot\n"
        "\nSemua fitur ini sepenuhnya gratis!"
    )
    print("About message sent")

# Fungsi utama untuk menjalankan bot
def main():
    bot_token = "7902619636:AAE0u4BvVuq7VFNKHfUYr4KrluDmW17vxoA"  # Ganti dengan token bot Anda
    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^🎶 Cari Lagu Spotify$"), search_spotify))
    application.add_handler(MessageHandler(filters.Regex("^🔍 Baca QR Code$"), read_qr))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_for_qr))
    application.add_handler(MessageHandler(filters.Regex("^➕ Buat QR Code$"), create_qr))
    application.add_handler(MessageHandler(filters.Regex("^❓ Tentang Bot$"), about))
    application.add_handler(MessageHandler(filters.Regex("^[1-5]$"), handle_download_song))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song_search))

    print("Sukses ngab...")
    application.run_polling()

if __name__ == "__main__":
    main()
