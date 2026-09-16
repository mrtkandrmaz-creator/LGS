import json
import os
import streamlit as st
from google import genai

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(
    page_title="LGS Hazırlık Asistanı - Web Sürümü",
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
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #3a0ca3;
        color: white;
    }
    .question-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DOSYA VE VERİ YÖNETİMİ ---
VERitabani_DOSYASI = "lgs_veritabani.json"

def veri_yukle():
    if os.path.exists(VERitabani_DOSYASI):
        try:
            with open(VERitabani_DOSYASI, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("dersler", {}), data.get("videolar", [])
        except Exception:
            pass
    
    # Varsayılan Veriler
    varsayilan_dersler = {
        "Matematik": [{"soru": "Örnek Soru: 2 + 2 * 2 işleminin sonucu kaçtır?", "secenekler": ["A) 4", "B) 6", "C) 8", "D) 2"], "cevap": "B"}],
        "Fen Bilimleri": [{"soru": "Örnek Fen Sorusu: Hücrenin enerji santrieli hangisidir?", "secenekler": ["A) Mitokondri", "B) Ribozom", "C) Kloroplast", "D) Koful"], "cevap": "A"}],
        "Türkçe": [{"soru": "Örnek Türkçe Sorusu: Aşağıdakilerden hangisi bir fiil (eylem) cümlesidir?", "secenekler": ["A) Hava bugün çok güzeldi.", "B) Kitap masanın üzerindeydi.", "C) Eve doğru koşmaya başladı.", "D) En sevdiğim renk mavidir."], "cevap": "C"}],
        "İnkılap Tarihi": [{"soru": "Örnek İnkılap Sorusu: TBMM hangi tarihte açılmıştır?", "secenekler": ["A) 19 Mayis 1919", "B) 23 Nisan 1920", "C) 29 Ekim 1923", "D) 30 Ağustos 1922"], "cevap": "B"}]
    }
    varsayilan_videolar = [
        {"baslik": "Matematik - Çarpanlar ve Katlar Konu Anlatımı", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    ]
    return varsayilan_dersler, varsayilan_videolar

def verileri_kaydet_dosyaya(dersler, videolar):
    data = {
        "dersler": dersler,
        "videolar": videolar
    }
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

if "toplam_cozulen" not in st.session_state:
    st.session_state.toplam_cozulen = 0
if "dogru_sayisi" not in st.session_state:
    st.session_state.dogru_sayisi = 0
if "yanlis_sayisi" not in st.session_state:
    st.session_state.yanlis_sayisi = 0
if "aktif_soru_index" not in st.session_state:
    st.session_state.aktif_soru_index = 0
if "cevap_kontrol_edildi" not in st.session_state:
    st.session_state.cevap_kontrol_edildi = False

# --- GEMINI AI İSTEMCİSİ ---
@st.cache_resource
def get_ai_client():
    try:
        # Streamlit secrets veya çevre değişkeninden API anahtarını alır
        api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
        if api_key:
            return genai.Client(api_key=api_key)
        return genai.Client()
    except Exception:
        return None

ai_client = get_ai_client()

# --- KENAR ÇUCUĞU (SIDEBAR) - DERSLER VE İSTATİSTİKLER ---
st.sidebar.title("📌 Navigasyon & İstatistik")
aktif_ders = st.sidebar.radio("Ders Seçin:", list(st.session_state.dersler.keys()))

# Ders değiştiğinde soru indeksini sıfırla
if "onceki_ders" not in st.session_state or st.session_state.onceki_ders != aktif_ders:
    st.session_state.onceki_ders = aktif_ders
    st.session_state.aktif_soru_index = 0
    st.session_state.cevap_kontrol_edildi = False

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Çalışma İstatistikleri")
st.sidebar.metric("Toplam Çözülen", st.session_state.toplam_cozulen)
st.sidebar.metric("Doğru Sayısı", st.session_state.dogru_sayisi)
st.sidebar.metric("Yanlış Sayısı", st.session_state.yanlis_sayisi)

basari = (st.session_state.dogru_sayisi / st.session_state.toplam_cozulen * 100) if st.session_state.toplam_cozulen > 0 else 0
st.sidebar.metric("Başarı Oranı", f"%{basari:.1f}")

# --- ANA SEKMELER ---
tab_soru, tab_video, tab_ai = st.tabs([
    "📚 Soru Bankası & İstatistikler", 
    "🎬 Video Dersler", 
    "🤖 YZ İçerik Üretim Paneli"
])

# --- SEKME 1: SORU BANKASI ---
with tab_soru:
    st.header(f"📚 {aktif_ders} - Soru Bankası")
    
    ders_sorulari = st.session_state.dersler.get(aktif_ders, [])
    
    if not ders_sorulari:
        st.warning("Bu derse ait soru bulunamadı. 'YZ İçerik Üretim Paneli'nden yeni sorular üretebilirsiniz.")
    else:
        if st.session_state.aktif_soru_index >= len(ders_sorulari):
            st.session_state.aktif_soru_index = 0
            
        index = st.session_state.aktif_soru_index
        soru_data = ders_sorulari[index]
        
        st.markdown(f"**Soru {index + 1} / {len(ders_sorulari)}**")
        st.markdown(f"<div class='question-card'><h4>{soru_data['soru']}</h4></div>", unsafe_allow_html=True)
        
        secenekler = soru_data["secenekler"]
        secilen_secenek = st.radio("Seçiminizi yapın:", secenekler, key=f"soru_radio_{index}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Cevabı Kontrol Et", key="btn_kontrol"):
                harfler = ["A", "B", "C", "D"]
                dogru_cevap = soru_data["cevap"]
                
                # Seçilen şıkkın harfini bul (Örn: "A) Şık metni" -> "A")
                secilen_harf = secilen_secenek.split(")")[0].strip()
                
                st.session_state.toplam_cozulen += 1
                if secilen_harf == dogru_cevap:
                    st.session_state.dogru_sayisi += 1
                    st.success("Tebrikler! Doğru Cevap 🎉")
                else:
                    st.error(f"Yanlış cevap. Doğru cevap: {dogru_cevap}")
                st.session_state.cevap_kontrol_edildi = True
                st.rerun()
                
        with col2:
            if st.button("Sonraki Soru ➡️", key="btn_sonraki"):
                st.session_state.aktif_soru_index = (st.session_state.aktif_soru_index + 1) % len(ders_sorulari)
                st.session_state.cevap_kontrol_edildi = False
                st.rerun()

# --- SEKME 2: VİDEO DERSLER ---
with tab_video:
    st.header("🎬 Video Dersler ve Konu Anlatımları")
    
    if not st.session_state.videolar:
        st.info("Henüz kayıtlı video ders bulunmuyor.")
    else:
        video_basliklari = [v["baslik"] for v in st.session_state.videolar]
        secilen_video_baslik = st.selectbox("İzlemek istediğiniz dersi seçin:", video_basliklari)
        
        secilen_video = next((v for v in st.session_state.videolar if v["baslik"] == secilen_video_baslik), None)
        
        if secilen_video:
            url = secilen_video["url"]
            # Streamlit st.video doğrudan YouTube linklerini destekler
            try:
                st.video(url)
            except Exception:
                st.warning("Video oynatılamadı, alternatif bağlantı kullanılıyor.")
                st.markdown(f"[Videoyu Tarayıcıda Aç]({url})")

# --- SEKME 3: YZ İÇERİK ÜRETİM PANELİ ---
with tab_ai:
    st.header("🤖 Yapay Zeka ile Soru ve Video Ders Üretici")
    st.markdown("Yapay zekanın sizin için LGS düzeyinde özgün sorular ve video kaynakları hazırlamasını sağlayın.")
    
    ai_ders = st.selectbox("Ders Seçin:", list(st.session_state.dersler.keys()), key="ai_ders_secim")
    ai_konu = st.text_input("Konu / İpucu Yazın:", placeholder="Örn: Basınç ve Katı Basıncı yeni nesil soru")
    
    if st.button("✨ Yapay Zeka ile İçerik Üret"):
        if not ai_client:
            st.error("Gemini AI istemcisi başlatılamadı. Lütfen API anahtarınızı (GEMINI_API_KEY) kontrol edin.")
        else:
            konu_metni = ai_konu if ai_konu.strip() else "Genel LGS tekrar konusu"
            prompt = f"""
            Lütfen 8. sınıf LGS öğrencileri için {ai_ders} dersinden, '{konu_metni}' konusunda:
            1. Özgün, kaliteli ve yeni nesil 1 adet çoktan seçmeli soru.
            2. Bu konuyla ilgili YouTube'da izlenebilecek eğitsel bir ders için uygun video başlığı.
            3. YouTube video URL'si (Örnek format: https://www.youtube.com/watch?v=dQw4w9WgXcQ - geçerli standart bir youtube linki kullan).
            
            Yanıtı kesinlikle şu JSON formatında ver, başka hiçbir metin veya açıklama ekleme:
            {{
                "soru": "Soru metni buraya",
                "secenekler": ["A) şık1", "B) şık2", "C) şık3", "D) şık4"],
                "cevap": "A",
                "video_baslik": "{ai_ders} - Konu Anlatımı ve Soru Çözümü: {konu_metni}",
                "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }}
            """
            
            with st.spinner("Yapay zeka yeni nesil içerik hazırlıyor... Lütfen bekleyin."):
                try:
                    response = ai_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    
                    cevap_metni = response.text.strip()
                    if cevap_metni.startswith("```"):
                        cevap_metni = cevap_metni.split("```")[1]
                        if cevap_metni.startswith("json"):
                            cevap_metni = cevap_metni[4:].strip()
                    
                    veri_dict = json.loads(cevap_metni)
                    
                    yeni_soru = {
                        "soru": veri_dict.get("soru"),
                        "secenekler": veri_dict.get("secenekler"),
                        "cevap": veri_dict.get("cevap")
                    }
                    if ai_ders not in st.session_state.dersler:
                        st.session_state.dersler[ai_ders] = []
                    st.session_state.dersler.append(yeni_soru) if isinstance(st.session_state.dersler, list) else st.session_state.dersler[ai_ders].append(yeni_soru)
                    
                    yeni_video = {
                        "baslik": veri_dict.get("video_baslik", f"{ai_ders} - {konu_metni}"),
                        "url": veri_dict.get("video_url", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
                    }
                    st.session_state.videolar.append(yeni_video)
                    
                    # Dosyaya kalıcı olarak kaydet
                    verileri_kaydet_dosyaya(st.session_state.dersler, st.session_state.videolar)
                    
                    st.success(f"'{ai_ders}' için yapay zeka yeni soru bankası sorusu ve video ders başarıyla ekledi! 🎉")
                except Exception as e:
                    st.error(f"İçerik üretilirken bir hata oluştu:\n{str(e)}")