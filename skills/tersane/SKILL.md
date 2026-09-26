---
name: tersane
description: Oyun için (Unreal Engine 5.x) fotogerçekçi, game-ready, modüler tarihî yelkenli gemi üretimi — Blender bpy (headless) ile sürümlü pass zinciri, gövde/güverte/kıç/arma/yelken/top/iç mekân/çarpışma/soket/LOD/bake/FBX. Kullanıcı yeni bir gemi (frigate, brig, kalyon, kadırga, çalupa…) istediğinde, mevcut bir gemiye pass eklerken, gemi modellerini denetlerken veya UE teslim paketi hazırlarken kullan. OTTOMAN_FRIGATE_1780_ISTANBUL projesinde öğrenilen kurallar, yöntemler ve hatalar.
---

# Tersane — Gemi Yapım Skill'i

Bu skill, `OTTOMAN_FRIGATE_1780_ISTANBUL` gemisi (v001–v029) yapılırken öğrenilenleri toplar. Amaç sonraki gemileri
aynı hataları yapmadan, aynı kalite ve düzende üretmek. **Canlı belgedir:** her gemide yeni bir ders çıktığında
"Değişiklik günlüğü" bölümüne yaz.

Kaynak örnek kod: `OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/` (pass betikleri) — yeni gemide kopyalayıp uyarlamak için
en iyi referans. Özellikle: `build_hull_v001.py` (gövde üreticisi), `pass_v013_*` (alt güverte, soketler, UCX),
`pass_v015_rigset.py` (arma), `pass_v020_cannon_realistic.py` (top), `pass_v022_sailset.py` (yelken + motif),
`pass_v026_lods.py` (LOD), `bake_tile_textures.py` (bake), `pass_v027_*` (merdiven kırpma, boolean doğrulama).

---

## 1. Kullanıcı kuralları (değişmez)

- **Tüm çıktılar Türkçe.** Rapor, commit mesajı, kod yorumu, özet.
- **Kaynaksız sayı yazılmaz.** Her ölçü `[BİRİNCİL]`, `[İKİNCİL: kaynak, "arama özeti"]` ya da `TAHMİN` olarak
  etiketlenir. Web erişimi kısıtlıysa bunu açıkça yaz.
- **Gate A insan onayı gerektirir**; otomatik onay yok. Ölçü/sınıf/yerleşim kararlarını kullanıcıya sor.
- **Low-poly yasağı — ölçülür, göz kararı değil** (v030 dersi: 109 mesh'ten 86'sı ihlaldeydi ve fark edilmemişti):
  - Yuvarlak kesit: **kiriş sapması ≤ 1,5 mm** → `seg ≥ π / acos(1 − 0,0015 / r)` (`resegment.required_segments`).
    Örnek: r 0,016 halat → 8, r 0,03 → 12, r 0,15 seren → 24, r 0,30 fıçı/direk → 32. Eğri yol/profil de aynı
    kurala göre sıklaştırılır (halka cıvatası, brok halatı, bodoslama, küpeşte istasyonları).
  - Kutu kenarı: bevel **≥ 3 segment** + harden normals (90° köşe 22,5° adımla).
  - Subdivision'da **viewport = render seviyesi** (FBX viewport'u dışa aktarır; v030'a kadar gövde oyunda fasetliydi).
  - Her pass sonunda `scripts/quality_audit.py` çalışır; hata varsa pass bitmemiştir. Yer tutucu (blockout) nesneye
    `quality_exempt` yazılır ve kullanıcıya söylenir. Bütçe: tekrar eden parça (fıçı, top) **tek mesh + örnek**.
- **Versiyonlu kayıt:** her pass önceki `.blend`'i açar, yalnız hedef nesneleri değiştirir, `vNNN.blend` olarak kaydeder;
  var olan sürümün **üzerine yazmaz** (betik `SystemExit` verir). Gerekmedikçe tüm gemi yeniden kurulmaz.
- **Her pass sonunda:** render + kısa audit (`reports/scene_audit_vNNN.json`) + belgelere not + commit/push.
- **Oynanış:** AC (Assassin's Creed) tarzı — her yer gezilebilir ve tırmanılabilir (güverteler, iç mekânlar, çarmıhlar,
  çanaklıklar, serenler, cıvadıra). Toplar mürettebatla çalışır; komuta zinciri oyuncu → 2. kaptan → topçu subayı.
