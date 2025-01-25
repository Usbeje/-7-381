import cv2
import numpy as np
from io import BytesIO
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL
import requests
from bs4 import BeautifulSoup

# Fungsi untuk memulai bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        ["🔍 Cari Lagu Spotify", "🔍 Baca QR Code", "➕ Buat QR Code", "❓ Tentang Bot"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Selamat datang di Bot AI Gratis! Pilih menu di bawah:",
        reply_markup=reply_markup,
    )

# Fungsi untuk membuat QR Code
async def create_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Silahkan pratinjau web saya "https://klg06i.mimo.run/index.html"',
    )

# Fungsi untuk membaca QR Code menggunakan OpenCV
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

# Fungsi untuk mencari lagu di YouTube
async def search_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Ketik nama dan artis lagu seperti ini: 'nama lagu - nama artis'."
    )
    context.user_data['mode'] = 'search_youtube'

# Fungsi untuk menangani pencarian lagu di YouTube
async def handle_song_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'search_youtube':
        search_query = update.message.text
        youtube_data = fetch_youtube_data(search_query)

        if youtube_data:
            context.user_data['youtube_url'] = youtube_data['url']
            reply_text = (
                f"🎵 Judul Lagu: {youtube_data['title']}\n"
                f"🎤 Artis: {youtube_data['channel']}\n"
                f"👀 Jumlah Tayangan: {youtube_data['views']}\n"
                f"📅 Tanggal Rilis: {youtube_data['release_date']}\n"
                f"🔗 URL: {youtube_data['url']}\n\n"
                "Download lagu? (ya/tidak)"
            )
            await update.message.reply_text(reply_text)
            context.user_data['mode'] = 'download_youtube'
        else:
            await update.message.reply_text("Maaf, lagu tidak ditemukan.")

# Fungsi untuk mendownload lagu dari YouTube
async def handle_download_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'download_youtube':
        response = update.message.text.lower()

        if response in ['ya', 'y', 'iya']:
            youtube_url = context.user_data['youtube_url']
            await update.message.reply_text("Sedang mendownload lagu, mohon tunggu...")
            file_name = "downloaded_song.mp3"
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
                    await update.message.reply_audio(audio_file, caption="Lagu Anda telah selesai didownload!")
            except Exception as e:
                await update.message.reply_text(f"Gagal mendownload lagu: {e}")
        elif response in ['tidak', 't', 'no', 'n']:
            await update.message.reply_text("Download dibatalkan.")
        else:
            await update.message.reply_text("Respon tidak valid. Harap ketik 'ya' atau 'tidak'.")

        context.user_data['mode'] = None

# Fungsi untuk mencari data YouTube
def fetch_youtube_data(query):
    search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all('a', href=True, attrs={"title": True})

    if results:
        for result in results:
            if '/watch?' in result['href']:
                title = result['title']
                url = f"https://www.youtube.com{result['href']}"
                channel = "Channel tidak diketahui"
                views = "Tidak tersedia"
                release_date = "Tidak tersedia"
                # Informasi tambahan bisa ditambahkan di sini
                return {
                    "title": title,
                    "url": url,
                    "channel": channel,
                    "views": views,
                    "release_date": release_date,
                }
    return None

# Fungsi untuk menampilkan informasi tentang bot
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Bot ini adalah bot multi-fungsi gratis yang memungkinkan Anda untuk:\n"
        "- 🔍 Mencari dan download lagu dari YouTube\n"
        "- 🔍 Membaca QR Code\n"
        "- ➕ Membuat QR Code\n\nSemua fitur ini sepenuhnya gratis!"
    )

# Fungsi utama untuk menjalankan bot
def main():
    bot_token = "7244876078:AAFqabhDdpAQ7JwmEx7pxVyugoXrc7zLZXI"  # Ganti dengan token bot Anda
    application = ApplicationBuilder().token(bot_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex("^➕ Buat QR Code$"), create_qr))
    application.add_handler(MessageHandler(filters.Regex("^🔍 Baca QR Code$"), read_qr))
    application.add_handler(MessageHandler(filters.Regex("^🔍 Cari Lagu Spotify$"), search_youtube))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo_for_qr))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song_search))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_download_request))
    application.add_handler(CommandHandler("about", about))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
