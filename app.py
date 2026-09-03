import json
import os
from dotenv import load_dotenv
import random
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
import urllib.parse
import urllib.request

app = Flask(__name__)
app.secret_key = "sporcu_hayat_gizli_anahtar"  # Session kullanabilmek için gereklidir

VERI_DOSYASI = "kullanicilar.json"
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def telegram_bildirim_gonder(mesaj):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode(
            {"chat_id": TELEGRAM_CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
        ).encode("utf-8")

        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=5) as response:
            print("Telegram Yanıtı:", response.read().decode("utf-8"))
    except Exception as e:
        print(f"Telegram Bildirim Hatası: {e}")


def verileri_oku():
    if not os.path.exists(VERI_DOSYASI):
        return {}
    with open(VERI_DOSYASI, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def verileri_kaydet(data):
    with open(VERI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


GOREVLER: list[dict[str, str]] = [
    {
        "hedef": "100 Metre Koşu!",
        "mesaj": (
            "Başlangıç için yeterli mi, eğer etkisi yoksa 500 metre koş. Şimdi hiç"
            " soğumadan 20 Şınav çek. Hazır mısın?"
        ),
    },
    {
        "hedef": "20 Mekik!",
        "mesaj": (
            "Karnın sızlamaya başladı mı? Harikasın, formunu hiç"
            " kaybetmiyorsun! 🔥 Sıradaki hedef: 30 Saniye Plank!"
        ),
    },
    {
        "hedef": "10 Squat!",
        "mesaj": (
            "Bacaklar zorlanmadıysa 30 squat yapabilirsin! 🚀 Şimdi 30"
            " saniye dinlen ve 10 Burpee(çömel,plank duruşu , şınav, zıpla) için hazırlan!"
        ),
    },
    {
        "hedef": "30 Saniye Wall Sit!",
        "mesaj": (
            "Duvarda oturur pozisyonda kal. Karnı ve bacakları zımba gibi yapan o antrenman"
            " bitti. Şimdi 15 Saniye dinlen ve 10 Şınav için hazırlan!"
        ),
    },
]


@app.route("/gorev-tamamla", methods=["POST"])
def gorev_tamamla():
    KULLANICILAR = verileri_oku()
    aktif_kullanici = session.get("kullanici_adi")

    if aktif_kullanici and aktif_kullanici in KULLANICILAR:
        KULLANICILAR[aktif_kullanici]["tamamlanan_gorevler"] = (
            KULLANICILAR[aktif_kullanici].get("tamamlanan_gorevler", 0) + 50
        )
        verileri_kaydet(KULLANICILAR)

    return redirect(url_for("index"))


@app.route("/", methods=["GET", "POST"])
def index():
    secilen_gorev = None
    if request.method == "POST":
        secilen_gorev = random.choice(GOREVLER)

    KULLANICILAR = verileri_oku()
    uye_sayisi = len(KULLANICILAR)

    return render_template(
        "index.html",
        gorev=secilen_gorev,
        uye_sayisi=uye_sayisi,
        kullanicilar=KULLANICILAR,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("esneme"))

    hata = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        KULLANICILAR = verileri_oku()

        if username in KULLANICILAR and check_password_hash(
            KULLANICILAR[username]["password"], password
        ):
            session["user_id"] = username
            session["kullanici_adi"] = username

            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("index"))
        else:
            hata = "Kullanıcı adı veya şifre hatalı!"

    return render_template("login.html", hata=hata)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("esneme"))

    hata = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        KULLANICILAR = verileri_oku()

        if not username or not password:
            hata = "Lütfen tüm alanları doldurun!"
        elif len(password) < 8:
            hata = "Şifreniz güvenlik nedeniyle en az 8 karakter olmalıdır!"
        elif username in KULLANICILAR:
            hata = "Bu kullanıcı adı zaten alınmış!"
        else:
            KULLANICILAR[username] = {
                "password": generate_password_hash(
                    password, method="pbkdf2:sha256"
                ),
                "tamamlanan_gorevler": 0,
            }
            verileri_kaydet(KULLANICILAR)

            # Oturum Açma
            session["user_id"] = username
            session["kullanici_adi"] = username


            toplam_uye = len(KULLANICILAR)
            bildirim_mesaji = (
                f"🎉 <b>Aramıza yeni biri katıldı!</b>\n\n"
                f"📊 <b>Toplam Üye Sayısı:</b> {toplam_uye}"
            )
            telegram_bildirim_gonder(bildirim_mesaji)

            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("index"))

    return render_template("register.html", hata=hata)




@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/spor")
def spor():
    return render_template("spor.html")


@app.route("/tesettur")
def tesettur():
    return render_template("tesettur.html")


@app.route("/esneme")
def esneme():
    if "user_id" not in session:
        flash(
            "Egzersiz ve Esneme Rehberi'ni görüntülemek için lütfen önce giriş"
            " yapın.",
            "warning",
        )
        return redirect(url_for("login", next=request.url))

    return render_template("esneme.html")


if __name__ == "__main__":
    app.run(debug=True)