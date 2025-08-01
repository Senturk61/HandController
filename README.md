# El Hareketi Kontrolcüsü - GUI v2.0

<img width="1499" height="785" alt="image" src="https://github.com/user-attachments/assets/74a238ec-6187-4ed1-9acf-2d1f7a3304b3" />

<img width="1920" height="1031" alt="image" src="https://github.com/user-attachments/assets/f2827cca-c3eb-449d-aa2d-f85bda2b8596" />


Bu proje, `OpenCV` ile görüntü işlemeyi, `MediaPipe` ile gerçek zamanlı el takibini ve `PySide6` ile tam teşekküllü bir kullanıcı arayüzünü bir araya getirir. Arka planda çalışan sağlam bir multithread yapısı sayesinde, arayüz donmadan akıcı bir kontrol deneyimi sunar.

## ✨ Öne Çıkan Özellikler

- **Modern Arayüz:** PySide6 ile oluşturulmuş, kullanıcı dostu ve sezgisel kontrol paneli.
- **Canlı Kontrol:** Arayüz üzerinden el takibini başlatma, durdurma ve ayarları anlık olarak değiştirme.
- **Akıcı Ses Ayarı:** "Pinch" hareketiyle, titreşimi engelleyen yumuşatma filtresi sayesinde hassas ses kontrolü.
- **Ayarlanabilir Hassasiyet:** Arayüzdeki kaydıraç ile ses kontrolünün yumuşaklığını canlı olarak ayarlayabilme.
- **Net Medya Hareketleri:** Yanlış algılamaları önleyen, sezgisel Play/Pause ve Şarkı Değiştirme hareketleri.
- **Olay Kayıt Paneli:** Algılanan tüm hareketleri ve uygulama durumunu anlık olarak gösteren log ekranı.
- **Sağlam Mimari:** Arayüz (GUI) ve el algılama (Worker) işlemlerini ayıran `multithread` yapı sayesinde %100 kararlı çalışma.
- **Kolay Dağıtım:** PyInstaller ile tek bir `.exe` dosyasına dönüştürülerek kolayca paylaşılabilme.

## 🖐️ Tanımlı Hareketler

| Hareket | Eylem | Açıklama |
| :---: | :--- | :--- |
| 🤏 **Pinch** | Ses Ayarı | Başparmak ve işaret parmağınız arasındaki mesafeyi değiştirerek sesi hassas bir şekilde ayarlayın. |
| ✋ **Açık El** | Play / Pause | Elinizi kameraya doğru beş parmağınız açık şekilde gösterin. (Tek seferlik tetiklenir) |
| 👆 + ↔️ **Kaydırma** | Şarkı Değiştirme | İşaret parmağınızı kaldırın ve elinizi sağa (sonraki) veya sola (önceki) doğru kaydırın. |

## 🚀 Kurulum (Kaynak Koddan Çalıştırmak İçin)

Projeyi kendi bilgisayarınızda geliştirmek veya çalıştırmak için aşağıdaki adımları izleyin:

1.  **Projeyi klonlayın:**
    ```bash
    git clone [https://github.com/Senturk61/HandController.git](https://github.com/Senturk61/HandController.git)
    cd HandController
    ```

2.  **Sanal bir ortam oluşturun ve aktive edin (Tavsiye edilir):**
    ```bash
    python -m venv venv
    # Windows için:
    .\venv\Scripts\activate
    ```

3.  **Gerekli kütüphaneleri `requirements.txt` dosyası ile yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Eğer `requirements.txt` dosyası yoksa, aşağıdaki komutlarla manuel olarak kurabilirsiniz.)*
    ```bash
    pip install opencv-python mediapipe numpy pyside6 pycaw comtypes pynput
    ```

## 💻 Kullanım

### A. `.exe` Dosyası ile (En Kolay Yöntem)
1.  GitHub sayfasındaki "Releases" bölümünden en son `.exe` dosyasını indirin.
2.  **"El Hareketi Kontrolcusu.exe"** dosyasına çift tıklayarak çalıştırın.
3.  Arayüzdeki **"Algılamayı Başlat"** butonuna basın.

### B. Kaynak Koddan
1.  Kurulum adımlarını tamamladığınızdan emin olun.
2.  Terminalde aşağıdaki komutu çalıştırın:
    ```bash
    python HandControllerGUI.py
    ```
3.  Arayüzdeki **"Algılamayı Başlat"** butonuna basın.

## 🔧 `.exe` Oluşturma

Projeyi dağıtılabilir tek bir `.exe` dosyası haline getirmek için:

1.  **PyInstaller'ı kurun:**
    ```bash
    pip install pyinstaller
    ```
2.  **`.spec` dosyasını oluşturun:** Terminalde ilk olarak aşağıdaki komutu çalıştırın. Bu komut `RecursionError` hatası vererek duracaktır, bu normaldir. Amacımız sadece `.spec` dosyasını oluşturmak.
    ```bash
    pyinstaller --windowed --name "El Hareketi Kontrolcusu" HandControllerGUI.py
    ```
3.  **`.spec` dosyasını düzenleyin:** Proje klasörünüzde oluşan `"El Hareketi Kontrolcusu.spec"` dosyasını bir metin düzenleyici ile açın ve en üst satırına şunu ekleyin:
    ```python
    import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)
    ```
4.  **`.spec` dosyası ile paketlemeyi tamamlayın (Tırnak işaretleri önemli!):**
    ```bash
    pyinstaller "El Hareketi Kontrolcusu.spec"
    ```
5.  Oluşturulan `.exe` dosyası `dist` klasörünün içinde yer alacaktır.

## 🛠️ Kullanılan Teknolojiler

- **Python 3.11**
- **PySide6:** Modern masaüstü arayüzü.
- **OpenCV-Python:** Görüntü işleme ve kamera yönetimi.
- **MediaPipe:** Gerçek zamanlı el takibi.
- **pycaw & comtypes:** Windows için sistemsel ses kontrolü.
- **pynput:** Klavye tuşlarını simüle ederek medya kontrolü.

## 🔄 Versiyon Geçmişi

### **v2.0 - GUI Sürümü (Güncel)**
- ✅ PySide6 ile tam teşekküllü masaüstü arayüzüne geçildi.
- ✅ Arayüz ve el algılama motoru için multithread mimari eklendi.
- ✅ Başlat/Durdur butonu, hassasiyet kaydıracı ve olay kayıt paneli eklendi.
- ✅ Şarkı değiştirme için "kaydırma" hareketi eklendi.
- ✅ Play/Pause için "açık el" hareketi tanımlandı.
- ✅ `.exe` paketleme talimatları güncellendi.

### **v1.0 - Komut Satırı Sürümü**
- ✅ OpenCV penceresi üzerinden temel görselleştirme.
- ✅ "Pinch", "Yumruk" ve "Peace" hareketleri ile kontrol.
- ✅ Titreşim önleyici stabilite algoritmaları.
- ✅ Akıllı kütüphane ve çoklu kamera desteği.

---

<div align="center">

**⭐ Eğer bu proje faydalıysa yıldız vermeyi unutmayın! ⭐**

Isa Senturk tarafından ❤️ ile yapılmıştır.

</div>