- **Modülerlik:** Hull Core + değiştirilebilir modüller (RigSet, SailSet, CannonBattery, Figurehead, BoatSet, AnchorSet,
  LanternFlagSet, DeckUtility, InteriorSet…). Yapısal gövde değişimi yeni hull sınıfıdır.
- **Sınıf sadakati:** kullanıcı bir sınıf seçtiyse (ör. frigate) başka sınıfın özelliği eklenmez (frigate'e hat gemisi
  alt bataryası vb.). Yükseltmeler sınıf içinde kalır; kullanıcıya sınırı sor.
- **Lisanslı referans varlıklar (Fab vb.) repoya konmaz**; yalnız denetim çıktıları.
- Git: kendi dalında çalış, main'e merge etme, force push yapma.

## 2. Ortam (bulut, headless)

- `pip install bpy==5.0.1` (python3.11). **numpy < 2.0 şart** (`pip install "numpy>=1.26,<2.0"`); opencv kurma
  (numpy'yi yükseltip bpy'yi bozar).
- **EGL/GPU yok → Workbench/EEVEE render çalışmaz.** Yalnız Cycles CPU. Önizleme için `samples=10–16`, 1200×700;
  teslim renderları 48 örnek 1600×900.
- İç mekân renderları çok yavaştır (nokta ışıklar, kapalı hacim): arka planda zincir betikle çalıştır.
- `pkill -f <desen>` kendi kabuğunu da öldürür (desen komut satırında geçer) → kullanma; `pgrep` ile bekle.
- Ön planda `sleep` yasak → uzun işleri `run_in_background` ile başlat, bildirimi bekle.
- Konteyner yeniden başlayabilir → **her pass'ten hemen sonra commit/push**; arka plan işlerini yeniden kur.
- YouTube / Wikipedia / pek çok site egress'te kapalı olabilir → kullanıcıdan ekran görüntüsü ya da başlık iste.

## 3. İş akışı

1. **Araştırma + Gate A:** sınıf, dönem, çapa gemi (ör. HMS Lyme 1748), ölçüler, top düzeni. Kaynak etiketli
   `ship_spec.yaml` + `reports/MODELLEME_PLANI.md`. Kullanıcı onayı.
2. **v001 gövde üreticisi** (tasarım uzayında), sonra pass zinciri. Her pass: tek konu.
3. Kararları **toplu sor** (AskUserQuestion, en fazla 4 soru; önerilen seçenek ilk sırada). Kullanıcı uyuyacaksa
   bütün açık kararları tek seferde sor, sonra sırayla çalış.
4. Belgeler: `KALDIGIM_YER.md` (son sürüm başta), `MODELLEME_PLANI.md` (§5x her pass), `ship_spec.yaml`.
5. Kullanıcı sırası verdiyse ("aksini söylemedikçe bu sırayla") ona uy, her adımda commit.

## Ayrıntı dosyaları (gerektiğinde oku)

| Dosya | İçerik | Ne zaman |
|---|---|---|
| `references/govde_ve_erisim.md` | §4 koordinat/su hattı, §5 gövde, §6 boolean, §7 merdiven/ambar, §8 soket, §9 UCX | Gövde, güverte, erişim, oynanış verisi |
| `references/arma_ve_yelken.md` | §10 arma, §11 yelken/bayrak/motif + Blender içi varyant anahtarı | Direk, seren, halat, yelken |
| `references/moduller.md` | §12 top, §13 figür, §14 iç mekân | Top, heykel, kamara/ambar |
| `references/teslim_lod_bake_fbx.md` | §15 LOD, tile bake, FBX | UE teslim paketi |

## Yardımcı betikler (`scripts/`, bpy 4.x/5.x)

