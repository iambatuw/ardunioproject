# Yüz Algılama + Arduino Buzzer Sistemi

PC kamerasından yüz algılayan ve algılama anında **Arduino'ya sinyal göndererek buzzer çalan** bir masaüstü uygulaması. OpenCV tabanlı, butonlu modern arayüz, stabil algılama (temporal smoothing ile yanlış pozitifler filtrelenir).

## Özellikler

- 🖥️ **Masaüstü GUI** — Tkinter tabanlı, butonlu modern arayüz
- 🎯 **Haar Cascade** ile gerçek zamanlı yüz algılama
- ⚡ **Yüksek FPS** — çok aşamalı optimizasyon (küçük çözünürlükte algılama, kare atlama)
- 🔇 **Temporal smoothing** — arka arkaya 3 kare onay, hayalet algılamalar elenir
- 🔔 **Arduino buzzer** kontrolü — Pin 8'den ses çıkışı
- 🔌 **Otomatik port tarama** — açılır listeden COM portunu seçin
- 🎨 **Minimal beyaz tema** — Apple benzeri temiz tasarım
- 🇹🇷 **Tam Türkçe arayüz** (ç, ş, ğ, ü, ö, ı destekli)
- 📦 **Hazır `.exe` sürümü** — [Releases](https://github.com/iambatuw/ardunioproject/releases) sayfasından indirin, Python kurmadan çalıştırın

## Ekran Görüntüsü

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Yüz Algılama Sistemi                                          14:32:10  │
├─────────────────────────────────────────────────┬───────────────────────┤
│                                                 │  DURUM                │
│                                                 │  ● Kamera      Aktif  │
│                ┌─        ─┐                     │  ● Arduino     COM3   │
│                │          │                     │  ● Buzzer     Çalıyor │
│                │   YÜZ    │                     │                       │
│                │          │                     │  ┌─────┐  ┌─────┐     │
│                └─        ─┘                     │  │ Yüz │  │ FPS │     │
│                                                 │  │  1  │  │ 45  │     │
│                                                 │  └─────┘  └─────┘     │
│                                                 │                       │
│                                                 │  [ Kamerayı Durdur ]  │
│                                                 │  [ Alarmı Sustur   ]  │
│                                                 │                       │
│                                                 │  ARDUINO              │
│                                                 │  [COM3  ▼] [↻]        │
│                                                 │  [Arduino'yu Ayır  ]  │
│                                                 │                       │
│                                                 │  [  Sistemi Kapat  ]  │
└─────────────────────────────────────────────────┴───────────────────────┘
```

## Nasıl Çalışır?

```
 ┌──────────┐        ┌──────────────┐      '1' / '0'      ┌──────────┐
 │  Kamera  │ ────►  │   Python     │  ─────────────►     │ Arduino  │
 │  (webcam)│ frame  │  (OpenCV +   │   USB Serial        │   UNO    │
 │          │        │   Tkinter)   │   9600 baud         │          │
 └──────────┘        └──────────────┘                     └─────┬────┘
                             ▲                                  │
                             │                           digitalWrite HIGH/LOW
                             │ Haar Cascade                     │
                             │ yuz algilama                     ▼
                             │                           ┌──────────┐
                             │                           │  Buzzer  │
                             └──────── Temporal          │   Pin 8  │
                                        Smoothing        └──────────┘
                                        (3 kare onay)
```

1. **Python** kameradan kare alır, yüz algılama için **yarı boyuta küçültür** (hızlandırma)
2. **Haar Cascade** sınıflandırıcı yüzleri tespit eder
3. **Temporal smoothing**: arka arkaya 3 kare aynı sonuç verirse durumu değiştirir (yanlış pozitifler elenir)
4. Durum değişikliğinde **Arduino'ya seri port üzerinden** `'1'` (yüz var) veya `'0'` (yüz yok) gönderilir
5. **Arduino** gelen değere göre Pin 8'deki buzzer'ı **HIGH** yapar veya susturur

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

### Seçenek A — Hazır `.exe` (önerilen)

1. [**Releases** sayfasından](https://github.com/iambatuw/ardunioproject/releases) `YuzAlgilama.exe` dosyasını indirin
2. Çift tıklayın — Python kurulumu gerekmez
3. Windows Defender uyarısı çıkarsa **More info → Run anyway**

### Seçenek B — Kaynak koddan

#### 1. Depoyu indirin

```powershell
git clone https://github.com/iambatuw/ardunioproject.git
cd ardunioproject
```

#### 2. Python kütüphaneleri

Python **3.10+** gereklidir.

```powershell
pip install -r requirements.txt
```

#### 3. Arduino kodunu yükleyin

1. `arduino_buzzer/arduino_buzzer.ino` dosyasını Arduino IDE ile açın
2. **Tools → Board:** Arduino UNO
3. **Tools → Port:** (Arduino'nuzun bağlı olduğu COM portu)
4. Upload (→) butonuna basın

> **Klon Arduino (CH340 çipli) kullanıyorsanız:** Önce [CH340 sürücüsünü](https://sparks.gogo.co.nz/ch340.html) kurun.

#### 4. Uygulamayı çalıştırın

```powershell
python yuz_algilama.py
```

## Kullanım

Uygulama açıldığında sağ panelde tüm kontroller bulunur:

| Buton                    | İşlev                                                     |
| ------------------------ | --------------------------------------------------------- |
| **Kamerayı Başlat**      | Webcam'i açar ve canlı algılamayı başlatır                |
| **Kamerayı Durdur**      | Kamerayı kapatır, Arduino'yu susturur                     |
| **Alarmı Sustur**        | Yüz algılansa bile buzzer'a sinyal gitmez                 |
| **Alarmı Aç**            | Buzzer uyarısını tekrar etkinleştirir                     |
| **Arduino'ya Bağla**     | Seçili COM portuna bağlanır                               |
| **Arduino'yu Ayır**      | Seri portu güvenli şekilde kapatır                        |
| **↻** (yenile)           | Bilgisayardaki COM portlarını yeniden tarar               |
| **Sistemi Kapat**        | Onay alarak her şeyi kapatır (kamera + Arduino + pencere) |

### Durum Paneli

- **Kamera** — kamera açık mı?
- **Arduino** — bağlı COM portu
- **Buzzer** — şu an çalıyor mu / kapalı mı / sessiz mi?
- **Yüz** sayacı — kamerada o an görünen yüz sayısı
- **FPS** — saniyedeki kare sayısı (performans göstergesi)

## Performans İnce Ayarı

`yuz_algilama.py` başındaki sabitler:

```python
SCALE_FACTOR      = 1.25   # Yüksek = daha hızlı, düşük = daha hassas
MIN_NEIGHBORS     = 6      # Yüksek = az yanlış pozitif
MIN_YUZ_BOYUTU    = 60     # Küçük yüzleri eler (piksel)
ONAY_KARE_SAYISI  = 3      # Durum değişimi için gereken ardışık kare

# Performans
ALGILAMA_OLCEK    = 0.5    # Algılama boyut oranı (0.5 = %50, ~4x hızlı)
HER_KAC_KAREDE    = 2      # Her N karede bir algılama
VIDEO_FPS_HEDEF   = 60     # GUI video güncelleme hedefi
```

**Daha hızlı istiyorum:** `ALGILAMA_OLCEK=0.4`, `HER_KAC_KAREDE=3`  
**Daha hassas istiyorum:** `ALGILAMA_OLCEK=0.75`, `HER_KAC_KAREDE=1`, `MIN_NEIGHBORS=8`

## `.exe` Olarak Paketleme

Kendi `.exe` dosyanızı oluşturmak için:

```powershell
pip install pyinstaller
pyinstaller --onefile --noconsole --name "YuzAlgilama" --collect-all cv2 yuz_algilama.py
```

Çıktı: `dist/YuzAlgilama.exe` (~60 MB)

## Proje Yapısı

```
ardunioproject/
├── yuz_algilama.py              # Ana GUI uygulaması (Tkinter + OpenCV)
├── arduino_buzzer/
│   └── arduino_buzzer.ino       # Arduino tarafı (Serial → Pin 8)
├── requirements.txt             # Python bağımlılıkları
├── README.md
├── LICENSE                      # MIT
└── .gitignore
```

## Sorun Giderme

| Problem                                          | Çözüm                                                                                  |
| ------------------------------------------------ | -------------------------------------------------------------------------------------- |
| `cannot open port COM3`                          | Arduino IDE'yi kapatın, doğru portu seçin ve `↻` ile yenileyin                         |
| `ModuleNotFoundError: cv2`                       | `pip install -r requirements.txt`                                                      |
| Buzzer ötmüyor (pasif buzzer)                    | `.ino` içinde `tone(BUZZER_PIN, 1000);` satırını aktifleştirin                         |
| Buzzer ötmüyor (aktif buzzer)                    | Varsayılan `digitalWrite(HIGH)` yeterli, bağlantıları kontrol edin                     |
| Kamera açılmıyor                                 | Başka program kamerayı kullanıyor olabilir                                             |
| Yanlış algılama (yüz yokken buzzer çalıyor)      | `MIN_NEIGHBORS`'ı yükseltin (6 → 8-10) veya `ONAY_KARE_SAYISI`'nı artırın (3 → 5)      |
| Uzaktan yüz algılanmıyor                         | `MIN_YUZ_BOYUTU`'nu düşürün (60 → 40)                                                  |
| FPS düşük                                        | `ALGILAMA_OLCEK=0.4` yapın veya `HER_KAC_KAREDE=3`                                     |

## Lisans

[MIT](LICENSE) — özgürce kullanın, değiştirin, paylaşın.


