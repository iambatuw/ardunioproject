"""
Yuz Algilama + Arduino Buzzer - Masaustu GUI Uygulamasi
--------------------------------------------------------
Ozellikler:
  - Kamera Ac / Durdur butonu
  - Alarm Sustur / Ac butonu
  - Arduino Bagla / Ayir + port secimi
  - Sistemi Kapat butonu
  - Canli durum gostergeleri (kamera, arduino, buzzer, FPS, yuz sayisi)

Python 3.10+ / Windows / OpenCV + pyserial + Pillow (+ tkinter built-in)
"""

import cv2
import time
import threading
from collections import deque
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

try:
    import serial
    import serial.tools.list_ports
    PYSERIAL_OK = True
except ImportError:
    PYSERIAL_OK = False


# ============= ALGILAMA AYARLARI =============
SCALE_FACTOR       = 1.25        # Yuksek = daha hizli
MIN_NEIGHBORS      = 6
MIN_YUZ_BOYUTU     = 60          # Algilama olcekli olduguna gore kucuk
ONAY_KARE_SAYISI   = 3
BAUD_RATE          = 9600
KAMERA_GENISLIK    = 640
KAMERA_YUKSEKLIK   = 480

# Performans
ALGILAMA_OLCEK     = 0.5         # Algilama icin kareyi kucult (0.5 = yari)
HER_KAC_KAREDE     = 2           # Her N karede bir algilama yap
VIDEO_FPS_HEDEF    = 60          # GUI video guncelleme hedefi
# =============================================

# Renk paleti
BEYAZ     = "#FFFFFF"
ACIK_GRI  = "#F5F5F7"
GRI       = "#E5E5EA"
KENAR     = "#D1D1D6"
METIN     = "#1C1C1E"
METIN_GRI = "#8E8E93"
YESIL     = "#34C759"
KIRMIZI   = "#FF3B30"
MAVI      = "#007AFF"
TURUNCU   = "#FF9500"


class YuzAlgilamaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yüz Algılama Sistemi")
        self.root.geometry("1100x640")
        self.root.configure(bg=BEYAZ)
        self.root.minsize(960, 560)

        # Durum degiskenleri
        self.kamera = None
        self.arduino = None
        self.kamera_aktif = False
        self.mute = False
        self.yuz_sayisi = 0
        self.onceki_gonderilen = None
        self.gecmis = deque(maxlen=ONAY_KARE_SAYISI)
        self.fps = 0.0
        self._fps_zaman = time.time()
        self._fps_sayac = 0
        self._thread = None
        self._stop_event = threading.Event()
        self._mevcut_frame = None  # Thread'den gelen son frame

        # Yuz modeli
        self.yuz_modeli = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        self._arayuz_olustur()
        self._portlari_tara()
        self._durum_guncelle()

        self.root.protocol("WM_DELETE_WINDOW", self.sistemi_kapat)

    # -------- ARAYUZ --------
    def _arayuz_olustur(self):
        # Ust bar
        ust = tk.Frame(self.root, bg=BEYAZ, height=60)
        ust.pack(fill=tk.X, side=tk.TOP)
        ust.pack_propagate(False)

        tk.Label(ust, text="Yüz Algılama Sistemi",
                 font=("Segoe UI", 18, "bold"),
                 bg=BEYAZ, fg=METIN).pack(side=tk.LEFT, padx=24, pady=14)

        self.saat_lbl = tk.Label(ust, text="", font=("Segoe UI", 11),
                                 bg=BEYAZ, fg=METIN_GRI)
        self.saat_lbl.pack(side=tk.RIGHT, padx=24)

        tk.Frame(self.root, bg=KENAR, height=1).pack(fill=tk.X)

        # Orta: video (sol) + kontrol (sag)
        orta = tk.Frame(self.root, bg=BEYAZ)
        orta.pack(fill=tk.BOTH, expand=True)

        # Sol: video
        sol = tk.Frame(orta, bg=ACIK_GRI)
        sol.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.video_lbl = tk.Label(sol, bg=ACIK_GRI,
                                  text="Kamera Kapalı\n\n'Kamerayı Başlat' düğmesine basın",
                                  fg=METIN_GRI, font=("Segoe UI", 13))
        self.video_lbl.pack(fill=tk.BOTH, expand=True)

        # Sag: kontrol paneli
        sag = tk.Frame(orta, bg=BEYAZ, width=320)
        sag.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 20), pady=20)
        sag.pack_propagate(False)

        self._durum_paneli(sag)
        self._buton_paneli(sag)
        self._arduino_paneli(sag)

    def _durum_paneli(self, parent):
        kart = tk.Frame(parent, bg=ACIK_GRI, highlightbackground=KENAR,
                        highlightthickness=1)
        kart.pack(fill=tk.X, pady=(0, 12))

        tk.Label(kart, text="DURUM", font=("Segoe UI", 9, "bold"),
                 bg=ACIK_GRI, fg=METIN_GRI).pack(anchor="w", padx=16, pady=(12, 6))

        self.led_kamera  = self._led_satir(kart, "Kamera",   "Kapalı")
        self.led_arduino = self._led_satir(kart, "Arduino",  "Bağlı değil")
        self.led_buzzer  = self._led_satir(kart, "Buzzer",   "Kapalı")

        # Istatistikler
        istat = tk.Frame(kart, bg=ACIK_GRI)
        istat.pack(fill=tk.X, padx=16, pady=(10, 14))

        self.yuz_lbl = self._istat_kutu(istat, "Yüz", "0")
        self.yuz_lbl.master.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        self.fps_lbl = self._istat_kutu(istat, "FPS", "0")
        self.fps_lbl.master.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(4, 0))

    def _led_satir(self, parent, baslik, durum):
        satir = tk.Frame(parent, bg=ACIK_GRI)
        satir.pack(fill=tk.X, padx=16, pady=3)

        canvas = tk.Canvas(satir, width=14, height=14, bg=ACIK_GRI,
                           highlightthickness=0)
        canvas.pack(side=tk.LEFT)
        nokta = canvas.create_oval(2, 2, 12, 12, fill=METIN_GRI, outline="")

        tk.Label(satir, text=baslik, font=("Segoe UI", 10),
                 bg=ACIK_GRI, fg=METIN, width=10, anchor="w").pack(side=tk.LEFT, padx=(8, 0))

        dlbl = tk.Label(satir, text=durum, font=("Segoe UI", 10),
                        bg=ACIK_GRI, fg=METIN_GRI, anchor="e")
        dlbl.pack(side=tk.RIGHT)

        return {"canvas": canvas, "nokta": nokta, "label": dlbl}

    def _istat_kutu(self, parent, baslik, deger):
        kutu = tk.Frame(parent, bg=BEYAZ, highlightbackground=KENAR,
                        highlightthickness=1)
        tk.Label(kutu, text=baslik, font=("Segoe UI", 9),
                 bg=BEYAZ, fg=METIN_GRI).pack(pady=(8, 0))
        lbl = tk.Label(kutu, text=deger, font=("Segoe UI", 20, "bold"),
                       bg=BEYAZ, fg=METIN)
        lbl.pack(pady=(0, 8))
        return lbl

    def _buton_paneli(self, parent):
        kart = tk.Frame(parent, bg=BEYAZ)
        kart.pack(fill=tk.X, pady=(0, 12))

        self.btn_kamera = self._buton(kart, "Kamerayı Başlat", self.kamera_toggle,
                                      renk=MAVI, onemli=True)
        self.btn_kamera.pack(fill=tk.X, pady=4)

        self.btn_mute = self._buton(kart, "Alarmı Sustur", self.mute_toggle,
                                    renk=TURUNCU)
        self.btn_mute.pack(fill=tk.X, pady=4)

    def _arduino_paneli(self, parent):
        kart = tk.Frame(parent, bg=ACIK_GRI, highlightbackground=KENAR,
                        highlightthickness=1)
        kart.pack(fill=tk.X, pady=(0, 12))

        tk.Label(kart, text="ARDUINO", font=("Segoe UI", 9, "bold"),
                 bg=ACIK_GRI, fg=METIN_GRI).pack(anchor="w", padx=16, pady=(12, 6))

        port_satir = tk.Frame(kart, bg=ACIK_GRI)
        port_satir.pack(fill=tk.X, padx=16, pady=(0, 8))

        self.port_var = tk.StringVar(value="COM3")
        self.port_combo = ttk.Combobox(port_satir, textvariable=self.port_var,
                                       state="readonly", width=10)
        self.port_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(port_satir, text="↻", command=self._portlari_tara,
                  bg=BEYAZ, fg=METIN, relief="flat", bd=1,
                  font=("Segoe UI", 10), width=3,
                  cursor="hand2").pack(side=tk.LEFT, padx=(6, 0))

        self.btn_arduino = self._buton(kart, "Arduino'ya Bağla",
                                       self.arduino_toggle, renk=YESIL)
        self.btn_arduino.pack(fill=tk.X, padx=16, pady=(0, 14))

        # Sistemi kapat dugmesi
        tk.Frame(parent, bg=BEYAZ).pack(expand=True, fill=tk.BOTH)
        self.btn_kapat = self._buton(parent, "Sistemi Kapat",
                                     self.sistemi_kapat, renk=KIRMIZI, onemli=True)
        self.btn_kapat.pack(fill=tk.X, side=tk.BOTTOM)

    def _buton(self, parent, metin, komut, renk=MAVI, onemli=False):
        btn = tk.Button(parent, text=metin, command=komut,
                        bg=renk, fg=BEYAZ,
                        font=("Segoe UI", 11, "bold" if onemli else "normal"),
                        relief="flat", bd=0, cursor="hand2",
                        activebackground=renk, activeforeground=BEYAZ,
                        pady=12)
        # Hover efekti
        def on_enter(e): btn.configure(bg=self._koyulaştır(renk))
        def on_leave(e): btn.configure(bg=renk)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn._orijinal_renk = renk
        return btn

    def _koyulaştır(self, hex_renk, miktar=20):
        h = hex_renk.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"#{max(0, r-miktar):02x}{max(0, g-miktar):02x}{max(0, b-miktar):02x}"

    # -------- ARDUINO --------
    def _portlari_tara(self):
        if not PYSERIAL_OK:
            self.port_combo["values"] = ["COM3"]
            return
        portlar = [p.device for p in serial.tools.list_ports.comports()]
        if not portlar:
            portlar = ["COM3", "COM4", "COM5"]
        self.port_combo["values"] = portlar
        if self.port_var.get() not in portlar:
            self.port_var.set(portlar[0])

    def arduino_toggle(self):
        if self.arduino is None:
            self._arduino_bagla()
        else:
            self._arduino_ayir()

    def _arduino_bagla(self):
        if not PYSERIAL_OK:
            messagebox.showerror("Hata", "pyserial kütüphanesi yüklü değil.")
            return
        port = self.port_var.get()
        try:
            self.arduino = serial.Serial(port, BAUD_RATE, timeout=1)
            time.sleep(2)
            self.btn_arduino.configure(text="Arduino'yu Ayır")
            self.btn_arduino._orijinal_renk = METIN_GRI
            self.btn_arduino.configure(bg=METIN_GRI)
        except Exception as e:
            messagebox.showerror("Bağlantı Hatası",
                                 f"{port} portuna bağlanılamıyor.\n\n{e}")
            self.arduino = None

    def _arduino_ayir(self):
        if self.arduino is not None:
            try:
                self.arduino.write(b'0')
                time.sleep(0.05)
                self.arduino.close()
            except Exception:
                pass
            self.arduino = None
        self.btn_arduino.configure(text="Arduino'ya Bağla")
        self.btn_arduino._orijinal_renk = YESIL
        self.btn_arduino.configure(bg=YESIL)
        self.onceki_gonderilen = None

    def _arduino_sinyal(self, deger):
        if self.arduino is None:
            return
        try:
            self.arduino.write(b'1' if deger else b'0')
        except Exception:
            self._arduino_ayir()

    # -------- KAMERA --------
    def kamera_toggle(self):
        if not self.kamera_aktif:
            self._kamera_baslat()
        else:
            self._kamera_durdur()

    def _kamera_baslat(self):
        self.kamera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.kamera.set(cv2.CAP_PROP_FRAME_WIDTH, KAMERA_GENISLIK)
        self.kamera.set(cv2.CAP_PROP_FRAME_HEIGHT, KAMERA_YUKSEKLIK)

        if not self.kamera.isOpened():
            messagebox.showerror("Hata", "Kamera açılamadı.")
            self.kamera = None
            return

        self.kamera_aktif = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._kamera_dongusu, daemon=True)
        self._thread.start()

        self.btn_kamera.configure(text="Kamerayı Durdur")
        self.btn_kamera._orijinal_renk = METIN_GRI
        self.btn_kamera.configure(bg=METIN_GRI)

        self._video_guncelle()

    def _kamera_durdur(self):
        self.kamera_aktif = False
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.5)
            self._thread = None
        if self.kamera is not None:
            self.kamera.release()
            self.kamera = None
        self._arduino_sinyal(False)
        self.onceki_gonderilen = None
        self.yuz_sayisi = 0
        self._mevcut_frame = None

        self.btn_kamera.configure(text="Kamerayı Başlat")
        self.btn_kamera._orijinal_renk = MAVI
        self.btn_kamera.configure(bg=MAVI)

        self.video_lbl.configure(image="",
                                 text="Kamera Kapalı\n\n'Kamerayı Başlat' düğmesine basın")
        self.video_lbl.image = None

    def _kamera_dongusu(self):
        """Kamera okuma + yuz algilama - ayri thread'de calisir."""
        kare_no = 0
        son_yuzler = []   # Son algilanan yuzler (her karede yeniden algilama yapilmiyor)

        while not self._stop_event.is_set() and self.kamera is not None:
            ret, kare = self.kamera.read()
            if not ret:
                time.sleep(0.01)
                continue

            kare = cv2.flip(kare, 1)
            kare_no += 1

            # Her N karede bir algilama (performans)
            if kare_no % HER_KAC_KAREDE == 0:
                # Kucuk boyutta algila -> cok daha hizli
                kucuk = cv2.resize(kare, None, fx=ALGILAMA_OLCEK, fy=ALGILAMA_OLCEK,
                                   interpolation=cv2.INTER_LINEAR)
                gri = cv2.cvtColor(kucuk, cv2.COLOR_BGR2GRAY)
                gri = cv2.equalizeHist(gri)

                tespitler = self.yuz_modeli.detectMultiScale(
                    gri,
                    scaleFactor=SCALE_FACTOR,
                    minNeighbors=MIN_NEIGHBORS,
                    minSize=(MIN_YUZ_BOYUTU, MIN_YUZ_BOYUTU),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                # Kucuk karedeki koordinatlari orijinal boyuta olcekle
                olcek_geri = 1.0 / ALGILAMA_OLCEK
                son_yuzler = [(int(x * olcek_geri), int(y * olcek_geri),
                               int(w * olcek_geri), int(h * olcek_geri))
                              for (x, y, w, h) in tespitler]

            yuzler = son_yuzler
            self.yuz_sayisi = len(yuzler)
            self.gecmis.append(self.yuz_sayisi > 0)

            # Temporal smoothing
            yeni_durum = self.onceki_gonderilen
            if len(self.gecmis) == ONAY_KARE_SAYISI:
                if all(self.gecmis):
                    yeni_durum = True
                elif not any(self.gecmis):
                    yeni_durum = False

            hedef = False if self.mute else yeni_durum
            if hedef != self.onceki_gonderilen:
                self._arduino_sinyal(bool(hedef))
                self.onceki_gonderilen = hedef

            # Kutu ciz
            buzzer_aktif = bool(self.onceki_gonderilen) and not self.mute
            renk = (80, 175, 76) if buzzer_aktif else (142, 142, 147)
            for (x, y, w, h) in yuzler:
                self._kose_kutu(kare, x, y, w, h, renk)

            # FPS
            self._fps_sayac += 1
            if time.time() - self._fps_zaman >= 1.0:
                self.fps = self._fps_sayac / (time.time() - self._fps_zaman)
                self._fps_sayac = 0
                self._fps_zaman = time.time()

            self._mevcut_frame = kare

    def _kose_kutu(self, img, x, y, w, h, renk, k=2, u=22):
        cv2.line(img, (x, y), (x + u, y), renk, k)
        cv2.line(img, (x, y), (x, y + u), renk, k)
        cv2.line(img, (x + w, y), (x + w - u, y), renk, k)
        cv2.line(img, (x + w, y), (x + w, y + u), renk, k)
        cv2.line(img, (x, y + h), (x + u, y + h), renk, k)
        cv2.line(img, (x, y + h), (x, y + h - u), renk, k)
        cv2.line(img, (x + w, y + h), (x + w - u, y + h), renk, k)
        cv2.line(img, (x + w, y + h), (x + w, y + h - u), renk, k)

    def _video_guncelle(self):
        """Tkinter ana thread'inde video etiketini gunceller."""
        if not self.kamera_aktif:
            return

        frame = self._mevcut_frame
        if frame is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Etiket boyutuna sigdir
            w = self.video_lbl.winfo_width()
            h = self.video_lbl.winfo_height()
            if w > 10 and h > 10:
                ih, iw = rgb.shape[:2]
                olcek = min(w / iw, h / ih)
                yeni = (max(1, int(iw * olcek)), max(1, int(ih * olcek)))
                rgb = cv2.resize(rgb, yeni, interpolation=cv2.INTER_LINEAR)
            img = Image.fromarray(rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_lbl.configure(image=imgtk, text="")
            self.video_lbl.image = imgtk

        self.root.after(max(1, int(1000 / VIDEO_FPS_HEDEF)), self._video_guncelle)

    # -------- MUTE --------
    def mute_toggle(self):
        self.mute = not self.mute
        if self.mute:
            self.btn_mute.configure(text="Alarmı Aç")
            self.btn_mute._orijinal_renk = METIN_GRI
            self.btn_mute.configure(bg=METIN_GRI)
            # Mute olur olmaz arduino'yu sustur
            self._arduino_sinyal(False)
            self.onceki_gonderilen = False
        else:
            self.btn_mute.configure(text="Alarmı Sustur")
            self.btn_mute._orijinal_renk = TURUNCU
            self.btn_mute.configure(bg=TURUNCU)

    # -------- DURUM GUNCELLEME --------
    def _durum_guncelle(self):
        # Kamera LED
        if self.kamera_aktif:
            self._led_ayar(self.led_kamera, YESIL, "Aktif")
        else:
            self._led_ayar(self.led_kamera, METIN_GRI, "Kapalı")

        # Arduino LED
        if self.arduino is not None:
            self._led_ayar(self.led_arduino, YESIL, self.port_var.get())
        else:
            self._led_ayar(self.led_arduino, METIN_GRI, "Bağlı değil")

        # Buzzer LED
        buzzer_aktif = bool(self.onceki_gonderilen) and not self.mute and self.kamera_aktif
        if self.mute:
            self._led_ayar(self.led_buzzer, TURUNCU, "Sessiz")
        elif buzzer_aktif:
            self._led_ayar(self.led_buzzer, KIRMIZI, "Çalıyor")
        else:
            self._led_ayar(self.led_buzzer, METIN_GRI, "Kapalı")

        # Istatistikler
        self.yuz_lbl.configure(text=str(self.yuz_sayisi))
        self.fps_lbl.configure(text=f"{self.fps:.0f}")

        # Saat
        self.saat_lbl.configure(text=time.strftime("%H:%M:%S"))

        self.root.after(200, self._durum_guncelle)

    def _led_ayar(self, led, renk, durum):
        led["canvas"].itemconfig(led["nokta"], fill=renk)
        led["label"].configure(text=durum)

    # -------- KAPAT --------
    def sistemi_kapat(self):
        if messagebox.askyesno("Sistemi Kapat", "Uygulamayı kapatmak istediğinize emin misiniz?"):
            try:
                self._kamera_durdur()
            except Exception:
                pass
            try:
                self._arduino_ayir()
            except Exception:
                pass
            self.root.destroy()


def main():
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use("clam")
    except Exception:
        pass
    app = YuzAlgilamaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
