"""
Yuz Algilama -> Arduino Buzzer Sistemi (Gelismis Surum)
- Kameradan yuz algilar (stabil + temporal smoothing)
- Arduino'ya '1' (yuz var) / '0' (yuz yok) gonderir
- Ses Arduino uzerindeki buzzer'dan (Pin 8) cikar

Tuslar:
  q  - cikis
  m  - sessize al/ac (mute toggle)
"""

import cv2
import serial
import time
from collections import deque

# ============= AYARLAR =============
ARDUINO_PORTU      = 'COM3'      # Arduino IDE > Tools > Port
BAUD_RATE          = 9600
KAMERA_INDEX       = 0           # Birden fazla kamera varsa 1, 2 deneyin
KAMERA_GENISLIK    = 960
KAMERA_YUKSEKLIK   = 540

# Yuz algilama hassasiyet ayarlari
SCALE_FACTOR       = 1.2         # Yuksek = daha hizli ama az hassas
MIN_NEIGHBORS      = 8           # Yuksek = az yanlis pozitif (onerilen 5-10)
MIN_YUZ_BOYUTU     = 80          # Piksel - bundan kucuk algilamalar elenir

# Stabilite (false positive onleme)
ONAY_KARE_SAYISI   = 3           # Durum degismesi icin gerekli ardisik kare
# ===================================


def panel_ciz(img, x, y, w, h, alpha=0.85, renk=(255, 255, 255)):
    """Yari saydam panel cizer (varsayilan: beyaz)."""
    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), renk, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)


def kose_kutu_ciz(img, x, y, w, h, renk, kalinlik=2, kose_uzunluk=20):
    """Modern kose isaretli kutu cizer."""
    cv2.line(img, (x, y), (x + kose_uzunluk, y), renk, kalinlik)
    cv2.line(img, (x, y), (x, y + kose_uzunluk), renk, kalinlik)
    cv2.line(img, (x + w, y), (x + w - kose_uzunluk, y), renk, kalinlik)
    cv2.line(img, (x + w, y), (x + w, y + kose_uzunluk), renk, kalinlik)
    cv2.line(img, (x, y + h), (x + kose_uzunluk, y + h), renk, kalinlik)
    cv2.line(img, (x, y + h), (x, y + h - kose_uzunluk), renk, kalinlik)
    cv2.line(img, (x + w, y + h), (x + w - kose_uzunluk, y + h), renk, kalinlik)
    cv2.line(img, (x + w, y + h), (x + w, y + h - kose_uzunluk), renk, kalinlik)


# ---- Arduino baglantisi ----
print("Arduino'ya baglaniliyor...")
try:
    arduino = serial.Serial(ARDUINO_PORTU, BAUD_RATE, timeout=1)
    time.sleep(2)
    print(f"  [OK] Arduino baglandi: {ARDUINO_PORTU}")
except Exception as e:
    print(f"  [HATA] {ARDUINO_PORTU} portuna baglanilamadi: {e}")
    print("  Arduino IDE > Tools > Port'tan dogru portu kontrol edin.")
    exit()

# ---- Yuz algilama modeli ----
yuz_modeli = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ---- Kamera ----
kamera = cv2.VideoCapture(KAMERA_INDEX, cv2.CAP_DSHOW)
kamera.set(cv2.CAP_PROP_FRAME_WIDTH, KAMERA_GENISLIK)
kamera.set(cv2.CAP_PROP_FRAME_HEIGHT, KAMERA_YUKSEKLIK)

if not kamera.isOpened():
    print("  [HATA] Kamera acilamadi.")
    arduino.close()
    exit()

print("  [OK] Kamera acildi.")
print("\nProgram basladi. Cikmak icin 'q', sessize almak icin 'm' tusuna basin.\n")

# ---- Durum degiskenleri ----
onceki_gonderilen = None       # Arduino'ya en son gonderilen durum
gecmis = deque(maxlen=ONAY_KARE_SAYISI)  # Son N karenin yuz var/yok bilgisi
mute = False                   # Sessize alma
fps_zaman = time.time()
fps_sayac = 0
fps = 0.0

# Pencere ayarlari
PENCERE_ADI = 'Yuz Algilama Sistemi'
cv2.namedWindow(PENCERE_ADI, cv2.WINDOW_NORMAL)

