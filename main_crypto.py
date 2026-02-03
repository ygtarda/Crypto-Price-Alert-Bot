import customtkinter as ctk
import requests
import threading
import time
from plyer import notification
from datetime import datetime
import csv
import os

# 🎨 Arayüz Teması
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green") # Para rengi olsun :)

class CryptoTrackerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.running = False # Takip durumu kontrolü
        self.api_url = "https://api.coingecko.com/api/v3/simple/price"
        self.currency = 'usd'
        self.csv_file = "fiyat_gecmisi_gui.csv"

        # Pencere Ayarları
        self.title("Pro Kripto Takip 📈")
        self.geometry("500x550")
        self.resizable(False, False)

        # --- ARAYÜZ ELEMANLARI ---
        self.header = ctk.CTkLabel(self, text="Kripto Fiyat Alarmı", font=("Roboto", 22, "bold"))
        self.header.pack(pady=20)

        # 1. Coin Girişi
        self.coin_frame = ctk.CTkFrame(self)
        self.coin_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.coin_frame, text="Coin ID (örn: bitcoin):", font=("Roboto", 14)).pack(side="left", padx=10)
        self.coin_entry = ctk.CTkEntry(self.coin_frame, width=200, placeholder_text="bitcoin")
        self.coin_entry.pack(side="right", padx=10)

        # 2. Hedef Fiyat Girişi
        self.price_frame = ctk.CTkFrame(self)
        self.price_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(self.price_frame, text="Hedef Fiyat ($):", font=("Roboto", 14)).pack(side="left", padx=10)
        self.target_entry = ctk.CTkEntry(self.price_frame, width=200, placeholder_text="Örn: 98500")
        self.target_entry.pack(side="right", padx=10)

        # 3. Başlat/Durdur Butonu
        self.action_btn = ctk.CTkButton(self, text="TAKİBİ BAŞLAT ▶️", command=self.toggle_tracking, height=45, font=("Roboto", 16, "bold"))
        self.action_btn.pack(pady=20)

        # 4. Durum Göstergesi (Büyük Fiyat)
        self.price_label = ctk.CTkLabel(self, text="--- $", font=("Roboto", 36, "bold"), text_color="#2CC985")
        self.price_label.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(self, text="Hazır Bekleniyor...", text_color="gray")
        self.status_label.pack(pady=5)

        # 5. Log Alanı (Aşağı akan yazılar)
        self.log_box = ctk.CTkTextbox(self, width=450, height=150)
        self.log_box.pack(pady=10)
        self.log_message("Uygulama başlatıldı. Coin ID ve Hedef Fiyat giriniz.")

    # --- YARDIMCI FONKSİYONLAR ---
    def log_message(self, message):
        """Arayüzdeki kutuya mesaj yazar"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("0.0", f"[{timestamp}] {message}\n") # En üste ekle

    def save_to_csv(self, coin, price):
        """Fiyatı dosyaya kaydeder"""
        file_exists = os.path.exists(self.csv_file)
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Tarih", "Coin", "Fiyat (USD)"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), coin, price])

    def send_notification(self, title, message):
        """Masaüstü bildirimi atar"""
        try:
             notification.notify(
                title=title,
                message=message,
                timeout=10
            )
        except:
            pass # Bildirim atamazsa program çökmesin

    # --- ANA MANTIK ---
    def get_price_safe(self, coin_id):
        """SSL hatasını aşarak fiyat çeker"""
        try:
            # 🛠️ SSL HATASI ÇÖZÜMÜ BURADA 🛠️
            # Kendimizi Chrome tarayıcı gibi tanıtıyoruz
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            params = {'ids': coin_id, 'vs_currencies': self.currency}
            
            # verify=False ile sertifika kontrolünü kapatıyoruz
            response = requests.get(self.api_url, params=params, headers=headers, verify=False, timeout=10)
            
            data = response.json()
            return data[coin_id][self.currency]
        except requests.exceptions.RequestException as e:
             self.log_message(f"Bağlantı Hatası: {e}")
             return None
        except KeyError:
             self.log_message(f"Hata: '{coin_id}' bulunamadı. ID'yi kontrol et.")
             return None
        except Exception as e:
             self.log_message(f"Genel Hata: {e}")
             return None

    def toggle_tracking(self):
        """Başlat/Durdur mantığı"""
        if not self.running:
            # Başlatılıyor...
            coin = self.coin_entry.get().lower().strip()
            target_str = self.target_entry.get().strip()

            if not coin or not target_str:
                self.status_label.configure(text="❌ Lütfen Coin ID ve Hedef Fiyat girin!", text_color="red")
                return

            try:
                target_price = float(target_str)
            except ValueError:
                self.status_label.configure(text="❌ Hedef fiyat sayı olmalı!", text_color="red")
                return

            self.running = True
            self.action_btn.configure(text="DURDUR ⏹️", fg_color="red", hover_color="darkred")
            self.coin_entry.configure(state="disabled")
            self.target_entry.configure(state="disabled")
            self.status_label.configure(text=f"✅ {coin.upper()} takip ediliyor... Hedef: ${target_price}", text_color="#2CC985")
            self.log_message(f"--- TAKİP BAŞLADI: {coin.upper()} ---")
            
            # Arka plan thread'ini başlat
            threading.Thread(target=self.tracking_loop, args=(coin, target_price), daemon=True).start()

        else:
            # Durduruluyor...
            self.running = False
            self.action_btn.configure(text="TAKİBİ BAŞLAT ▶️", fg_color=["#2CC985", "#2DB47B"], hover_color=["#24A36B", "#24A36B"])
            self.coin_entry.configure(state="normal")
            self.target_entry.configure(state="normal")
            self.status_label.configure(text="⏹️ Takip durduruldu.", text_color="orange")
            self.log_message("--- TAKİP DURDURULDU ---")

    def tracking_loop(self, coin_id, target_price):
        """Arka planda çalışan döngü"""
        alarm_triggered = False # Sürekli bildirim atmaması için bayrak

        while self.running:
            current_price = self.get_price_safe(coin_id)
            
            if current_price:
                # Arayüzü güncelle
                self.price_label.configure(text=f"${current_price:,.2f}")
                self.log_message(f"Güncel: ${current_price:,.2f}")
                self.save_to_csv(coin_id, current_price)

                # Alarm Kontrolü
                # Hedef fiyatı geçince VEYA %5 altına düşünce alarm ver
                if current_price >= target_price and not alarm_triggered:
                    self.send_notification(f"{coin_id.upper()} HEDEFİ VURDU! 🚀", f"Fiyat: ${current_price} (Hedef: ${target_price})")
                    self.log_message("🔔 ALARM TETİKLENDİ: Hedef fiyata ulaşıldı!")
                    alarm_triggered = True # Bir kere çaldı, sustur

                elif current_price < target_price and alarm_triggered:
                    # Fiyat tekrar hedefin altına düşerse alarmı sıfırla
                    alarm_triggered = False
            
            # 30 saniye bekle (Döngüyü kırmadan bekleme yöntemi)
            for _ in range(30):
                if not self.running: break
                time.sleep(1)

if __name__ == "__main__":
    app = CryptoTrackerGUI()
    app.mainloop()