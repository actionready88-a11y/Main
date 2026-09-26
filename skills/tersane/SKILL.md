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
- **Low-poly yasağı:** kutu gibi parçalara pah (bevel), lathe'lerde yeterli dilim (namlu 40–48, direk 16–20).
  Ama bütçe gözetilir (bkz. §9, `references/govde_ve_erisim.md`).
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
| `bake_tile_textures.py` | Prosedürel malzemeleri tile BC/N/ORM'e bake (DirectX normal) + manifest (CLI) |

Kullanım: `import sys; sys.path.append("<skill>/scripts"); import geom, stairs, ship_checks, lods`

## 16. Denetim listesi (her pass)

- [ ] `scene_audit_vNNN.json`: üçgen, sınırlar, su çekimi, eksik UV/malzeme, birim dışı ölçek, soket sayısı
- [ ] BVH çakışma: merdiven/eşya × güverte/koaming/kiriş
- [ ] Ambar ağzı/lumbar delikleri ışınla açık mı (boolean doğrulama)
- [ ] Mürettebat/istasyon/navlink çakışması, kafa payı
- [ ] UCX ≤ 64 köşe, ad kuralı, sahibi mevcut
- [ ] Render: bir dış (omuz), bir yakın (değişen parça), iç mekânsa ışıklı iç görüntü
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
| Sürücü testi başsızda hep eski değer | sonuç orijinale yazılmaz, evaluate önbellekli | sürücü yapısını/ifadesini doğrula |

## Değişiklik günlüğü

- **2026-09-26 (v001–v027, OTTOMAN_FRIGATE_1780_ISTANBUL):** ilk sürüm. Gövde, Hull_B, kıç, merdivenler, UCX, soketler,
  top A→B, arma, yelken + motif, bayrak, kamara, ambar, LOD, tile bake, top varyant FBX paketi, frigate sınıf kuralı,
  boolean doğrulama dersi.
- **v028–v029:** Osmanlı tunç topu C (yunus kulp, stilize tuğra/kitabe, AO patina, yıpranmış boyalı kızak, palanga, alet
  rafı); yelken aç/kapa anahtarı (kontrol boşu + sürücü + N paneli).
