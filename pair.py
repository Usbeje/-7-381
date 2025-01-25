from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from yt_dlp import YoutubeDL
import requests
from bs4 import BeautifulSoup
import cv2
import numpy as np
from io import BytesIO

# Fungsi untuk memulai bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [["🎶 Cari Lagu", "🔍 Baca QR Code", "➕ Buat QR Code", "❓ Tentang Bot"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Selamat datang di Bot AI Gratis! Pilih menu di bawah:", reply_markup=reply_markup)

# Fungsi untuk membuat QR Code
async def create_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Silahkan pratinjau web saya: https://klg06i.mimo.run/index.html")

# Fungsi untuk membaca QR Code
async def read_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Kirimkan gambar QR Code yang ingin dibaca.")
    context.user_data['mode'] = 'read_qr'

async def handle_photo_for_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'read_qr':
        try:
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
        except Exception as e:
            await update.message.reply_text(f"Terjadi kesalahan: {e}")

        context.user_data['mode'] = None

# Fungsi untuk mencari lagu di YouTube
async def search_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Silahkan masukkan judul lagu dan artis, contoh: 'Cars Outside - James Arthur'")
    context.user_data['mode'] = 'youtube_search'

async def handle_song_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'youtube_search':
        search_query = update.message.text
        youtube_data = get_youtube_data(search_query)

        if youtube_data:
            title, views, url = youtube_data
            await update.message.reply_text(
                f"🎵 Lagu ditemukan:\n"
                f"   Judul: {title}\n"
                f"   Jumlah Tayangan: {views}\n"
                f"   URL: {url}\n\n"
                f"Apakah Anda ingin mendownload lagu ini? (Ketik 'Ya' atau 'Tidak')"
            )
            context.user_data['youtube_url'] = url
            context.user_data['mode'] = 'youtube_download'
        else:
            await update.message.reply_text("Maaf, lagu tidak ditemukan. Pastikan penulisan benar.")

async def handle_youtube_download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('mode') == 'youtube_download':
        response = update.message.text.lower()
        youtube_url = context.user_data.get('youtube_url')

        if response in ['ya', 'y']:
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
                    await update.message.reply_audio(audio_file, caption="Lagu berhasil didownload!")
            except Exception as e:
                await update.message.reply_text(f"Gagal mendownload lagu: {e}")
        elif response in ['tidak', 'no', 'n']:
            await update.message.reply_text("Download dibatalkan.")
        else:
            await update.message.reply_text("Respon tidak valid. Silakan ketik 'Ya' atau 'Tidak'.")

        context.user_data['mode'] = None

# Fungsi untuk mendapatkan data YouTube
def get_youtube_data(query):
    try:
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        response = requests.get(search_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.find_all('a', href=True, title=True)

        for result in results:
            if '/watch?' in result['href']:
                title = result['title']
                url = f"https://www.youtube.com{result['href']}"
                views = "Tidak diketahui"  # Bisa diperluas dengan scraping jumlah tayangan
                return title, views, url
    except Exception as e:
        print(f"Error saat mengambil data YouTube: {e}")
    return None

# Fungsi untuk menampilkan informasi tentang bot
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Bot ini adalah bot multi-fungsi gratis yang memungkinkan Anda untuk:\n"
        "- 🎶 Cari dan download lagu di YouTube\n"
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
    application.add_handler(MessageHandler(filters.Regex("^🎶 Cari Lagu$"), search_youtube))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song_search))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_download))
    application.add_handler(CommandHandler("about", about))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
