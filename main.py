import json
import os
import streamlit as st
from google import genai

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="LGS Hazırlık Asistanı - Modern Web Sürümü",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- MODERN ÖZEL CSS TASARIMI ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #4361ee;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1rem;
        width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #3a0ca3;
        color: white;
        box-shadow: 0 4px 12px rgba(67, 97, 238, 0.3);
    }
    .question-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- VERİ VE ÜNİTE YAPILARI ---
DERS_UNITELERI = {
    "Matematik": [
        "Çarpanlar ve Katlar", 
        "Üslü İfadeler", 
        "Kareköklü İfadeler", 
        "Veri Analizi", 
        "Basit Olayların Olma Olasılığı", 
        "Cebirsel İfadeler ve Özdeşlikler"
    ],
    "Fen Bilimleri": [
        "Mevsimler ve İklim", 
        "DNA ve Genetik Kod", 
        "Basınç", 
        "Madde ve Endüstri", 
        "Basit Makineler", 
        "Enerji Dönüşümleri", 
        "Elektrik Yükleri"
    ],
    "Türkçe": [
        "Sözcükte ve Cümlede Anlam", 
        "Parçada Anlam", 
        "Fiilimsiler", 
        "Cümlenin Ögeleri", 
        "Yazım Kuralları ve Noktalama", 
        "Metin Türleri ve Söz Sanatları"
    ],
    "İnkılap Tarihi": [
        "Bir Kahraman Doğuyor", 
        "Milli Uyanış: Bağımsızlık Yolunda Adımlar", 
        "Ya İstiklal Ya Ölüm", 
        "Atatürkçülük ve Çağdaşlaşan Türkiye", 
        "Demokratikleşme Yolundaki Adımlar"
    ]
}

VERitabani_DOSYASI = "lgs_veritabani.json"