| Betik | İş |
|---|---|
| `geom.py` | box8/aabox/obox, lathe, tube, spar, finish (normal + UV + bevel), convex_ucx (≤64 köşe), rename_two_phase |
| `stairs.py` | çakışmasız merdiven (kırpılmış kiriş), mevcut merdivenden parametre çıkarma |
| `ship_checks.py` | BVH çakışma, delik ışın testi, UCX denetimi, soketleri güverteye oturtma, boolean listesi (CLI) |
| `lods.py` | LOD zinciri (%50/%20, gövde +%8) `50_LODS` koleksiyonunda |
| `lod_store.py` | LOD'ları ayrı `<blend>_LOD.blend` dosyasına yazar / geri yükler (GitHub 100 MB dosya sınırı) |
| `quality_audit.py` | **Kalite testi**: faset (kiriş sapması + süreklilik), düz gölge, havada ada, istisna listesi (CLI) |
| `resegment.py` | Mesh düzeyinde yeniden dilimleme: lathe/tube halkaları, elipsoitler, profil/yol ve süpürme sıklaştırma |
| `sdf_sculpt.py` | SDF yontu: elipsoit/konik kapsül/zincir, yumuşak birleşim/oyma, bölge malzemesi, yüzeye yansıtma, tüy tohumları, marching cubes → tek parça mesh (figür, arma) |
| `bake_tile_textures.py` | Prosedürel malzemeleri tile BC/N/ORM'e bake (DirectX normal) + manifest (CLI) |

Kullanım: `import sys; sys.path.append("<skill>/scripts"); import geom, stairs, ship_checks, lods`

## 16. Denetim listesi (her pass)

- [ ] `scene_audit_vNNN.json`: üçgen, sınırlar, su çekimi, eksik UV/malzeme, birim dışı ölçek, soket sayısı
- [ ] BVH çakışma: merdiven/eşya × güverte/koaming/kiriş
- [ ] Ambar ağzı/lumbar delikleri ışınla açık mı (boolean doğrulama)
- [ ] Mürettebat/istasyon/navlink çakışması, kafa payı
- [ ] UCX ≤ 64 köşe, ad kuralı, sahibi mevcut
- [ ] **Kalite testi** (`quality_audit.py`): faset (kiriş sapması > 1,5 mm), düz gölge, havada ada = 0 hata
- [ ] Render: bir dış (omuz), bir yakın (değişen parça), iç mekânsa ışıklı iç görüntü; kullanıcı yakın bakar
- [ ] Belgeler (KALDIGIM_YER, MODELLEME_PLANI §, spec) + commit + push

## 17. Bilinen tuzaklar (kısa)

| Belirti | Neden | Çözüm |
|---|---|---|
| Delik/ambar kapalı | EXACT boolean sessiz hata | FLOAT + ışın testi |
| Merdiven güverteye giriyor | kiriş eğim kalınlığı | kiriş kırpma + BVH testi |
| Kamarada zemin boşluğu | güverte s0 = 0,02 | s0 ≈ 0,006 |
| Top/mürettebat havada/gömülü | orta hat yüksekliği | ışınla yüzeye oturt |
| Kapak kırmızı (ters yüz) | box8 normalleri | `recalc_face_normals` sonra malzeme ata |
| Monkeypatch sonsuz döngü | yamalı fonksiyon kendini çağırır | orijinali önceden değişkende sakla |
| Seren çapı yanlış | basamak halatı köşeleri | filtre `|z| < 0,35` |
| Çanaklık tırtıklı | kare ızgara hücreleri | ışınsal halka ızgara |
| Ambar yükü 225 k üçgen | aşırı detaylı fıçı | 10 dilim, 2 çember |
| Figür oyuncak gibi | skin modifier | blockout + sculpt/AI/varlık |
| Filika direğin içinde | eski soket | soket mesafe testi |
| Bayrak direği bumbaya çarpar | yerleşim | sancak gaf ucunda |
| Kullanıcı varyantı açamıyor | durum yalnızca betikte (`set_state`) | kontrol boşu + sürücü + N paneli |
| Yakından low-poly (halat yassı, seren köşeli) | sabit küçük `seg` | `resegment.py` + kiriş sapması kuralı |
| Oyunda gövde fasetli, renderda düzgün | Subsurf viewport 1 / render 2 | iki seviye eşit |
| Elle keskin kenarlar kayboldu | `set_sharp_from_angle` sıfırlar | `resegment.sharp_from_angle_keep` |
| Merdiven 6 cm havada | çakışmayı önlemek için kiriş ayağı kırpıldı | ayak güverteye (4 mm gömülü) |
| Kanca/bigot/başlık havada | konum hesabı yüzeyi ıskaladı | `quality_audit` havada ada + hedefe taşı |
| Halat havada V çiziyor | makarasız kırılma noktası | kırılmaya yönlendirme makarası |
| Eski üreticiyi çağırınca parça 3–13 m kaydı | pass zinciri yamaları | mesh düzeyinde düzelt (resegment) ya da konum karşılaştır |
| Figür oyuncak/damla gibi (metaball) | ayrıntı yok, oranlar tahmini | SDF yontu + anatomik oran + yüzeye yatan tüy tutamı (`sdf_sculpt.py`) |
| Parmaklık gemiden ayrı ama test temiz | bir ucu figüre değiyor, diğeri havada | iki ucun da hedefe değdiğini ayrı ölç (bağlantı uçları) |
| Push reddi: blend > 100 MB | türetilmiş LOD'lar ana dosyada (≈ %55) | `lod_store.save_split` → `_LOD.blend` ayrı |
| Gizli nesne yanlış yerde ölçülür | sürücüyle gizli nesnede `matrix_world` değerlendirilmez | ebeveynsizse `matrix_basis` |
| Renderda tavan gizlenmiyor | görünürlük sürücüsü `hide_render`'ı ezer | render adımında önce sürücüyü sil (kaydetme) |
| Parça atılıyor, sebep belirsiz | çakışma BVH'si tek parça | nesne nesne yeniden test et, `clash_with` raporla |
| Sürücü testi başsızda hep eski değer | sonuç orijinale yazılmaz, evaluate önbellekli | sürücü yapısını/ifadesini doğrula |

