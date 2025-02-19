import os, requests, random, datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Import daftar dari file eksternal
from data_lists import list_dzikir, list_renungan

# Load token dari .env
load_dotenv()
bot_token = os.getenv('BOT_TOKEN')

# Inisialisasi bot dengan Application
app = Application.builder().token(bot_token).build()

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Halo! Selamat datang di bot telegram saya.")

async def info(update: Update, context: CallbackContext):
    print("Command /info dipanggil")
    text_info = "Informasi Bot"
    await update.message.reply_text(text_info)

# Fungsi untuk mendapatkan kode kota berdasarkan nama kota
def get_kode_kota(nama_kota):
    url = f"https://api.myquran.com/v2/sholat/kota/cari/{nama_kota}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("status") and "data" in data:
            hasil = data["data"]
            if len(hasil) == 1:  # Jika hanya ada satu kota
                return hasil[0]["id"], hasil[0]["lokasi"]
            elif len(hasil) > 1:  # Jika ada lebih dari satu kota
                return [(kota["id"], kota["lokasi"]) for kota in hasil]
        return None
    except requests.exceptions.RequestException:
        return None

# Fungsi untuk mendapatkan jadwal sholat secara lengkap berdasarkan kode kota dan tanggal
def get_jadwal_sholat(kode_kota, tanggal):
    url = f"https://api.myquran.com/v2/sholat/jadwal/{kode_kota}/{tanggal}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data["status"]:
            jadwal = data["data"]["jadwal"]
            return (
                f"Jadwal Sholat di {data['data']['lokasi']} ({data['data']['daerah']}) pada {jadwal['tanggal']}:\n\n"
                f"🕌 Imsak: {jadwal['imsak']}\n"
                f"🕌 Subuh: {jadwal['subuh']}\n"
                f"🌅 Terbit: {jadwal['terbit']}\n"
                f"🌞 Dhuha: {jadwal['dhuha']}\n"
                f"🕌 Dzuhur: {jadwal['dzuhur']}\n"
                f"🕌 Ashar: {jadwal['ashar']}\n"
                f"🌇 Maghrib: {jadwal['maghrib']}\n"
                f"🌙 Isya: {jadwal['isya']}"
            )
        return "Jadwal sholat tidak ditemukan."
    except requests.exceptions.RequestException:
        return "Gagal mengambil data jadwal sholat."

# Fungsi untuk mengambil data Asmaul Husna berdasarkan nomor
def get_husna_by_number(nomor: int) -> str:
    url = f"https://api.myquran.com/v2/husna/{nomor}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "data" in data:
            husna = data["data"]
            message = (
                f"Nomor: {husna['id']}\n"
                f"Nama: {husna['indo']} ({husna['arab']})\n"
                f"Latin: {husna['latin']}"
            )
            return message
        else:
            return "Data Asmaul Husna tidak ditemukan."
    except requests.exceptions.RequestException as e:
        return f"Terjadi kesalahan: {e}"


# Fungsi untuk mengambil semua data Asmaul Husna
def get_all_husna() -> str:
    url = "https://api.myquran.com/v2/husna/semua"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "data" in data:
            husna_list = data["data"]
            messages = []
            for husna in husna_list:
                pesan = (
                    f"Nomor: {husna['id']}\n"
                    f"Nama: {husna['indo']} ({husna['arab']})\n"
                    f"Latin: {husna['latin']}\n"
                )
                messages.append(pesan)
            # Gabungkan semua pesan dengan pemisah baris ganda
            return "\n".join(messages)
        else:
            return "Data Asmaul Husna tidak ditemukan."
    except requests.exceptions.RequestException as e:
        return f"Terjadi kesalahan: {e}"

# Fungsi untuk mendapatkan daftar semua surat
def get_all_surahs():
    url = "https://api.myquran.com/v2/quran/surat/semua"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "data" in data:
            return data["data"]
        else:
            return None
    except requests.exceptions.RequestException:
        return None

