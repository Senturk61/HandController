import cv2
import mediapipe as mp
import math
import numpy as np
import time
import sys

# Ses kontrolü için gerekli kütüphaneleri güvenli şekilde import et
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    AUDIO_AVAILABLE = True
    print("Ses kontrolü aktif")
except ImportError as e:
    print(f"Ses kontrolü kütüphaneleri bulunamadı: {e}")
    print("Ses kontrolü devre dışı - sadece görüntü işleme çalışacak")
    AUDIO_AVAILABLE = False

try:
    from pynput.keyboard import Key, Controller
    KEYBOARD_AVAILABLE = True
    print("Klavye kontrolü aktif")
except ImportError as e:
    print(f"Klavye kontrolü kütüphanesi bulunamadı: {e}")
    print("Klavye kontrolü devre dışı")
    KEYBOARD_AVAILABLE = False

# --- 1. Başlangıç Ayarları ---
W_CAM, H_CAM = 1280, 720

# Klavye kontrolcüsünü güvenli şekilde başlat
if KEYBOARD_AVAILABLE:
    try:
        keyboard = Controller()
    except Exception as e:
        print(f"Klavye kontrolcüsü başlatılamadı: {e}")
        KEYBOARD_AVAILABLE = False

# MediaPipe ayarları
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Kamera başlatma - güvenli mod
print("Kamera başlatılıyor...")
cap = cv2.VideoCapture(0)

# Kamera alternatiflerini dene
if not cap.isOpened():
    print("Kamera 0 açılamadı, kamera 1 deneniyor...")
    cap = cv2.VideoCapture(1)
    
if not cap.isOpened():
    print("Kamera 1 açılamadı, kamera 2 deneniyor...")
    cap = cv2.VideoCapture(2)

if not cap.isOpened():
    print("HATA: Hiçbir kamera bulunamadı!")
    print("Lütfen kameranızın bağlı ve çalışır durumda olduğundan emin olun.")
    sys.exit(1)

print("Kamera başarıyla açıldı!")
cap.set(3, W_CAM)
cap.set(4, H_CAM)

# Ses kontrolü başlatma - güvenli mod
volume = None
vol_range = None
min_vol = 0
max_vol = 1

if AUDIO_AVAILABLE:
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        vol_range = volume.GetVolumeRange()
        min_vol = vol_range[0]
        max_vol = vol_range[1]
        print("Ses sistemi başarıyla bağlandı!")
    except Exception as e:
        print(f"Ses sistemi bağlanamadı: {e}")
        print("Ses kontrolü devre dışı bırakılıyor...")
        AUDIO_AVAILABLE = False
        volume = None

# Zamanlama ayarları
cooldown = 2.0  # Play/pause için bekleme süresi artırıldı
last_action_time = 0
gesture_start_time = 0
gesture_hold_duration = 1.5  # Hareketin ne kadar süre tutulması gerekiyor

# Ses kontrolü için stabilite ayarları
last_volume_change_time = 0
volume_change_cooldown = 0.1  # 100ms'de bir ses değişikliği
last_volume_level = -1  # Son ses seviyesi
volume_threshold = 0.05  # Minimum değişim miktarı

print("\n" + "="*50)
print("🎮 EL HAREKETİ KONTROLCÜSÜ v4 - GÜVENLİ MOD")
print("="*50)
print("📹 Kamera: Aktif")
print(f"🔊 Ses Kontrolü: {'Aktif' if AUDIO_AVAILABLE else 'Devre Dışı'}")
print(f"⌨️  Klavye Kontrolü: {'Aktif' if KEYBOARD_AVAILABLE else 'Devre Dışı'}")
print("\n📋 YENİ Kullanım:")
print("   🔊 SES KONTROLÜ:")
print("      • 🤏 PINCH = Başparmak + İşaret parmağı yaklaştır/uzaklaştır")
print("      • Yakın = Sessiz, Uzak = Yüksek ses")
print("   🎵 MÜZİK KONTROLÜ:")
print("      • ✌️ Peace işareti (1.5sn) = Play/Pause (Güvenli)")
print("      • ✊ Yumruk (anında) = Acil Play/Pause")
print("   ❌ Çıkmak için 'q' tuşuna basın")
print("="*50)