def veri_yukle():
    if os.path.exists(VERitabani_DOSYASI):
        try:
            with open(VERitabani_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("dersler", {}), data.get("videolar", [])
        except Exception:
            pass
    
    varsayilan_dersler = {
        "Matematik": [{
            "unite": "Çarpanlar ve Katlar",
            "zorluk": "Orta",
            "tip": "Soru Bankası",
            "soru": "Örnek Soru: 18 ve 24 sayısal değerlerinin en büyük ortak böleni (EBOB) kaçtır?",
            "secenekler": ["A) 3", "B) 6", "C) 9", "D) 12"],
            "cevap": "B"
        }]
    }
    varsayilan_videolar = [
        {"baslik": "Matematik - Çarpanlar ve Katlar Konu Anlatımı", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    ]
    return varsayilan_dersler, varsayilan_videolar

def verileri_kaydet_dosyaya(dersler, videolar):
    data = {"dersler": dersler, "videolar": videolar}
    try:
        with open(VERitabani_DOSYASI, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

# --- SESSION STATE BAŞLATMA ---
if "dersler" not in st.session_state or "videolar" not in st.session_state:
    d, v = veri_yukle()
    st.session_state.dersler = d
    st.session_state.videolar = v

for key, val in [("aktif_soru_index", 0), ("cevap_kontrol_edildi", False)]:
    if key not in st.session_state:
        st.session_state[key] = val

# --- GEMINI AI İSTEMCİSİ ---
@st.cache_resource
def get_ai_client():
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
        if api_key:
            return genai.Client(api_key=api_key)
        return genai.Client()
    except Exception:
        return None

ai_client = get_ai_client()

# --- SOL PANEL (SIDEBAR) MENÜLERİ ---
st.sidebar.markdown("## 🧭 LGS Eğitim Paneli")
st.sidebar.markdown("---")

# Ana Menüler
ana_menu = st.sidebar.radio(
    "📌 Ana Menüler", 
    ["📚 Soru Bankası", "📝 Testler", "🏆 Deneme Sınavları", "🎬 Video Dersler"]
)

st.sidebar.markdown("---")

# Seçilen menüye göre sol panelde ders ve ünite filtrelerini göster
if ana_menu in ["📚 Soru Bankası", "📝 Testler", "🏆 Deneme Sınavları"]:
    st.sidebar.markdown("### ⚙️ Filtreler")
    secilen_ders = st.sidebar.selectbox("📚 Seçmeli Ders", list(DERS_UNITELERI.keys()))
    mevcut_uniteler = DERS_UNITELERI.get(secilen_ders, [])
    secilen_unite = st.sidebar.selectbox("📖 Ünite / Konu", mevcut_uniteler)
    secilen_zorluk = st.sidebar.selectbox("🎯 Zorluk Derecesi", ["Kolay", "Orta", "Zor", "Karma"])
else:
    secilen_ders = "Matematik"
    secilen_unite = "Çarpanlar ve Katlar"
    secilen_zorluk = "Orta"

st.sidebar.markdown("---")
st.sidebar.subheader("🔢 Soru Seçimi ve Üretimi")
secilen_soru_adedi = st.sidebar.number_input(
    "Kaç adet soru üretilsin/seçilsin?", 
    min_value=1, 
    max_value=100, 
    value=5, 
    step=1
)

# İstediğiniz gibi "Soru Üret" butonu soru seçimi alanının hemen altına eklendi
soru_uret_tiklandi = st.sidebar.button("✨ Yapay Zeka ile Soru Üret")

# --- ANA EKRAN İÇERİKLERİ (ANA MENÜYE GÖRE DEĞİŞİR) ---

if soru_uret_tiklandi:
    if not ai_client:
        st.error("Gemini AI istemcisi başlatılamadı. Lütfen API anahtarınızı kontrol edin.")
    else:
        with st.spinner(f"Yapay zeka {secilen_ders} - {secilen_unite} için {secilen_soru_adedi} adet soru hazırlıyor, lütfen bekleyin..."):
            basarili_sayisi = 0
            for i in range(secilen_soru_adedi):
                try:
                    prompt = f"""
                    8. sınıf LGS sınavına hazırlık için {secilen_ders} dersi, {secilen_unite} ünitesi konusunda;
                    Zorluk derecesi: {secilen_zorluk},
                    Özgün, kaliteli ve yeni nesil tarzda 1 adet çoktan seçmeli soru üret.
                    Yanıtı kesinlikle şu JSON formatında ver, başka hiçbir açıklama metni ekleme:
                    {{
                        "soru": "Soru metni buraya",
                        "secenekler": ["A) ...", "B) ...", "C) ...", "D) ..."],
                        "cevap": "A"
                    }}
                    """
                    res = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                    txt = res.text.strip()
                    if txt.startswith("```"):
                        txt = txt.split("```")[1]
                        if txt.startswith("json"):
                            txt = txt[4:].strip()
                    jdata = json.loads(txt)
                    
                    yeni_soru = {
                        "unite": secilen_unite,
                        "zorluk": secilen_zorluk,
                        "tip": ana_menu.replace("📚 ", "").replace("📝 ", "").replace("🏆 ", ""),
                        "soru": jdata.get("soru"),
                        "secenekler": jdata.get("secenekler"),
                        "cevap": jdata.get("cevap")
                    }
                    
                    if secilen_ders not in st.session_state.dersler:
                        st.session_state.dersler[secilen_ders] = []
                    st.session_state.dersler[secilen_ders].append(yeni_soru)
                    basarili_sayisi += 1
                except Exception:
                    pass
            
            if basarili_sayisi > 0:
                verileri_kaydet_dosyaya(st.session_state.dersler, st.session_state.videolar)
                st.success(f"Başarıyla {basarili_sayisi} adet yeni soru üretildi ve sisteme kaydedildi! 🎉")
                st.rerun()
            else:
                st.error("Soru üretilirken bir hata oluştu. Lütfen tekrar deneyin.")

if ana_menu == "📚 Soru Bankası":
    st.header("📚 Soru Bankası")
    st.markdown(f"**{secilen_ders}** » *{secilen_unite}* ({secilen_zorluk}) | Hedef Adet: **{secilen_soru_adedi}**")
    st.markdown("---")
    
    ders_sorulari = st.session_state.dersler.get(secilen_ders, [])
    filtrelenmis_sorular = [
        s for s in ders_sorulari 
        if s.get("unite", "") == secilen_unite and 
           (secilen_zorluk == "Karma" or s.get("zorluk", "Orta") == secilen_zorluk)
    ]
    
    if not filtrelenmis_sorular:
        st.warning("Bu filtreye uygun soru bulunamadı. Sol panelden **'✨ Yapay Zeka ile Soru Üret'** butonuna basarak anında soru oluşturabilirsiniz!")
    else:
        if st.session_state.aktif_soru_index >= len(filtrelenmis_sorular):
            st.session_state.aktif_soru_index = 0
            
        index = st.session_state.aktif_soru_index
        soru_data = filtrelenmis_sorular[index]
        
        st.markdown(f"**Soru {index + 1} / {len(filtrelenmis_sorular)}**")
        st.markdown(f"<div class='question-card'><h4>{soru_data['soru']}</h4></div>", unsafe_allow_html=True)
        
        secenekler = soru_data["secenekler"]
        secilen_secenek = st.radio("Seçiminizi yapın:", secenekler, key=f"sb_{index}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cevabı Kontrol Et", key="sb_kontrol"):
                dogru_cevap = soru_data["cevap"]
                secilen_harf = secilen_secenek.split(")")[0].strip()
                if secilen_harf == dogru_cevap:
                    st.success("Tebrikler! Doğru Cevap 🎉")
                else:
                    st.error(f"Yanlış cevap. Doğru cevap: {dogru_cevap}")
        with col2:
            if st.button("Sonraki Soru ➡️", key="sb_sonraki"):
                st.session_state.aktif_soru_index = (st.session_state.aktif_soru_index + 1) % len(filtrelenmis_sorular)
                st.rerun()

elif ana_menu == "📝 Testler":
    st.header("📝 Ünite Testleri")
    st.markdown(f"Seçilen Ünite: **{secilen_unite}** | Hedef Soru Adedi: **{secilen_soru_adedi}**")
    st.info("Sol paneldeki **'✨ Yapay Zeka ile Soru Üret'** butonunu kullanarak belirttiğiniz sayıda test sorusunu anında oluşturabilirsiniz.")

elif ana_menu == "🏆 Deneme Sınavları":
    st.header("🏆 Genel LGS Deneme Sınavları")
    st.markdown(f"Sınav Kapsamı: **{secilen_soru_adedi} Soruluk Deneme Simülasyonu**")
    st.warning("Sol paneldeki **'✨ Yapay Zeka ile Soru Üret'** butonu ile deneme sınavı havuzunu zenginleştirebilirsiniz.")

elif ana_menu == "🎬 Video Dersler":
    st.header("🎬 Konu Anlatım ve Çözüm Videoları")
    if not st.session_state.videolar:
        st.info("Kayıtlı video bulunmuyor.")
    else:
        video_basliklari = [v["baslik"] for v in st.session_state.videolar]
        secilen_video_baslik = st.selectbox("İzlemek istediğiniz videoyu seçin:", video_basliklari)
        secilen_video = next((v for v in st.session_state.videolar if v["baslik"] == secilen_video_baslik), None)
        if secilen_video:
            try:
                st.video(secilen_video["url"])
            except Exception:
                st.markdown(f"[Videoyu Aç]({secilen_video['url']})")