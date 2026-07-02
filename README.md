# 🎬 Faceless Shorts Generator

Script dosyası ver → yayına hazır 9:16 video al. Yüz yok, kendi ses yok, ücretli araç yok.

**Zincir:** Script (.txt) → edge-tts seslendirme (ücretsiz Microsoft neural sesler) → Pexels stok video (ücretsiz API) → ffmpeg montaj → kelime vurgulu altyazılı MP4

---

## Kurulum (bir kere, ~10 dakika)

**1. Gereksinimler**
- Python 3.10+
- ffmpeg → `winget install ffmpeg` (Windows) / `brew install ffmpeg` (Mac) / `sudo apt install ffmpeg` (Linux)

**2. Paketler**
```bash
pip install -r requirements.txt
```

**3. Pexels API anahtarı (ücretsiz)**
- https://www.pexels.com/api/ → kayıt ol → anahtarını kopyala
- Ortam değişkeni olarak ayarla:
```bash
# Mac/Linux (kalıcı olması için ~/.zshrc veya ~/.bashrc'ye ekle):
export PEXELS_API_KEY="anahtarin_buraya"

# Windows PowerShell:
setx PEXELS_API_KEY "anahtarin_buraya"
```

**4. (Opsiyonel) Arka plan müziği**
- Telifsiz bir mp3'ü `assets/music.mp3` olarak koy (YouTube Audio Library'den indir)
- Varsa otomatik olarak %12 seste altta çalar, yoksa müziksiz üretir

---

## Kullanım

**1. Script yaz** → `scripts/` klasörüne .txt olarak kaydet. Format:

```
[scene: jellyfish underwater glowing]
This tiny jellyfish has figured out how to never die.

[scene: ocean deep blue]
It reverses its own aging...
```

- `[scene: ...]` içindeki kelimeler Pexels arama terimi (İngilizce, somut ve görsel: "jellyfish underwater" iyi, "immortality concept" kötü)
- Altındaki satırlar o sahnede seslendirilecek metin
- 5-6 sahne ≈ 40-50 saniyelik video

**2. Çalıştır:**
```bash
python generate.py scripts/video1_immortal_jellyfish.txt
```

**3. Sonuç:** `output/video1_immortal_jellyfish.mp4` — 1080x1920, altyazılı, yayına hazır.

### Ses seçenekleri
```bash
python generate.py scripts/video1.txt --voice en-US-GuyNeural
```
İyi sesler: `en-US-ChristopherNeural` (varsayılan, derin/belgesel), `en-US-GuyNeural` (enerjik), `en-GB-RyanNeural` (İngiliz aksanı). Tüm liste: `edge-tts --list-voices`

---

## Yeni senaryo üretme (Claude prompt şablonu)

Claude'a şunu yapıştır:

```
Write a 40-second short-form video script about [KONU] in this exact format:

[scene: 2-4 word English stock footage search term]
Narration text for this scene.

Rules: 5-6 scenes. First scene = shocking hook under 12 words.
Scene search terms must be concrete and visual (things a camera can film).
Simple English, no jargon. Last scene = one-line follow CTA.
Every fact must be verifiable.
```

Çıktıyı direkt `scripts/yeni_video.txt` olarak kaydet, çalıştır. **Ama yayınlamadan önce:**
1. Fact-check yap (NotebookLM'e kaynakla sor)
2. En az bir cümleyi kendi cümlenle değiştir/güçlendir — tamamen otomatik içerik platform politikalarına takılır, senin dokunuşun şart

---

## Sorun giderme

| Sorun | Çözüm |
|---|---|
| `Pexels'te sonuç yok` | Sahne terimini daha genel yap ("bioluminescent polyp" → "jellyfish glowing") |
| Ses robotik geldi | Farklı voice dene, veya `generate.py` içinde `rate="+8%"` değerini oynat |
| Altyazı çok büyük/küçük | `generate.py` başındaki `SUB_SIZE = 88` değerini değiştir |
| Klip konuyla alakasız | Pexels aramasında ilk 10 sonuçtan seçiyor; terimi netleştir |
| ffmpeg bulunamadı | Kurulumu PATH'e ekle, terminali yeniden başlat |

---

## Sonraki geliştirmeler (istersen)

- [ ] Ken Burns efekti (yavaş zoom) — statik görünen kliplere hareket katar
- [ ] Anthropic API entegrasyonu ile script üretimini de pipeline'a alma
- [ ] Metricool API ile otomatik zamanlama
- [ ] Sahne geçişlerinde crossfade

Bu proje GitHub profiline de eklenebilir: "AI-powered short-form video automation pipeline" — staj başvurularında somut, çalışan bir proje.