# --- 2. Ana Döngü ---
frame_count = 0

try:
    while True:
        success, image = cap.read()
        if not success:
            print("Kamera görüntüsü alınamadı!")
            break

        frame_count += 1
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # MediaPipe işleme
        try:
            results = hands.process(image_rgb)
        except Exception as e:
            print(f"MediaPipe işleme hatası: {e}")
            continue

        # Durum bilgileri ekrana yazdır
        status_color = (0, 255, 0) if AUDIO_AVAILABLE else (0, 0, 255)
        cv2.putText(image, f"Ses: {'ON' if AUDIO_AVAILABLE else 'OFF'}", 
                   (W_CAM-150, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        keyboard_color = (0, 255, 0) if KEYBOARD_AVAILABLE else (0, 0, 255)
        cv2.putText(image, f"Klavye: {'ON' if KEYBOARD_AVAILABLE else 'OFF'}", 
                   (W_CAM-150, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, keyboard_color, 2)

        if results.multi_hand_landmarks:
            my_hand = results.multi_hand_landmarks[0]
            
            try:
                landmarks = my_hand.landmark
                mp_drawing.draw_landmarks(image, my_hand, mp_hands.HAND_CONNECTIONS)

                # Landmark sayısını kontrol et ve güvenli şekilde al
                if len(landmarks) < 21:
                    print(f"Yetersiz landmark: {len(landmarks)}/21")
                    continue
                    
                try:
                    # Landmark indekslerini direkt sayı ile al (daha güvenli)
                    thumb_tip = landmarks[4]      # THUMB_TIP
                    index_tip = landmarks[8]      # INDEX_FINGER_TIP
                    middle_tip = landmarks[12]    # MIDDLE_FINGER_TIP
                    ring_tip = landmarks[16]      # RING_FINGER_TIP
                    pinky_tip = landmarks[20]     # PINKY_TIP
                    
                    index_pip = landmarks[6]      # INDEX_FINGER_PIP
                    middle_pip = landmarks[10]    # MIDDLE_FINGER_PIP
                    ring_pip = landmarks[14]      # RING_FINGER_PIP
                    pinky_pip = landmarks[18]     # PINKY_FINGER_PIP
                    
                    # Koordinatları kontrol et (bazen None olabiliyor)
                    if any(point is None for point in [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip]):
                        print("Bazı landmark noktaları None!")
                        continue
                        
                except (IndexError, AttributeError) as e:
                    print(f"Landmark erişim hatası: {e}")
                    cv2.putText(image, f"Landmark Hatasi: {len(landmarks)}", (50, 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)
                    continue
                
                # Hareketleri güvenli şekilde tanımla
                try:
                    # YENİ: Başparmak + İşaret parmağı ile ses kontrolü (Pinch hareketi)
                    thumb_index_distance = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
                    
                    # Ses kontrolü: Başparmak ve işaret parmağı yakınken
                    is_pinch_gesture = thumb_index_distance < 0.15  # Parmaklar yeterince yakın mı?
                    
                    # Diğer parmakların durumu kontrol et (ses kontrolü için)
                    middle_up = middle_tip.y < middle_pip.y
                    ring_down = ring_tip.y > ring_pip.y
                    pinky_down = pinky_tip.y > pinky_pip.y
                    
                    # Play/Pause: "OK" işareti - başparmak + işaret çok yakın, diğerleri yukarı
                    ring_up = ring_tip.y < ring_pip.y
                    pinky_up = pinky_tip.y < pinky_pip.y
                    is_ok_gesture = (thumb_index_distance < 0.05 and 
                                    middle_up and ring_up and pinky_up)
                    
                    # Yumruk: Tüm parmaklar kapalı
                    all_fingers_down = (index_tip.y > index_pip.y and 
                                       middle_tip.y > middle_pip.y and
                                       ring_tip.y > ring_pip.y and 
                                       pinky_tip.y > pinky_pip.y)
                    
                    # YENİ: "Peace" işareti - alternatif Play/Pause
                    index_up = index_tip.y < index_pip.y
                    is_peace_gesture = (index_up and middle_up and ring_down and pinky_down and
                                       abs(index_tip.x - middle_tip.x) > 0.05)
                    
                    # Debug bilgisi ekle
                    cv2.putText(image, f"Landmarks: {len(landmarks)}", (50, 100), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    cv2.putText(image, f"Thumb-Index: {thumb_index_distance:.3f}", (50, 120), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                    
                except AttributeError as e:
                    print(f"Hareket tanıma hatası: {e}")
                    print(f"Thumb tip type: {type(thumb_tip)}")
                    continue

                # HAREKET 1: Ses Kontrol Modu - Başparmak + İşaret Parmağı (Pinch) - STABİLİZE EDİLMİŞ
                if is_pinch_gesture and AUDIO_AVAILABLE and volume is not None:
                    try:
                        current_time = time.time()
                        
                        cv2.putText(image, "🤏 PINCH SES KONTROLU", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 3)
                        
                        # Mesafe hesapla - başparmak ve işaret parmağı arası
                        length = thumb_index_distance
                        vol_level_scalar = np.interp(length, [0.01, 0.12], [0, 1])  # Daha dar aralık, hassas kontrol
                        vol_level_scalar = max(0, min(1, vol_level_scalar))  # 0-1 arası sınırla
                        
                        # STABİLİTE KONTROLÜ: Sadece belirli koşullarda ses değiştir
                        should_change_volume = False
                        
                        # İlk kez ses kontrolü yapılıyorsa
                        if last_volume_level == -1:
                            should_change_volume = True
                            
                        # Yeterli zaman geçti mi?
                        elif (current_time - last_volume_change_time) > volume_change_cooldown:
                            # Yeterince büyük değişiklik var mı?
                            volume_difference = abs(vol_level_scalar - last_volume_level)
                            if volume_difference > volume_threshold:
                                should_change_volume = True
                        
                        # Ses seviyesini değiştir (sadece gerektiğinde)
                        if should_change_volume:
                            volume.SetMasterVolumeLevelScalar(vol_level_scalar, None)
                            last_volume_level = vol_level_scalar
                            last_volume_change_time = current_time
                            print(f"Ses değişti: {int(vol_level_scalar * 100)}%")
                        else:
                            # Mevcut ses seviyesini kullan
                            vol_level_scalar = last_volume_level if last_volume_level != -1 else vol_level_scalar
                        
                        # YENİ: Daha büyük ve renkli görsel gösterge
                        bar_height = int(np.interp(vol_level_scalar, [0, 1], [350, 100]))
                        
                        # Ses çubuğu - gradient etkisi
                        cv2.rectangle(image, (30, 100), (80, 350), (100, 100, 100), 3)
                        
                        # Ses seviyesine göre renk değişimi
                        if vol_level_scalar < 0.3:
                            color = (0, 255, 0)  # Yeşil - düşük
                        elif vol_level_scalar < 0.7:
                            color = (0, 255, 255)  # Sarı - orta
                        else:
                            color = (0, 100, 255)  # Kırmızı - yüksek
                            
                        cv2.rectangle(image, (30, bar_height), (80, 350), color, cv2.FILLED)
                        
                        # Ses yüzdesi - daha büyük font
                        cv2.putText(image, f'{int(vol_level_scalar * 100)}%', 
                                   (20, 380), cv2.FONT_HERSHEY_COMPLEX, 1.2, color, 3)
                        
                        # Parmak mesafesi göstergesi
                        cv2.putText(image, f'Mesafe: {length:.3f}', 
                                   (20, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                        # STABİLİTE göstergesi
                        stability_color = (0, 255, 0) if should_change_volume else (100, 100, 100)
                        cv2.putText(image, "●" if should_change_volume else "○", 
                                   (90, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, stability_color, 3)
                        
                        # Parmaklar arası çizgi çiz
                        thumb_x, thumb_y = int(thumb_tip.x * W_CAM), int(thumb_tip.y * H_CAM)
                        index_x, index_y = int(index_tip.x * W_CAM), int(index_tip.y * H_CAM)
                        cv2.line(image, (thumb_x, thumb_y), (index_x, index_y), color, 3)
                        cv2.circle(image, (thumb_x, thumb_y), 8, (255, 0, 0), -1)  # Mavi nokta
                        cv2.circle(image, (index_x, index_y), 8, (0, 255, 0), -1)  # Yeşil nokta
                        
                    except Exception as e:
                        print(f"Ses kontrolü hatası: {e}")
                        cv2.putText(image, "SES HATASI!", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)

                # HAREKET 2: Play/Pause - Peace İşareti ile (V)
                elif is_peace_gesture and KEYBOARD_AVAILABLE:
                    current_time = time.time()
                    
                    # İlk kez Peace işareti yapıldığında zamanlayıcıyı başlat
                    if gesture_start_time == 0:
                        gesture_start_time = current_time
                    
                    # Hareket yeterince uzun süre tutuldu mu?
                    hold_time = current_time - gesture_start_time
                    
                    if hold_time >= gesture_hold_duration and (current_time - last_action_time) > cooldown:
                        try:
                            cv2.putText(image, "✌️ PEACE PLAY/PAUSE!", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                            keyboard.press(Key.media_play_pause)
                            keyboard.release(Key.media_play_pause)
                            last_action_time = current_time
                            gesture_start_time = 0  # Sıfırla
                            print("Peace Play/Pause komutu gönderildi")
                        except Exception as e:
                            print(f"Klavye kontrolü hatası: {e}")
                            cv2.putText(image, "KLAVYE HATASI!", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                    else:
                        # Bekleme durumu göster
                        remaining = gesture_hold_duration - hold_time
                        if remaining > 0:
                            cv2.putText(image, f"✌️ HAZIRLANILIYOR... {remaining:.1f}s", 
                                       (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255), 3)
                        
                # HAREKET 3: Yumruk - Acil Play/Pause (hızlı ama tek seferlik)
                elif all_fingers_down and KEYBOARD_AVAILABLE:
                    current_time = time.time()
                    if (current_time - last_action_time) > cooldown:
                        try:
                            cv2.putText(image, "✊ ACIL PLAY/PAUSE!", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)
                            keyboard.press(Key.media_play_pause)
                            keyboard.release(Key.media_play_pause)
                            last_action_time = current_time
                            print("Acil Play/Pause komutu gönderildi")
                        except Exception as e:
                            print(f"Klavye kontrolü hatası: {e}")
                            cv2.putText(image, "KLAVYE HATASI!", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                
                else:
                    # Hareket tanınmadığında zamanlayıcıyı sıfırla
                    gesture_start_time = 0
                
                # Hareket tanınmadığında
                if is_pinch_gesture and not AUDIO_AVAILABLE:
                    cv2.putText(image, "SES SİSTEMİ YOK!", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)
                elif (is_peace_gesture or all_fingers_down) and not KEYBOARD_AVAILABLE:
                    cv2.putText(image, "KLAVYE SİSTEMİ YOK!", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 3)

            except Exception as e:
                print(f"El işleme hatası (Frame {frame_count}): {e}")
                cv2.putText(image, "EL İŞLEME HATASI!", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 255), 3)

        # Kullanım talimatlarını ekranda göster
        cv2.putText(image, "Cikis icin 'q' basin", (10, H_CAM-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("🎮 El Hareketi Kontrolcusu v4", image)
        
        # Çıkış kontrolü
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q') or key == 27:  # q, Q veya ESC
            print("Çıkış tuşu algılandı...")
            break

except KeyboardInterrupt:
    print("\nKullanici tarafindan durduruldu (Ctrl+C)")
except Exception as e:
    print(f"Beklenmeyen hata: {e}")
    print("Program güvenli şekilde kapatılıyor...")

finally:
    # Temizlik işlemleri
    print("Sistem kapatılıyor...")
    if 'cap' in locals():
        cap.release()
    cv2.destroyAllWindows()
    print("✅ Sistem başarıyla kapatıldı.")
    print("Teşekkürler! 👋")