## Değişiklik günlüğü

- **2026-09-26 (v001–v027, OTTOMAN_FRIGATE_1780_ISTANBUL):** ilk sürüm. Gövde, Hull_B, kıç, merdivenler, UCX, soketler,
  top A→B, arma, yelken + motif, bayrak, kamara, ambar, LOD, tile bake, top varyant FBX paketi, frigate sınıf kuralı,
  boolean doğrulama dersi.
- **v031–v034:** Osmanlı süslemeleri (dekal-kabartma yamalar, 3B arma/rozet/alem), kuşak tahtası–lumbar çakışması,
  faset temizliği, bozkurt figürü tek parça (metaball + gömme + EXACT birleşim).
- **v035–v036:** bozkurt figürü SDF yontusu (`sdf_sculpt.py`; tek alan → tek parça), yele yumuşak kaynak + patinalı
  bronz (altın kenar = solucan etkisi), malzeme çoğunluk süzgeci; baş parmaklıkları bordaya gömülü.
- **v038–v044 (Kızıl Sancak uyarlaması):** açık yelken B (Coons yaması, karın/kıvrım/camadan); Meshy figür içe
  aktarımı (ada birleştirme, decimate, doku PNG dönüşümü); arma dokuları PIL raster, top mührü Delaunay kabartma;
  iç düzen kiti `interior_kit.py` (bölme, hamak, perde, oda kimliği boşu); üçgen düzeyi çakışma + kaydırma/içe alma
  denemeleri; paylaşılan mesh örnekleri (UE ISM); v044'ten itibaren LOD'lar ayrı dosyada (`lod_store.py`).
- **v037:** eğik çanaklık topolojiyle bulunur (eksene dik varsayma); halat dönüşü `fillet_kinks`; seçici kıvrımlı
  Catmull-Clark + ölç/geri al (`pass_v037_facet_cleanup2.cc_subdivide`). Kalite testi 23 → 3 nesne.
- **v030 (kalite testi):** low-poly yasağı ölçülebilir hale geldi (kiriş sapması, bevel ≥ 3, subsurf seviye eşitliği);
  `quality_audit.py`, `resegment.py`; faset 15.249 m → ~350 m, havada parça 35 → 0; fıçı örnekleme.
- **v028–v029:** Osmanlı tunç topu C (yunus kulp, stilize tuğra/kitabe, AO patina, yıpranmış boyalı kızak, palanga, alet
  rafı); yelken aç/kapa anahtarı (kontrol boşu + sürücü + N paneli).
