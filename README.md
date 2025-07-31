# 🎮 Hand Controller v4 - El Hareketi ile Bilgisayar Kontrolü

**Gelişmiş el hareketlerini kullanarak bilgisayarınızın ses seviyesini ve müzik çalarını kontrol edin!**

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-green.svg)](https://opencv.org)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-red.svg)](https://mediapipe.dev)

## 🌟 Özellikler

### 🔊 Ses Kontrolü
- **🤏 Pinch Hareketi**: Başparmak ve işaret parmağını yaklaştırıp uzaklaştırarak ses seviyesini kontrol edin
- **Stabilize Algoritma**: Titreşimi önleyen akıllı filtreleme sistemi
- **Görsel Geri Bildirim**: Renk kodlu ses çubuğu (yeşil → sarı → kırmızı)
- **Gerçek Zamanlı Gösterge**: Parmak mesafesi ve ses seviyesi bilgileri

### 🎵 Müzik Kontrolü
- **✌️ Peace İşareti**: 1.5 saniye tutarak güvenli play/pause
- **✊ Yumruk**: Anında acil play/pause (2 saniye cooldown)
- **Döngü Koruması**: Kazara tekrar tetiklenmesi önlendi

### 🛡️ Güvenlik & Stabilite
- **Akıllı Kütüphane Kontrolü**: Eksik kütüphaneler olsa bile çalışır
- **Çoklu Kamera Desteği**: Otomatik kamera algılama (0, 1, 2)
- **Kapsamlı Hata Yönetimi**: Crash-proof tasarım
- **Güvenli Çıkış**: Q, ESC veya Ctrl+C ile temiz kapatma

## 📋 Sistem Gereksinimleri

- **İşletim Sistemi**: Windows 10/11
- **Python**: 3.7 veya üzeri
- **Kamera**: USB veya dahili webcam
- **RAM**: Minimum 4GB (8GB önerilir)

## 🚀 Kurulum

### 1. Repository'yi İndirin
```bash
git clone https://github.com/kullaniciadi/hand-controller.git
cd hand-controller
```

### 2. Gerekli Kütüphaneleri Kurun
```bash
# Temel kütüphaneler
pip install opencv-python mediapipe numpy

# Ses kontrolü için (Windows)
pip install pycaw comtypes

# Klavye kontrolü için
pip install pynput
```

### 3. Programı Çalıştırın
```bash
python HandController.py
```

**⚠️ Önemli**: Ses kontrolü için programı **yönetici olarak** çalıştırmanız gerekebilir.

## 🎯 Kullanım Kılavuzu

### Ses Kontrolü 🔊
1. **Kameranın karşısına geçin**
2. **Başparmak ve işaret parmağınızı yaklaştırın** (Pinch hareketi)
3. **Parmakları yaklaştırın** → Ses azalır
4. **Parmakları uzaklaştırın** → Ses artar
5. **Stabilite göstergesi** (●/○) ile değişiklikleri takip edin

### Müzik Kontrolü 🎵

#### ✌️ Peace İşareti (Güvenli Mod)
- İşaret ve orta parmağınızı kaldırın (V şekli)
- **1.5 saniye** tutun
- "HAZIRLANILIYOR..." mesajını bekleyin
- Play/Pause komutu otomatik gönderilir

#### ✊ Yumruk (Acil Mod)
- Tüm parmakları kapalı tutun
- **Anında** tetiklenir
- 2 saniye cooldown vardır

### Çıkış
- **Q** tuşuna basın
- **ESC** tuşuna basın
- **Ctrl+C** ile durdurun

## 🔧 Teknik Detaylar

### Hareket Tanıma Algoritması
```python
# Pinch hareketi algılama
thumb_index_distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
is_pinch_gesture = thumb_index_distance < 0.15

# Stabilite kontrolü
volume_change_cooldown = 0.1  # 100ms
volume_threshold = 0.05       # %5 minimum değişim
```

### Ses Kontrolü Optimizasyonu
- **100ms Cooldown**: Saniyede maksimum 10 değişiklik
- **%5 Threshold**: Küçük titreşimler filtrelenir
- **Adaptive Range**: 0.01-0.12 mesafe aralığı optimized

### MediaPipe Landmark İndeksleri
```python
THUMB_TIP = 4      # Başparmak ucu
INDEX_TIP = 8      # İşaret parmağı ucu
MIDDLE_TIP = 12    # Orta parmak ucu
RING_TIP = 16      # Yüzük parmağı ucu
PINKY_TIP = 20     # Serçe parmağı ucu
```

## 🐛 Sorun Giderme

### Kamera Bulunamadı
```bash
# Kamera indekslerini test edin
python -c "import cv2; print([i for i in range(5) if cv2.VideoCapture(i).isOpened()])"
```

### Ses Kontrolü Çalışmıyor
1. **Yönetici olarak çalıştırın**
2. **Windows ses ayarlarını kontrol edin**
3. **Antivirus yazılımı engelleme kontrolü**

### MediaPipe Hatası
```bash
# MediaPipe'ı yeniden kurun
pip uninstall mediapipe
pip install mediapipe
```

### Performans Sorunları
- **Kamera çözünürlüğünü düşürün**: `W_CAM, H_CAM = 640, 480`
- **Detection confidence azaltın**: `min_detection_confidence=0.5`
- **Arka plan uygulamalarını kapatın**

## 📊 Debug Modu

Program çalışırken şu bilgileri gösterir:
- **Landmark sayısı**: El algılama durumu
- **Parmak mesafesi**: Pinch hassasiyet kontrolü
- **Ses seviyesi**: Gerçek zamanlı değerler
- **Stabilite durumu**: ● (aktif) / ○ (beklemede)

## 🎨 Görsel Göstergeler

| Gösterge | Anlamı |
|----------|--------|
| 🤏 PINCH SES KONTROLU | Ses kontrolü aktif |
| ✌️ PEACE PLAY/PAUSE | Peace hareketi algılandı |
| ✊ ACIL PLAY/PAUSE | Yumruk hareketi tetiklendi |
| ● Yeşil nokta | Ses değişiyor |
| ○ Gri nokta | Stabil/beklemede |
| Yeşil çubuk | Düşük ses (0-30%) |
| Sarı çubuk | Orta ses (30-70%) |
| Kırmızı çubuk | Yüksek ses (70-100%) |

## 🔄 Versiyon Geçmişi

### v4.0 (Güncel)
- ✅ Pinch hareketi ile ses kontrolü
- ✅ Stabilite optimizasyonu
- ✅ Gelişmiş hata yönetimi
- ✅ Çoklu kamera desteği

### v3.0
- ✅ Peace işareti play/pause
- ✅ Yumruk acil kontrolü
- ✅ Cooldown sistemi

### v2.0
- ✅ MediaPipe entegrasyonu
- ✅ Temel el tanıma

### v1.0
- ✅ İlk versiyon
- ✅ Basit hareket kontrolü


## 🙏 Teşekkürler

- **Google MediaPipe** - El tanıma teknolojisi
- **OpenCV** - Bilgisayar görüşü kütüphanesi  
- **PyCaw** - Windows ses kontrolü
- **PyNput** - Klavye kontrolü
- 
---

<div align="center">

**⭐ Eğer bu proje faydalıysa yıldız vermeyi unutmayın! ⭐**

Made with ❤️ by Isa Senturk

</div>