# Fungsi untuk mendapatkan informasi surat berdasarkan nomor
def get_surat_by_number(number: int):
    url = f"https://api.myquran.com/v2/quran/surat/{number}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "data" in data:
            return data["data"]
        else:
            return None
    except requests.exceptions.RequestException:
        return None

# Fungsi untuk mendapatkan ayat berdasarkan nomor surat dan nomor ayat
def get_ayat_by_number(surat_number: int, ayat_number: int):
    url = f"https://api.myquran.com/v2/quran/ayat/{surat_number}/{ayat_number}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "data" in data:
            # Data ayat biasanya berupa list, ambil elemen pertama
            if isinstance(data["data"], list) and len(data["data"]) > 0:
                return data["data"][0]
            else:
                return None
        else:
            return None
    except requests.exceptions.RequestException:
        return None

# Command /jadwalsholat: tampilkan jadwal sholat lengkap
async def jadwal_sholat(update: Update, context: CallbackContext):
    print("Command /jadwalsholat dipanggil")
    if not context.args:
        await update.message.reply_text("Gunakan format: `/jadwalsholat [nama_kota]`", parse_mode="Markdown")
        return

    nama_kota = context.args[0]
    tanggal = datetime.datetime.today().strftime('%Y-%m-%d')
    hasil = get_kode_kota(nama_kota)
    if not hasil:
        await update.message.reply_text("Kota tidak ditemukan. Coba masukkan nama kota yang lebih spesifik.")
        return

    # Jika ada lebih dari satu hasil, tampilkan pilihan
    if isinstance(hasil, list):
        pilihan_kota = "\n".join([f"{i+1}. {kota[1]} (ID: {kota[0]})" for i, kota in enumerate(hasil)])
        await update.message.reply_text(
            f"Ditemukan beberapa hasil untuk `{nama_kota}`:\n\n{pilihan_kota}\n\n"
            "Silakan pilih kota dengan mengetik ID kota (misal: `1609`)",
            parse_mode="Markdown"
        )
        context.user_data["pending_cities"] = hasil
        context.user_data["pending_tanggal"] = tanggal
        return

    # Jika hanya satu hasil
    kode_kota, lokasi = hasil
    hasil_jadwal = get_jadwal_sholat(kode_kota, tanggal)
    await update.message.reply_text(hasil_jadwal)

# Command /maghrib: tampilkan waktu Maghrib saja
async def maghrib(update: Update, context: CallbackContext):
    print("Command /maghrib dipanggil")
    if not context.args:
        await update.message.reply_text("Gunakan format: `/maghrib [nama_kota]`", parse_mode="Markdown")
        return

    nama_kota = context.args[0]
    tanggal = datetime.datetime.today().strftime('%Y-%m-%d')
    hasil = get_kode_kota(nama_kota)
    if not hasil:
        await update.message.reply_text("Kota tidak ditemukan. Coba masukkan nama kota yang lebih spesifik.")
        return

    # Jika ada lebih dari satu hasil, tampilkan pilihan dan simpan data pending khusus untuk maghrib
    if isinstance(hasil, list):
        pilihan_kota = "\n".join([f"{i+1}. {kota[1]} (ID: {kota[0]})" for i, kota in enumerate(hasil)])
        await update.message.reply_text(
            f"Ditemukan beberapa hasil untuk `{nama_kota}`:\n\n{pilihan_kota}\n\n"
            "Silakan pilih kota dengan mengetik ID kota (misal: `1609`)",
            parse_mode="Markdown"
        )
        context.user_data["pending_maghrib"] = hasil
        context.user_data["pending_maghrib_tanggal"] = tanggal
        return

    # Jika hanya satu hasil, ambil waktu Maghrib saja
    kode_kota, lokasi = hasil
    url = f"https://api.myquran.com/v2/sholat/jadwal/{kode_kota}/{tanggal}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data["status"]:
            jadwal = data["data"]["jadwal"]
            maghrib_time = jadwal.get("maghrib", "Tidak ada data")
            lokasi = data["data"]["lokasi"]
            daerah = data["data"]["daerah"]
            await update.message.reply_text(
                f"Waktu Maghrib di {lokasi} ({daerah}) pada {jadwal['tanggal']} adalah {maghrib_time}"
            )
        else:
            await update.message.reply_text("Jadwal sholat tidak ditemukan.")
    except requests.exceptions.RequestException:
        await update.message.reply_text("Gagal mengambil data jadwal sholat.")

