import sys
import cv2
import mediapipe as mp
import math
import numpy as np
import time

# PySide6'nın gerekli tüm modüllerini import et
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                               QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSlider, QTextEdit)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap

# --- GÜVENLİ KÜTÜPHANE YÜKLEME ---
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    AUDIO_AVAILABLE = True
except ImportError: AUDIO_AVAILABLE = False

try:
    from pynput.keyboard import Key, Controller
    KEYBOARD_AVAILABLE = True
except ImportError: KEYBOARD_AVAILABLE = False


# ==============================================================================
#  ÇALIŞAN THREAD: TÜM EL ALGILAMA MANTIĞI BURADA ÇALIŞACAK
# ==============================================================================
class VideoThread(QThread):
    change_pixmap_signal = Signal(np.ndarray)
    log_signal = Signal(str)
    status_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._is_running = True
        self.smoothing_factor = 0.2
        self.open_palm_action_taken = False
        self.swipe_initial_pos = None
        self.swipe_action_taken = False

    def run(self):
        # Ayarlar
        W_CAM, H_CAM = 1280, 720
        SWIPE_THRESHOLD = 0.15
        
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        mp_drawing = mp.solutions.drawing_utils
        keyboard = Controller() if KEYBOARD_AVAILABLE else None

        cap = cv2.VideoCapture(0)
        if not cap.isOpened(): cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            self.status_signal.emit("HATA: Kamera bulunamadı!")
            return

        cap.set(3, W_CAM); cap.set(4, H_CAM)

        volume = None
        if AUDIO_AVAILABLE:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
            except Exception as e:
                self.log_signal.emit(f"Ses sistemi hatası: {e}"); volume = None
        
        smoothed_length = None
        
        self.status_signal.emit("Aktif: El hareketleri algılanıyor...")
        self.log_signal.emit("Algılama başlatıldı.")

        while self._is_running:
            success, image = cap.read()
            if not success: break

            image = cv2.flip(image, 1)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = hands.process(image_rgb)
            
            if results.multi_hand_landmarks:
                my_hand = results.multi_hand_landmarks[0]
                try:
                    landmarks = my_hand.landmark
                    mp_drawing.draw_landmarks(image, my_hand, mp_hands.HAND_CONNECTIONS)

                    fingers_up = []
                    # Başparmak (sağ ele göre - yatayda daha kararlı)
                    fingers_up.append(1 if landmarks[4].x < landmarks[2].x else 0)
                    # Diğer 4 parmak
                    for i in [8, 12, 16, 20]:
                        fingers_up.append(1 if landmarks[i].y < landmarks[i-2].y else 0)
                    
                    total_fingers_up = fingers_up.count(1)
                    
                    # YENİ: GÖRSEL HATA AYIKLAYICI - Ekrana parmak sayısını yaz
                    cv2.putText(image, f"Acik Parmak: {total_fingers_up}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

                    # GÜNCELLENMİŞ HAREKET TANIMLARI
                    # Not: fingers_up listesi -> [Başparmak, İşaret, Orta, Yüzük, Serçe]
                    is_open_palm = (total_fingers_up >= 4) # DÜZELTME: Daha esnek olması için >= 4 yaptık
                    is_pointing = (fingers_up[1] == 1 and fingers_up[2] == 0 and fingers_up[3] == 0 and fingers_up[4] == 0)

                    # --- HAREKET 1: ŞARKI DEĞİŞTİRME (İşaret Parmağı ile Kaydırma) ---
                    if is_pointing and keyboard:
                        if self.swipe_initial_pos is None:
                            self.swipe_initial_pos = landmarks[0].x
                            self.log_signal.emit("Kaydırma modu aktif...")
                        
                        delta_x = landmarks[0].x - self.swipe_initial_pos
                        
                        if delta_x > SWIPE_THRESHOLD and not self.swipe_action_taken:
                            keyboard.press(Key.media_next); keyboard.release(Key.media_next)
                            self.log_signal.emit(">> Sonraki Şarkı")
                            self.swipe_action_taken = True
                        
                        elif delta_x < -SWIPE_THRESHOLD and not self.swipe_action_taken:
                            keyboard.press(Key.media_previous); keyboard.release(Key.media_previous)
                            self.log_signal.emit("<< Önceki Şarkı")
                            self.swipe_action_taken = True
                            
                        cv2.putText(image, ">> KAYDIR >>", (W_CAM // 2, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 255), 3)

                    # --- HAREKET 2: PLAY/PAUSE (Açık El ile) ---
                    elif is_open_palm and keyboard:
                        self.swipe_initial_pos = None # Diğer modların durumunu sıfırla
                        if not self.open_palm_action_taken:
                            keyboard.press(Key.media_play_pause)
                            keyboard.release(Key.media_play_pause)
                            self.log_signal.emit("Açık El: Play/Pause komutu gönderildi.")
                            self.open_palm_action_taken = True
                        
                        cv2.putText(image, "✋ PLAY/PAUSE", (50, 50), cv2.FONT_HERSHEY_COMPLEX, 1.2, (0, 0, 255), 3)

                    # --- HAREKET 3: SES KONTROLÜ (Diğer tüm durumlarda) ---
                    else: # DÜZELTME: Bu bir 'elif' yerine 'else' olmalı ki varsayılan durum olsun
                        self.open_palm_action_taken = False
                        self.swipe_initial_pos = None
                        self.swipe_action_taken = False

                        if volume:
                            thumb_tip = landmarks[4]; index_tip = landmarks[8]
                            raw_length = math.hypot(index_tip.x - thumb_tip.x, index_tip.y - thumb_tip.y)
                            if smoothed_length is None: smoothed_length = raw_length
                            else: smoothed_length = self.smoothing_factor * raw_length + (1 - self.smoothing_factor) * smoothed_length
                            
                            vol_level_scalar = np.interp(smoothed_length, [0.03, 0.25], [0, 1])
                            volume.SetMasterVolumeLevelScalar(vol_level_scalar, None)
                except Exception as e:
                    self.log_signal.emit(f"HATA: {e}")

            else:
                self.open_palm_action_taken = False
                self.swipe_initial_pos = None
                self.swipe_action_taken = False
                
            self.change_pixmap_signal.emit(image)
        
        cap.release()
        self.status_signal.emit("Durduruldu.")
        self.log_signal.emit("Algılama durduruldu.")

    def stop(self):
        self._is_running = False
        self.quit()
        self.wait()

# ==============================================================================
# ANA PENCERE (GUI) SINIFI - HİÇBİR DEĞİŞİKLİK GEREKMİYOR
# (Bu kısım tamamen aynı kalabilir)
# ==============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("El Hareketi Kontrolcüsü v11 - Hata Ayıklama Modu")
        # ... (Geri kalan tüm MainWindow kodu bir öncekiyle aynıdır)
        # ... Sadece kopyalayıp yapıştırabilirsiniz.
        self.setGeometry(100, 100, 1200, 600)
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        left_panel_layout = QVBoxLayout()
        left_panel_container = QWidget()
        left_panel_container.setLayout(left_panel_layout)
        left_panel_container.setFixedWidth(250)
        title_label = QLabel("KONTROL PANELİ")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold; margin-bottom: 10px;")
        self.start_button = QPushButton("Algılamayı Başlat")
        self.start_button.setStyleSheet("background-color: green; color: white; font-size: 12pt; padding: 5px;")
        self.stop_button = QPushButton("Algılamayı Durdur")
        self.stop_button.setStyleSheet("background-color: red; color: white; font-size: 12pt; padding: 5px;")
        self.stop_button.setEnabled(False)
        self.status_label = QLabel("Durum: Beklemede")
        self.status_label.setStyleSheet("font-size: 11pt; margin-top: 10px;")
        smoothing_label = QLabel("Yumuşatma Faktörü (Düşük = Yumuşak)")
        self.smoothing_slider = QSlider(Qt.Orientation.Horizontal)
        self.smoothing_slider.setRange(1, 9); self.smoothing_slider.setValue(2); self.smoothing_slider.setTickInterval(1); self.smoothing_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        log_label = QLabel("Olay Kayıtları"); self.log_box = QTextEdit(); self.log_box.setReadOnly(True)
        left_panel_layout.addWidget(title_label); left_panel_layout.addWidget(self.start_button); left_panel_layout.addWidget(self.stop_button); left_panel_layout.addWidget(self.status_label)
        left_panel_layout.addStretch(); left_panel_layout.addWidget(smoothing_label); left_panel_layout.addWidget(self.smoothing_slider); left_panel_layout.addStretch()
        left_panel_layout.addWidget(log_label); left_panel_layout.addWidget(self.log_box)
        self.video_label = QLabel("Başlatmak için butona basın."); self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.video_label.setStyleSheet("background-color: black; color: white; font-size: 20pt;")
        main_layout.addWidget(left_panel_container); main_layout.addWidget(self.video_label)
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.log_signal.connect(self.add_to_log)
        self.thread.status_signal.connect(self.set_status)
        self.start_button.clicked.connect(self.start_video_thread)
        self.stop_button.clicked.connect(self.stop_video_thread)
        self.smoothing_slider.valueChanged.connect(self.update_smoothing_factor)
    def update_image(self, cv_img):
        h, w, ch = cv_img.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(cv_img.data, w, h, bytes_per_line, QImage.Format.Format_BGR888)
        p = QPixmap.fromImage(convert_to_Qt_format)
        self.video_label.setPixmap(p)
    def add_to_log(self, text):
        self.log_box.append(text)
    def set_status(self, text):
        self.status_label.setText(f"Durum: {text}")
    def update_smoothing_factor(self, value):
        self.thread.smoothing_factor = value / 10.0
        self.add_to_log(f"Yumuşatma faktörü {self.thread.smoothing_factor:.1f} olarak ayarlandı.")
    def start_video_thread(self):
        self.log_box.clear()
        self.thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
    def stop_video_thread(self):
        self.thread.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.video_label.setText("Durduruldu. Tekrar başlatabilirsiniz.")
        self.video_label.setStyleSheet("background-color: black; color: white; font-size: 20pt;")
    def closeEvent(self, event):
        self.stop_video_thread()
        event.accept()

# --- UYGULAMAYI BAŞLATMA ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())