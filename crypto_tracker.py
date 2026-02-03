import requests
import time
from plyer import notification
from datetime import datetime
import csv
import os

class CryptoTracker:
    def __init__(self, coin_id, currency='usd', target_price=None):
        self.coin_id = coin_id  # Örn: 'bitcoin', 'ethereum', 'avalanche-2'
        self.currency = currency
        self.target_price = target_price
        self.api_url = "https://api.coingecko.com/api/v3/simple/price"
        self.csv_file = "fiyat_gecmisi.csv"
        
        # CSV dosyası yoksa başlıkları oluştur
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Tarih", "Coin", "Fiyat"])

    def get_price(self):
        """API'den güncel fiyatı çeker"""
        try:
            # CoinGecko botları engellemesin diye tarayıcı taklidi yapıyoruz
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            
            params = {
                'ids': self.coin_id,
                'vs_currencies': self.currency
            }
            
            # verify=False diyerek SSL hatasını görmezden geliyoruz
            response = requests.get(self.api_url, params=params, headers=headers, verify=False)
            
            data = response.json()
            price = data[self.coin_id][self.currency]
            return price
        except Exception as e:
            print(f"Hata oluştu: {e}")
            return None
        
    def log_to_csv(self, price):
        """Fiyatı tarihle birlikte kaydeder"""
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([timestamp, self.coin_id, price])
            print(f"💾 Veri kaydedildi: {timestamp} -> {price} {self.currency.upper()}")

    def send_notification(self, price, message):
        """Masaüstü bildirimi gönderir"""
        notification.notify(
            title=f"{self.coin_id.upper()} Alarmı! 🚨",
            message=f"{message}\nGüncel Fiyat: {price} {self.currency.upper()}",
            app_icon=None,  # İstersen buraya .ico dosya yolu verebilirsin
            timeout=10
        )

    def start_tracking(self, interval=60):
        """Takip döngüsünü başlatır"""
        print(f"🚀 {self.coin_id.upper()} takibi başladı... (Hedef: {self.target_price})")
        print("Çıkmak için CTRL+C yapabilirsin.")
        
        while True:
            current_price = self.get_price()
            
            if current_price:
                self.log_to_csv(current_price)
                
                # Fiyat kontrol mantığı
                if self.target_price:
                    if current_price >= self.target_price:
                        self.send_notification(current_price, "Hedef fiyata ulaşıldı! 📈 Satış zamanı mı?")
                    elif current_price <= (self.target_price * 0.95): # %5 düşüş olursa
                        self.send_notification(current_price, "Fiyat düşüyor! 📉 Alım fırsatı olabilir.")
                
            time.sleep(interval) # Belirlenen saniye kadar bekle

if __name__ == "__main__":
    # KULLANIM AYARLARI
    # coin_id: bitcoin, ethereum, ripple vs. (CoinGecko ID'si)
    # target_price: Alarmın çalmasını istediğin fiyat
    
    bot = CryptoTracker(coin_id='bitcoin', currency='usd', target_price=98000)
    
    # 30 saniyede bir kontrol et
    bot.start_tracking(interval=30)