# Command /dzikir: menggunakan list dari file eksternal
async def dzikir(update: Update, context: CallbackContext):
    print("Command /dzikir dipanggil")
    await update.message.reply_text(random.choice(list_dzikir))

# Command /renungan: menggunakan list dari file eksternal
async def renungan(update: Update, context: CallbackContext):
    print("Command /renungan dipanggil")
    await update.message.reply_text(random.choice(list_renungan))

# Command /husna: menampilkan Asmaul Husna berdasarkan nomor
async def husna(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Gunakan format: `/husna [nomor]` (contoh: `/husna 5`)", parse_mode="Markdown")
        return
    try:
        nomor = int(context.args[0])
        if nomor < 1 or nomor > 99:
            await update.message.reply_text("Nomor tidak valid. Masukkan angka antara 1 hingga 99.")
            return
    except ValueError:
        await update.message.reply_text("Nomor tidak valid. Masukkan angka.")
        return

    pesan = get_husna_by_number(nomor)
    await update.message.reply_text(pesan)


# Command /allhusna: menampilkan semua Asmaul Husna
async def alhusna(update: Update, context: CallbackContext):
    pesan = get_all_husna()
    # Telegram membatasi pesan sekitar 4096 karakter, jadi kita pecah jika perlu
    if len(pesan) > 4000:
        parts = [pesan[i:i+4000] for i in range(0, len(pesan), 4000)]
        for part in parts:
            await update.message.reply_text(part)
    else:
        await update.message.reply_text(pesan)

# Command /listsurat: Menampilkan daftar semua surat
async def listsurat(update: Update, context: CallbackContext):
    surahs = get_all_surahs()
    if surahs:
        message = "Daftar Surat Al-Quran (Nomor 1-114):\n\n"
        for i, surat in enumerate(surahs):
            message += f"{i+1}. {surat['name_id']}\n"
        # Telegram membatasi panjang pesan (sekitar 4096 karakter), jadi pecah jika perlu
        if len(message) > 4000:
            parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
            for part in parts:
                await update.message.reply_text(part)
        else:
            await update.message.reply_text(message)
    else:
        await update.message.reply_text("Gagal mendapatkan daftar surat.")

# Command /surah: Menampilkan informasi detail surat berdasarkan nomor
async def surah(update: Update, context: CallbackContext):
    if not context.args:
        await update.message.reply_text("Gunakan format: `/surah [nomor]` (contoh: `/surah 1`)", parse_mode="Markdown")
        return
    try:
        number = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Nomor surat harus berupa angka.")
        return
    if number < 1 or number > 114:
        await update.message.reply_text("Nomor surat tidak valid. Masukkan antara 1 hingga 114.")
        return
    data = get_surat_by_number(number)
    if data:
        message = (
            f"Informasi Surat Al-Quran Nomor {number}:\n\n"
            f"Nama Surat: {data['name_id']} ({data['name_short']})\n"
            f"Nama Panjang: {data['name_long']}\n"
            f"Arti: {data['translation_id']}\n"
            f"Jumlah Ayat: {data['number_of_verses']}\n"
            f"Jenis Wahyu: {data['revelation_id']}\n"
            f"Tafsir: {data['tafsir']}\n"
            f"Audio URL: {data['audio_url']}"
        )
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Data surat tidak ditemukan.")

# Command /ayat: Menampilkan informasi ayat berdasarkan nomor surat dan nomor ayat
async def ayat(update: Update, context: CallbackContext):
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Gunakan format: `/ayat [nomor_surat] [nomor_ayat]` (contoh: `/ayat 1 1`)", parse_mode="Markdown")
        return
    try:
        surat_number = int(context.args[0])
        ayat_number = int(context.args[1])
    except ValueError:
        await update.message.reply_text("Nomor surat dan ayat harus berupa angka.")
        return
    data = get_ayat_by_number(surat_number, ayat_number)
    if data:
        message = (
            f"Ayat {ayat_number} dari Surat {surat_number}:\n\n"
            f"Ayat (Arab): {data['arab']}\n"
            f"Ayat (Latin): {data['latin']}\n"
            f"Terjemahan: {data['text']}\n"
            f"Audio URL: {data['audio']}"
        )
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Data ayat tidak ditemukan.")
            
# Handler untuk menangani input numerik sebagai pilihan kota (untuk kedua command)
async def select_city(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    # Prioritaskan pending untuk /maghrib
    if "pending_maghrib" in context.user_data:
        pending = context.user_data["pending_maghrib"]
        matching = [city for city in pending if city[0] == text]
        if matching:
            kode_kota, lokasi = matching[0]
            tanggal = context.user_data.get("pending_maghrib_tanggal", datetime.datetime.today().strftime('%Y-%m-%d'))
            url = f"https://api.myquran.com/v2/sholat/jadwal/{kode_kota}/{tanggal}"
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
                if data["status"]:
                    jadwal = data["data"]["jadwal"]
                    maghrib_time = jadwal.get("maghrib", "Tidak ada data")
                    lokasi = data["data"]["lokasi"]
                    daerah = data["data"]["daerah"]
                    await update.message.reply_text(
                        f"Waktu Maghrib di {lokasi} ({daerah}) pada {jadwal['tanggal']} adalah {maghrib_time}"
                    )
                else:
                    await update.message.reply_text("Jadwal sholat tidak ditemukan.")
            except requests.exceptions.RequestException:
                await update.message.reply_text("Gagal mengambil data jadwal sholat.")
            context.user_data.pop("pending_maghrib")
            context.user_data.pop("pending_maghrib_tanggal", None)
            context.user_data["skip_echo"] = True
            return
    # Jika tidak ada pending maghrib, periksa pending untuk jadwalsholat
    if "pending_cities" in context.user_data:
        pending = context.user_data["pending_cities"]
        matching = [city for city in pending if city[0] == text]
        if matching:
            kode_kota, lokasi = matching[0]
            tanggal = context.user_data.get("pending_tanggal", datetime.datetime.today().strftime('%Y-%m-%d'))
            hasil_jadwal = get_jadwal_sholat(kode_kota, tanggal)
            await update.message.reply_text(hasil_jadwal)
            context.user_data.pop("pending_cities")
            context.user_data.pop("pending_tanggal", None)
            context.user_data["skip_echo"] = True
        else:
            await update.message.reply_text("ID kota tidak valid. Silakan coba lagi.")

# Handler echo untuk pesan selain perintah
async def echo(update: Update, context: CallbackContext):
    if context.user_data.pop("skip_echo", False):
        return
    message = update.message.text
    await update.message.reply_text(message)
    print(f"Pesan dari user: {message}")

# Daftarkan handler dengan urutan yang disarankan
app.add_handler(CommandHandler('start', start))
app.add_handler(CommandHandler('info', info))
app.add_handler(CommandHandler('jadwalsholat', jadwal_sholat))
app.add_handler(CommandHandler('maghrib', maghrib))
app.add_handler(CommandHandler('dzikir', dzikir))
app.add_handler(CommandHandler('renungan', renungan))
app.add_handler(CommandHandler('husna', husna))
app.add_handler(CommandHandler('alhusna', alhusna))
app.add_handler(CommandHandler('listsurat', listsurat))
app.add_handler(CommandHandler('surah', surah))
app.add_handler(CommandHandler('ayat', ayat))
app.add_handler(MessageHandler(filters.Regex(r'^\d+$'), select_city))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

if __name__ == '__main__':
    print("Bot Telegram terhubung...")
    app.run_polling()
