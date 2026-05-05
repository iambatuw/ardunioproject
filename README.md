# Yüz Algılama + Arduino Buzzer Sistemi

PC kamerasından yüz algılayan ve algılama anında **Arduino'ya sinyal göndererek buzzer çalan** bir sistem. OpenCV tabanlı, minimal beyaz arayüzlü, stabil (temporal smoothing ile yanlış pozitifler filtrelenir).

## Özellikler

- 🎯 **Haar Cascade** ile gerçek zamanlı yüz algılama
- 🔇 **Temporal smoothing** — arka arkaya 3 kare onay gerektirir, hayalet algılamalar elenir
- 🔔 **Arduino buzzer** kontrolü — Pin 8'den ses çıkışı
- 🎨 **Minimal beyaz arayüz** — köşe işaretli yüz kutuları, FPS sayacı, durum göstergesi
- ⌨️ **Klavye kontrolü** — `Q` çıkış, `M` sessize al
- 📦 **Tek dosyalık `.exe`** olarak paketlenebilir (PyInstaller ile)

## Ekran Görüntüsü

```
┌──────────────────────────────────────────────────────┐
│ ● Buzzer Aktif          Yuz Sayisi: 1        30 FPS  │
├──────────────────────────────────────────────────────┤
│                                                      │
│                    ┌─      ─┐                        │
│                    │  YÜZ   │                        │
│                    └─      ─┘                        │
│                                                      │
├──────────────────────────────────────────────────────┤
│ Q: Cikis  M: Sessize Al             COM3 - 14:32:10  │
└──────────────────────────────────────────────────────┘
```

## Donanım Gereksinimleri

| Parça          | Açıklama                         |
| -------------- | -------------------------------- |
| Arduino UNO    | Veya uyumlu (Nano, Mega vs.)     |
| Buzzer         | Aktif veya pasif                 |
| Kamera         | Dahili veya USB webcam           |
| USB kablo      | Arduino için                     |

### Bağlantı Şeması

```
Buzzer (+)  ──►  Pin 8
Buzzer (-)  ──►  GND
```

## Kurulum

### 1. Depoyu indirin

```powershell
git clone https://github.com/iambatuw/ardunioproject.git
cd ardunioproject
```

### 2. Python kütüphaneleri

Python **3.10+** gereklidir.

```powershell
pip install -r requirements.txt
```

### 3. Arduino kodunu yükleyin

1. `arduino_buzzer/arduino_buzzer.ino` dosyasını Arduino IDE ile açın
2. **Tools → Board:** Arduino UNO
3. **Tools → Port:** (Arduino'nuzun bağlı olduğu COM portu)
4. Upload (→) butonuna basın

> **Klon Arduino (CH340 çipli) kullanıyorsanız:** Önce [CH340 sürücüsünü](https://sparks.gogo.co.nz/ch340.html) kurun.

### 4. Python kodunu çalıştırın

`yuz_algilama.py` içindeki `ARDUINO_PORTU` değişkenini kendi portunuzla güncelleyin:

```python
ARDUINO_PORTU = 'COM3'   # Arduino IDE > Tools > Port'tan kontrol edin
```

Sonra çalıştırın:

```powershell
python yuz_algilama.py
```

## Kullanım

| Tuş | İşlev                        |
| --- | ---------------------------- |
| `Q` | Programdan çık               |
| `M` | Buzzer'ı sessize al / aç     |

## Ayarlar (İnce Ayar)

`yuz_algilama.py` başındaki sabitleri değiştirerek hassasiyeti ayarlayabilirsiniz:

```python
SCALE_FACTOR     = 1.2   # Yüksek = hızlı, düşük = hassas
MIN_NEIGHBORS    = 8     # Yüksek = az yanlış pozitif
MIN_YUZ_BOYUTU   = 80    # Küçük şeyler yüz sayılmaz (piksel)
ONAY_KARE_SAYISI = 3     # Durum değişimi için gerekli ardışık kare
```

## `.exe` Olarak Paketleme

Tek dosyalık Windows executable oluşturmak için:

```powershell
pip install pyinstaller
pyinstaller --onefile --noconsole --name "YuzAlgilama" --collect-all cv2 yuz_algilama.py
```

Çıktı: `dist/YuzAlgilama.exe` (~57 MB)

## Proje Yapısı

```
yuz_algilama/
├── yuz_algilama.py              # Ana Python uygulaması
├── arduino_buzzer/
│   └── arduino_buzzer.ino       # Arduino tarafı
├── requirements.txt             # Python bağımlılıkları
├── README.md
├── LICENSE
└── .gitignore
```

## Sorun Giderme

| Problem                                         | Çözüm                                                                   |
| ----------------------------------------------- | ----------------------------------------------------------------------- |
| `cannot open port COM3`                         | Arduino IDE'yi kapatın veya doğru portu `ARDUINO_PORTU`'na yazın        |
| `ModuleNotFoundError: cv2`                      | `pip install opencv-python` çalıştırın                                  |
| Buzzer ötmüyor (pasif buzzer)                   | `.ino` içinde `tone(BUZZER_PIN, 1000);` satırını aktifleştirin          |
| Buzzer ötmüyor (aktif buzzer)                   | Varsayılan `digitalWrite(HIGH)` yeterli, bağlantıları kontrol edin      |
| Kamera açılmıyor                                | Başka program kamerayı kullanıyor olabilir, `KAMERA_INDEX`'i değiştirin |
| Yanlış algılama (yüz yokken 1 gönderiyor)       | `MIN_NEIGHBORS`'ı yükseltin (8 → 10-12)                                 |
| Uzaktan yüz algılanmıyor                        | `MIN_YUZ_BOYUTU`'nu düşürün (80 → 40)                                   |

## Lisans

MIT — `LICENSE` dosyasına bakın.