while True:
    ret, kare = kamera.read()
    if not ret:
        print("  [UYARI] Kameradan kare alinamadi.")
        break

    kare = cv2.flip(kare, 1)  # Ayna gibi (sag-sol cevirme)
    yukseklik, genislik = kare.shape[:2]

    # ---- Yuz algila ----
    gri = cv2.cvtColor(kare, cv2.COLOR_BGR2GRAY)
    gri = cv2.equalizeHist(gri)  # Kontrast iyilestirme -> daha stabil

    yuzler = yuz_modeli.detectMultiScale(
        gri,
        scaleFactor=SCALE_FACTOR,
        minNeighbors=MIN_NEIGHBORS,
        minSize=(MIN_YUZ_BOYUTU, MIN_YUZ_BOYUTU),
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    yuz_var_su_an = len(yuzler) > 0
    gecmis.append(yuz_var_su_an)

    # ---- Temporal smoothing: durum degisimi icin ardisik N kare gerekir ----
    yeni_durum = onceki_gonderilen
    if len(gecmis) == ONAY_KARE_SAYISI:
        if all(gecmis):
            yeni_durum = True
        elif not any(gecmis):
            yeni_durum = False

    # Mute aktifse her durumda False kabul et
    hedef_durum = False if mute else yeni_durum

    # Arduino'ya sadece durum degistiginde gonder
    if hedef_durum != onceki_gonderilen:
        if hedef_durum:
            print(f"[{time.strftime('%H:%M:%S')}] Yuz algilandi -> '1' gonderildi")
            arduino.write(b'1')
        else:
            sebep = "mute" if mute else "yuz yok"
            print(f"[{time.strftime('%H:%M:%S')}] {sebep} -> '0' gonderildi")
            arduino.write(b'0')
        onceki_gonderilen = hedef_durum

    # ---- FPS hesapla ----
    fps_sayac += 1
    if time.time() - fps_zaman >= 1.0:
        fps = fps_sayac / (time.time() - fps_zaman)
        fps_sayac = 0
        fps_zaman = time.time()

    # ---- GORSEL ARAYUZ (Minimal Beyaz Tema) ----
    aktif_yuz_sayisi = len(yuzler)
    buzzer_aktif = (onceki_gonderilen is True) and not mute

    # Renk paleti (BGR)
    BEYAZ      = (255, 255, 255)
    SIYAH      = (30, 30, 30)
    GRI        = (130, 130, 130)
    ACIK_GRI   = (220, 220, 220)
    AKSAN      = (90, 90, 90)         # koyu gri vurgu
    AKTIF      = (80, 175, 76)        # yumusak yesil
    PASIF      = (180, 180, 180)      # gri

    # Yuzleri ciz
    kutu_renk = AKTIF if buzzer_aktif else AKSAN
    for (x, y, w, h) in yuzler:
        kose_kutu_ciz(kare, x, y, w, h, kutu_renk, kalinlik=2, kose_uzunluk=22)

    # ---- UST PANEL (beyaz) ----
    panel_ciz(kare, 0, 0, genislik, 64, alpha=0.92, renk=BEYAZ)
    cv2.line(kare, (0, 64), (genislik, 64), ACIK_GRI, 1)

    # Sol: durum noktasi + metin
    nokta_renk = AKTIF if buzzer_aktif else PASIF
    cv2.circle(kare, (28, 32), 8, nokta_renk, -1)

    if mute:
        durum_yazi = "Sessiz"
    elif buzzer_aktif:
        durum_yazi = "Buzzer Aktif"
    else:
        durum_yazi = "Bekleniyor"
    cv2.putText(kare, durum_yazi, (48, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, SIYAH, 1, cv2.LINE_AA)

    # Orta: yuz sayisi
    yuz_yazi = f"Yuz Sayisi: {aktif_yuz_sayisi}"
    (tw, _), _ = cv2.getTextSize(yuz_yazi, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
    cv2.putText(kare, yuz_yazi, ((genislik - tw) // 2, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, SIYAH, 1, cv2.LINE_AA)

    # Sag: FPS
    fps_yazi = f"{fps:.0f} FPS"
    cv2.putText(kare, fps_yazi, (genislik - 90, 38),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, GRI, 1, cv2.LINE_AA)

    # ---- ALT PANEL (beyaz) ----
    panel_ciz(kare, 0, yukseklik - 38, genislik, 38, alpha=0.92, renk=BEYAZ)
    cv2.line(kare, (0, yukseklik - 38), (genislik, yukseklik - 38), ACIK_GRI, 1)

    sol_yazi = f"Q: Cikis    M: {'Sesi Ac' if mute else 'Sessize Al'}"
    cv2.putText(kare, sol_yazi, (15, yukseklik - 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, SIYAH, 1, cv2.LINE_AA)

    sag_yazi = f"{ARDUINO_PORTU}  -  {time.strftime('%H:%M:%S')}"
    (tw, _), _ = cv2.getTextSize(sag_yazi, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
    cv2.putText(kare, sag_yazi, (genislik - tw - 15, yukseklik - 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, GRI, 1, cv2.LINE_AA)

    # ---- Pencere ----
    cv2.imshow(PENCERE_ADI, kare)

    tus = cv2.waitKey(1) & 0xFF
    if tus == ord('q'):
        break
    elif tus == ord('m'):
        mute = not mute
        print(f"[{time.strftime('%H:%M:%S')}] Mute: {'ACIK' if mute else 'KAPALI'}")

# ---- Temizlik ----
print("\nProgram kapatiliyor...")
try:
    arduino.write(b'0')
    time.sleep(0.1)
    arduino.close()
except Exception:
    pass
kamera.release()
cv2.destroyAllWindows()
print("Cikis basarili.")
