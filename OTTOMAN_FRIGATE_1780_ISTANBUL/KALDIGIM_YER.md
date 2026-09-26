# Kaldığım Yer — v046 (2026-09-26) — CLAUDE DESKTOP'A DEVİR

- Repo: `actionready88-a11y/Main`, dal `claude/amazing-meitner-keq46t` (main'e birleştirilmedi), klasör `OTTOMAN_FRIGATE_1780_ISTANBUL/`.
- Bu dosya bulut oturumunda (Claude Code, claude.ai/code) yapılan her şeyin özetidir. Yeni oturum buradan başlar.
- Önce `CLAUDE.md`'yi, sonra bu dosyanın ► bölümlerini, gerekirse aşağıdaki sürüm bölümlerini oku.

## ► 0. YEREL KURULUM (Claude Desktop / kendi bilgisayarın)
1. **Depoyu güncelle** (GitHub Desktop: Fetch → Pull; ya da komut satırı):
   ```
   git fetch origin
   git checkout claude/amazing-meitner-keq46t
   git pull origin claude/amazing-meitner-keq46t
   git lfs install
   git lfs pull          # .glb dosyaları Git LFS'te (figür modelleri); bu olmadan 133 baytlık işaretçi kalır
   ```
2. **Commit sayısı:**
   - Bu dal 73 commit (v001 → v046); `main`'in 71 commit önünde. Tam liste: `reports/COMMIT_GECMISI.md`.
   - GitHub Desktop'ta görülen "592" büyük ihtimalle yerel **Changes** sayısıdır: senin bilgisayarında değişmiş ya da izlenmeyen
     dosyalar. Bunlar buluttan görünmez. Yeni oturum önce `git status` ile bunlara baksın.
   - Yerelde kaydedilmesi gereken iş varsa commit'lenir. Blender'ın kendiliğinden oluşturduğu dosyalar (`*.blend1`, `__pycache__`)
     ve yeniden adlandırma artıkları commit'lenmez. **Pull etmeden önce yerel değişiklikleri commit'le ya da stash'le**
     (çakışmada blend dosyaları birleştirilemez).
3. **Açılacak dosya:** `Blender/versions/OTTOMAN_FRIGATE_1780_ISTANBUL_v046.blend` (Blender 4.x/5.x).
   - LOD'lar ayrı dosyada: `..._v046_LOD.blend`. Gerekince File → Append → `..._v046_LOD.blend` → Collection → `50_LODS`.
   - **Pembe malzeme:** v044 ve öncesinde doku yolları bulut yoluyla (`/home/user/Main/...`) kayıtlıydı. Bu yüzden
     bilgisayarında pembe görünürler. Çözüm: File → External Data → Find Missing Files → proje içindeki `Textures` klasörü.
     v045 ve sonrasında yollar göreli (`//../../Textures/...`), sorun yok.
4. **Betikler:** `scripts/pass_vNNN_*.py`.
   - Bulutta `python3.11` + `bpy 5.0.1` ile çalıştı. Yerelde: `blender -b --python scripts/pass_vNNN_x.py -- --no-render`.
   - Her pass önceki sürümü açar ve yeni sürüm kaydeder. Kayıtlı bir sürümün üzerine **asla** yazılmaz; çıktı varsa betik durur.
   - Kayıt `skills/tersane/scripts/lod_store.py` ile yapılır: `load(önceki)` ve `save_split(yeni)`.
     LOD'lar ayrı dosyaya gider, doku yolları göreli yazılır.
5. **TESLIM/ zip'leri eski:** v036'da kaldılar. Güncel iş için depoyu kullan.

## ► 1. KURALLAR (değişmez)
- **Dil:** Türkçe çıktı.
- **Sayılar:** kaynaksız sayı yazılmaz; [BİRİNCİL]/[İKİNCİL]/[TAHMİN] etiketi konur.
- **Onaylar:** Gate A insan onayı gerektirir, otomatik onay yok. `_context/` salt okunur.
- **Low-poly yasağı** ölçülür: her pass'te `quality_audit` çalışır. Faset = kiriş sapması > 1,5 mm; düz gölge ve havada ada da sayılır.
- **Git:** kendi dalında çalış; main'e merge yok, force push yok. Her adım commit + push edilir.
- **Varlıklar:**
  - Fab ya da lisanslı varlık depoya konmaz.
  - Kullanıcının tasarım paketi ("Project Pirate Tasarım") depoya konmaz; yalnız özet ve sayfa göndermeleri yazılır.
  - Meshy çıktısı kullanıcıya ait; lisans planı kullanıcıdan sorulacak (ücretsiz plan → CC BY 4.0, "Meshy AI" atfı gerekir).
- **Magnific ücretli:** hesapta 0 kredi var, harcama yapılmaz.
- **Kızıl Sancak kimliği** ("Yüzde Yetmiş Özgünlük Kuralı"): gemi kullanıcının oyunundaki **Kızıl Sancak İmparatorluğu**'na ait.
  - Osmanlı'dan esinli ama kopya değil. Birebir ay-yıldız sancak, tuğra gibi semboller kullanılmaz.
  - Onaylı plan: `reports/KIZIL_SANCAK_UYARLAMA_PLANI.md` (§0 kullanıcı kararları).
- **Top düzeni:** 20 borda + 2 baş = 22 top. Kıç topları kaldırıldı.
- **Çırak yatakhanesi** kaptan dairesinde değil; subay kabinlerinden de ayrı, alt güvertenin baş tarafında.

## ► 2. GEMİNİN ŞU ANKİ DURUMU (v046)
- **Kimlik:**
  - Oyun içi ad "Kızıl Pençe" (şimdilik); ana üs Sancakkale; donanma kurumu Kızıl Deniz Meclisi.
  - Kimlik bilgisi `00_CONTROLS/SHIP_IDENTITY` boşunda.
  - Arma kullanıcının konseptinden: hilal, mızrak, gök yıldızı, dalgalar (`scripts/kizil_sancak.py`).
- **Dış görünüm:**
  - Kızıl sancak ve flandra.
  - Ana mayistra ve ana gabyada kızıl bant ve arma.
  - Kıç arması ve "KIZIL PENÇE" ad levhası.
  - Toplarda tuğra yerine mühür.
  - Açık yelkenler B (dolgun karın, kıvrımlar, kanvas dokusu).
- **Pruva:**
  - Kurt figürü D (`MOD_FIGUREHEAD_KURT_D`, 450k üçgen). Alın ve omuzlardaki ay-yıldızdan yıldızlar silindi, hilaller kaldı.
  - Figür, mahmuzun (`MOD_BOW_RAM_A`) yuvasına oturuyor. Baş kıvrımı ve baş parmaklıkları kaldırıldı.
  - `SOCKET_RAM` mahmuz burnunda.
- **İç düzen:**
  - Kıç kamarası: CaptainOffice (makam) ve kaptan kamarası ayrı.
  - Alt güverte: hamaklar, sofralar, subay odası (4 kabin), revir, marangoz ve yelkenci atölyesi, ocak, çırak yatakhanesi.
  - Ambar: kurşun kaplı cephanelik, fener odası, hazırlama odası, erzak odası, gülle sandıkları.
  - Top güvertesi: 8 hazır servis dolabı ve rüzgâr hortumu.
  - Hasar kontrol: her güvertede 2 istasyon + ambarda 1.
  - Oda kimlikleri: `35_ROOMS` koleksiyonundaki boşlar (CompartmentID, RoomLabel, OperationalStationID, WatertightZoneID).
- **Blender içi anahtarlar:**
  - `00_CONTROLS/CTRL_YELKEN.yelken_acik`: 0 sarılı / 1 açık. N panelinde "Gemi" sekmesinde buton.
  - `00_CONTROLS/CTRL_SUSLEME.susleme_acik`: süslemeler açık / kapalı.
- **Kalite testi:** yalnız eski 5 hata var:
  - gövde kıç "tuck" bölgesi 7,3 mm (su altı);
  - filika 1,8 mm;
  - kıç galerisi 2,6 mm;
  - ocak 2,5 mm;
  - kıç arması 3,0 mm.

## ► 3. SIRADAKİ İŞLER (öncelik sırası)
1. **Dümen dolabı** (kullanıcı isteği, AC Black Flag görseli): bizdeki dümen `MOD_HELM_WHEEL_A` (x ≈ −17,4, z 6,65) tek başına
   bir öğe gibi duruyor. Güverteyle bütünleştir:
   - kaide / podyum;
   - dümen halatlarının tamburdan güverteye inişi;
   - pusula dolabı (binnacle);
   - çevre küpeşte, halat bağları, eşyalar.
2. **Mahmuz / figür ince ayarı:** kullanıcı onayı bekleniyor. Figürün arka montaj bloğunun üst kenarı yandan hâlâ az görünüyor;
   gerekirse `DISH_TAB`'ın arka değerleri artırılır.
3. **Kullanıcıya sorulacak:**
   - Meshy lisans planı.
   - Aynı 119 MB figür dosyasının depoda 3 kopyası var: `Imports/Meshy/Kurt Gemi Figürü.glb`, `Imports/Meshy/..._cle_...glb`
     ve kök klasörde `Kurt Gemi Figürü.glb`. Fazlalar silinsin mi?
4. **Kalan fasetler:** yukarıdaki 5 eski hata.
5. **UE hazırlığı:** Top C modülü UV + bake, FBX dışa aktarımı, UE malzeme notları.
6. **Tersane skill:** güncel (`skills/tersane/SKILL.md`, günlük v044'e kadar). v045–v046 dersleri eklenebilir:
   yıldız silme yöntemi (ışın + zemin düzlemi + UV maske dolgusu), yay uzunluğu + eğrilik ağırlıklı kesit örnekleme.

## ► 4. TUZAKLAR (bu oturumda öğrenilenler)
- **Dosya boyutu:** GitHub tek dosyada 100 MB sınırı var. LOD'lar ana blend'den ayrıldı (`lod_store.py`).
  Figür modelleri (`*.glb`) Git LFS'te.
- **Pembe malzeme:** doku yolları mutlak kaydedilmişti. Kayıttan önce `lod_store.make_relative` çağrılır.
- **Gizli nesneler:** sürücüyle gizlenen nesnelerde `matrix_world` değerlendirilmez. Ebeveynsizse `matrix_basis` kullan.
- **Render'da gizleme:** görünürlük sürücüleri `hide_render`'ı ezer. Render adımında önce sürücüyü sil (kaydetme).
- **Bekleme döngüsü:** `until ! pgrep -f X` kendi komut satırını da yakalar ve sonsuz döngüye girer.
  PID ile bekle ya da arka plan görevini kullan.
- **Yerleştirme:** çakışma testi üçgen düzeyinde yapılır (BVH). Parça atılırsa nesne nesne test edip `clash_with` raporla.
- **Faset:** süperelips kesitlerde noktalar köşede sıklaşır, ortada seyrekleşir. Yay uzunluğu + 0,15 × dönüş açısı ağırlığıyla
  yeniden örnekle. Dik profilde kesitleri yerel olarak sıklaştır.
- **Kullanıcı ince çubuk görünümünü sevmiyor** (baş parmaklıkları, altın silme tüpleri). Süsleri gövdeye gömülü yap.
- Ayrıntılı ders listesi: `skills/tersane/SKILL.md` §17.

## ► 5. SÜRÜM ÖZETİ (her sürümün ayrıntısı aşağıda ya da `reports/MODELLEME_PLANI.md`'de)
| Sürüm | İş |
|---|---|
| v001–v004 | gövde çekirdeği, paftalar, sade çarpışma, oynanış soketleri |
| v005–v011 | yüksek kıç, merdivenler, dümen, kıç galerisi, kaptan kamarası |
| v012–v019 | toplar, Hull_B alt güverte, arma, filika, çapa, ırgat, UCX |
| v020–v027 | gerçekçi top, bozkurt blockout, yelken + motifler, sancak, ambar, LOD, bake, frigat kararı |
| v028–v033 | Osmanlı tunç topu C, yelken anahtarı, kalite testi, Osmanlı süslemeleri, faset temizliği |
| v034–v037 | bozkurt figürü B–B3 (SDF), baş parmaklıkları, faset temizliği 2 |
| v038–v039 | açık yelkenler B, Meshy figür C |
| v040 | Kızıl Sancak dış kimliği |
| v041–v044 | Kızıl Sancak iç düzeni (kamara, alt güverte yaşamı, ambar/cephanelik, hazır dolaplar, hasar kontrol, havalandırma) |
| v045 | Kurt figürü D (yıldızlar silindi) |
| v046 | pruva mahmuzu + figür yuvası, baş parmaklıkları kaldırıldı |

## v046 — pruva mahmuzu (ram) + figür yuvası; baş parmaklıkları kaldırıldı
- Betik: `scripts/pass_v046_bow_ram_cradle.py`.
- Kullanıcı: "figür emanet gibi duruyor; bir Ram yap, yuva yapıp figürü oraya yerleştir; çubukları kaldır".
- **Çubuklar:** figürün yanındaki altın çubuklar baş parmaklıklarıydı (CORE_HEAD_RAIL_S/P); LOD'larıyla kaldırıldı.
- **MOD_BOW_RAM_A:**
  - Bodoslamadan öne uzanan tek parça mahmuz. Alt kenarı su hattından öne-yukarı süpürülüyor.
  - Burun x 25,95'te, bronz kaplı.
  - Üstünde figürün alt çizgisini izleyen yuva var. Arka yarıda 72 cm'lik yan duvarlar figürün bloğunu ve göğsünü sarıyor; pençeler burnun üstünde.
  - Süsler:
    - kalas dokusu;
    - yuva ağzında altın dudak ve altında kızıl bant;
    - alt kenarda bronz sakal şeridi;
    - burunda iki bronz halka.
  - Kesitler süperelips biçiminde. Çevre noktaları yay uzunluğu + eğrilik ağırlığıyla dağıtıldı (192 nokta). Kesit aralığı 2,5 cm, dik inişte 8 mm.
  - 157k üçgen; faset yok.
- **SOCKET_RAM:** mahmuz burnuna taşındı (x 25,95, z 3,5); oyunda çarpma noktası.
- **Ölçüler:** [TAHMİN]. Osmanlı kadırga "mahmuz"undan esinli, birebir değil.

## v045 — pruva figürü D: Kurt Gemi Figürü (yıldızlar silindi), bordaya gömülü
- Betikler:
  - `scripts/pass_v045_figurehead_kurt.py`
  - `scripts/figure_kurt_prep.py` (yıldız silme)
- **Kaynak:** kullanıcının `Imports/Meshy/Kurt Gemi Figürü.glb` dosyası (3,0 M yüz). Depoda Git LFS ile tutuluyor.
- **Yıldız silme:** alın ve iki omuzdaki ay-yıldızdan yıldızlar silindi, hilaller kaldı.
  - Geometri: kabartma, zemin düzlemine indirildi.
  - Dokular: yıldız bölgesi zeminin grenli dokusuyla dolduruldu (BC, N, ORM). Yeni dosyalar `Textures/Figurehead/T_Figure_KurtD_*.png`.
  - Figürün başka bir yerinde yıldız yok (6 açıdan tarandı).
- **Yerleşim:**
  - Baş kıvrımı (CORE_HEAD_KNEE) ve parmaklık destekleri kaldırıldı.
  - Yükseklik 3,0 m; boyut 3,85 × 1,47 × 3,28 m; 450k üçgen. Bodoslama tırmığına uyum için 15° öne eğik.
  - Montaj bloğu bodoslamaya 10 cm gömülü.
  - Parmaklık kolları yelede bitiyor.
  - Cıvadıraya en yakın mesafe 0,91 m.
  - Ölçü değerleri [TAHMİN, render ile ayarlandı].
- **Lisans:** Meshy planı kullanıcı tarafından doğrulanacak (ücretsiz plan → CC BY 4.0, atıf gerekir).
- **Doku yolları:** v045'ten itibaren göreli kaydediliyor. v044 ve öncesinde yollar mutlak bulut yoluydu; kullanıcının
  bilgisayarında dokular pembe görünüyordu.
- **Kalite testi:** figür geçti (en kötü faset 1,8 mm, eşik altı sayılır). Yalnız eski 5 hata kaldı.

## v044 — top güvertesi hazır dolaplar, hasar kontrol, havalandırma; LOD'lar ayrı dosyada
- Betik: `scripts/pass_v044_gundeck_ready_damage_vent.py` (v043 → v044).
- **Dosya boyutu:** v043 ana blend 99,5 MB idi (GitHub sınırı 100 MB). LOD'lar artık ayrı dosyada:
  - `OTTOMAN_FRIGATE_1780_ISTANBUL_v044.blend`: 45 MB, sahne, LOD'suz.
  - `OTTOMAN_FRIGATE_1780_ISTANBUL_v044_LOD.blend`: 60 MB, yalnız `50_LODS` koleksiyonu.
  - UE dışa aktarımı için LOD dosyası ana dosyaya Append edilir (File → Append → Collection → 50_LODS).
  - Betikler `skills/tersane/scripts/lod_store.py` ile yükler ve ayırır.
- **Hazır servis dolapları** (Ek Cilt II s. 112/115):
  - 8 adet, top çiftleri 2-3, 4-5, 6-7, 8-9 arasında, bordaya dayalı.
  - Paylaşılan mesh `SM_PROP_READY_LOCKER_A` (UE ISM), `27_GUNDECK_INSTANCES`.
  - Kızıl kapak, bakır kenar, asma kilit, halat kulp; kapasite 6 torba [TAHMİN].
- **Hasar kontrol istasyonları** (s. 87), güverte başına 2 + ambar:
  - top güvertesi (−9,0; 1,5) ve (4,3; 1,6);
  - alt güverte (−11,0; 2,4) ve (8,4; 1,8);
  - ambar (v043).
- **Havalandırma** (s. 97): kanvas rüzgâr hortumu (`MOD_VENT_WINDSAIL_A`).
  - Ana ambar ızgarasında kasalı ağızdan alt güverteye iner.
  - Mizana istralyasına asılı, kanatlı ağız pruvaya bakar, iki gergi halatı güverte halkasına bağlı.
  - Ana direğe uzanan ilk deneme istralyayla çakıştı.
- **Oda kimlikleri:** STATION_READY_SERVICE_P1–4/S1–4, STATION_DAMAGE_CONTROL_GUN_A/F, LOWER_A/F, HOLD, STATION_VENT_WINDSAIL.
- **Kalite testi:** yalnız eski 5 hata kaldı. Yeni nesnelerde faset yok, havada parça yok.
- **Renderlar:** `renders/v044/`.

## v043 — ambar: cephanelik, hazırlama odası, erzak ve gülle
- Betik: `scripts/pass_v043_hold_magazine.py` (v042 → v043).
- **Cephanelik** (ambar, baş; x 11,95–14,2):
  - kurşun kaplı ahşap bölme (`MAT_Lead_Sheet`, donuk) ve kurşun zemin;
  - raflarda 40 mühürlü barut fıçısı (`SM_PROP_POWDER_BARREL_A`, bakır çember + kurşun mühür;
    UE Instanced Static Mesh, `26_HOLD_INSTANCES`).
- **Fener odası** (`STATION_LIGHT_ROOM`): cephaneliğe camlı pencereden ışık veren ayrı fener; ateş cephaneliğe girmez
  (Ek Cilt II s. 111–115).
- **Hazırlama odası** (x 10,65–11,95):
  - ahşap zemin, barut torbası dolum tezgâhı, bakır ölçü kapları;
  - flanel torba rafları;
  - kıç kapıda ıslak perde (yangın kesici).
- **Erzak (ekmek) odası:** kıç ambarda bölme (x −12,35), çuval ve sandıklar.
- **Gülle dolapları:** 2 alçak sandık × 40 gülle (`SM_PROP_SHOT_PILE_A`, 9 librelik r 0,061 m [TAHMİN]).
  8 aday noktadan 6'sı ambar yapısıyla çakıştığı için atlandı.
- **Hasar kontrol istasyonu (ambar):** kızıl kapaklı dolap, tapa, kova, yedek kereste, kalafat üstüpüsü (s. 87).
- **Oda kimlikleri:** ROOM_MAGAZINE, ROOM_FILLING, STATION_LIGHT_ROOM, ROOM_BREAD_ROOM, ROOM_SHOT_LOCKER, ROOM_HOLD_CARGO
  (`35_ROOMS`).
- **Kalite testi:** 142 nesne, 5 hata; hepsi önceki sürümlerden kalan: gövde kıç tuck, filika, kıç galerisi,
  ocak 2,5 mm, kıç arması 3 mm. Yeni nesnelerde faset yok, havada ada yok.
- **Renderlar:** `renders/v043/` (ambar_ust, cephanelik, hazirlama, erzak_gulle).

## v042 — kaptan dairesi düzeltmesi + alt güverte yaşamı
- Kullanıcı: çırak rıhtımı kaptan dairesinde olmaz, kıç topları kalksın (toplam 20 borda + 2 baş topu) →
  - kıç topları ve soketleri silindi (22 top);
  - sancak-ön bölme kalktı, çalışma masası eski köşesine döndü, yazı rafı kıç kasarası duvarında.
- Kullanıcı: çırak yatakhanesi subay kabinleriyle iç içe olmasın → ayrı perdeli **çırak yatakhanesi**:
  - alt güverte baş, x 12,0–14,15, pruva direğinin iki yanı;
  - 2×2 ranza, sandıklar, ders tahtası.
- Alt güverte:
  - hamaklar: 37 asılı + 17 sarılı (vardiya);
  - 8 bordaya asılı sofra;
  - subay odası: 4 perdeli kabin + sofra;
  - revir: 2 asma yatak, cerrah sandığı;
  - marangoz ve yelkenci atölyeleri;
  - tuğla ocak, bakır kazanlar, üst güverteden çıkan baca, su fıçısı.
- Üst güverte: içme suyu fıçısı (scuttlebutt), baş tuvaletleri.
- Her parça üçgen düzeyinde çakışma testiyle yerleşti (`try_add` / `try_shift`).
- Oda kimlikleri: `35_ROOMS`.

## v041 — iç düzen 1: kıç kamarası bölündü (Ek Cilt II s. 98–99)
- CaptainOffice (makam; kıç pencereli büyük kamara): toplantı/harita masası, çalışma masası, büfe, yazı rafı,
  ferman/mühür kutusu, Kızıl Sancak duvar sancağı; kıç topları burada (eşyalar `clear_for_action`).
- Kaptan kamarası (iskele-ön): asma yatak, sandık, lavabo dolabı, kitap rafı, askı.
- Çırak / junior rıhtımı (sancak-ön): ranza, deniz sandığı, ders/harita tahtası.
- Kızıl cilalı kapılı bölmeler (`MOD_CABIN_PARTITIONS_A`, 6 UCX); oda kimlikleri `35_ROOMS/ROOM_*`
  (CompartmentID / RoomLabel / OperationalStationID / WatertightZoneID); ad levhası 4 cm aşağı.
- Parça kütüphanesi: `scripts/interior_kit.py`.

## v040 — Kızıl Sancak dış kimlik
- Sancak ve flandra: kızıl zemin, altın işleme kenar, arma, çatal uç (`scripts/make_kizil_sancak_textures.py`).
- Ana mayistra ve ana gabya: orta 2,44 m kızıl bant + iki yüzlü arma amblemi.
- Kıç arması: kızıl mine madalyon üzerinde arma.
- Top C: tuğra söküldü, yerine arma mührü (kabartma, Delaunay kapak); kitabe kaldı.
- Kıç ad levhası: altın harfle "KIZIL PENÇE".

## v039 — bozkurt figürü C (Meshy AI, kullanıcı üretimi)
- `Imports/Meshy/*.glb` (2,40 M üçgen, 4K BC + 4K N + 2K ORM) → köşe birleştirme (930 → 1 ada) → 250k üçgen →
  yüz pruvaya (+X), ×1,25 (2,38 × 0,90 × 1,88 m) → hilal motifli montaj plakası baş kıvrımına oturur.
- UCX 61 köşe, LOD'lar, cıvadırayla 1,96 m boşluk; kalite testi geçti (havada parça yok). Eski B figürü sahneden çıktı
  (v036–v038 dosyalarında duruyor; kaynak `wolf_sdf2.py`).

## v038 — açık yelkenler B (kullanıcı: "yelkenler basit duruyor", Fab referansı)
- 11 açık yelken yeniden kuruldu (`scripts/pass_v038_sails_b.py`): ≈ 12 cm ağ, Coons yaması (köşeler/yaka yerinde),
  rüzgârla dolgun karın (kare 0,10·en, flok/velena 0,08, randa 0,07 [TAHMİN]), alt kenar kavisi, yaka kıvrımları,
  köşe gerilme kırışıkları, kenar halatı, gabyalarda 3 camadan bandı + bağlar; amblemler yeni yüzeye taşındı.
- Kanvas dokusu `Textures/Sails/T_Sail_Canvas_B_{BC,N,ORM}` (`scripts/make_sail_canvas.py`), "Weathering" renk özniteliği.
- Bulgu: açık yelkenler varsayılan gizli → matrix_world hesaplanmıyordu (LOD'lar orijine konuyordu) → `lods.py`
  ebeveynsiz nesnede matrix_basis kullanır. Kalite testi açık yelkenleri ayrıca ölçer (`kalite_testi_v038.json` →
  open_sails); kalan ≈ 3 mm faset kıvrım dalgalarında → sonraki turda ağ sıklaştırma.
- Pruva figürü: kullanıcı Meshy GLB (37 MB) yükleyecek → `Imports/Meshy/` → incele, tek parça yerleştir.

## v037 — faset temizliği 2. tur (23 → 3 nesne)
- Çanaklıklar: ana/mizana çanaklığı direk yatıklığı kadar eğik olduğundan v033 seçiminden kaçmıştı → topolojiyle 4 halka
  + uyarlamalı Catmull-Rom (üç direk; 16 mm → 0).
- Hareketli arma: makara/babada keskin dönüş (116 mm) → `resegment.fillet_kinks` (±d halkası, d = max(3r, 4 cm)) +
  0,6 mm toleransla sıklaştırma → eşik altı.
- Filika, ırgat, kıç panoları, fener, dümen dolabı, tulumba, ambar yükü, alt kuşak, bodoslama, 4 seren, 2 sarılı yelken:
  yalnız faset adalarına kıvrımlı (crease) 1 düzey Catmull-Clark; ölçülerek tutuldu (sapma ≤ 12 mm, en kötü sapma azaldı).

## v036 — bozkurt figürü B3 (patinalı bronz, oyma yele)
- Kullanıcı v035 için "figür olmamış" dedi: yele tutamları "solucan" gibi; altın kenar çizgileri etkiyi büyütüyordu.
- Hazır varlık arandı: ortamdan yalnız GitHub erişilebilir, uygun model yok → Blender'da yeniden denendi.
- Denenen ve bırakılan: basık, oluklu "kiremit" tutamlar (oluklar 6 mm vokselde çukur/delik bıraktı; büyük tutamlar hamur
  gibi topaklandı). Seçilen: v035 tutamları yumuşak kaynak (k 0,012, kabarma ×0,85) → tek oyma kütle; malzeme
  `MAT_Figure_WolfBronzePatina` (çukur koyu patina, çıkıntı aşınmış bronz); diş/dil sınırı malzeme tırtıkları temizlendi.
- Tek ada, kapalı mesh, 260k üçgen, UCX 64 köşe; 302 tutam; baş parmaklıkları v035'teki gibi.

## v035 — bozkurt figürü B2 (SDF yontusu) + baş parmaklıkları
- v034 figürü (metaball) kullanıcıya göre çok kötüydü → SDF yontusu: anatomik kurt başı (kafatası %55/burun %45), açık çene,
  kavisli köpek dişleri, burun delikleri, hırlama kıvrımları, çatık kaş, oyuklu kulaklar, yüzeye yatan 319 tüy tutamı
  (boyun/yele, yanak, tepe, boğaz), altın gadroon kuşaklı + rumi sarmallı kaide. Tek SDF alanı → tek ada, kapalı mesh;
  260k üçgen (hero), UCX 57 köşe. Araç: `skills/tersane/scripts/sdf_sculpt.py` (gerekli: scikit-image).
- Baş parmaklıkları gemiden ayrıydı (arka uç bordadan 0,67 m uzak, 4 köşeli kesit) → kaideden başlayıp bordaya (x 20,1)
  gömülen Bezier yol, yuvarlatılmış silme profili, her yanda baş kıvrımına inen 2 destek.

## v034 — bozkurt figürü B (tek parça)
- Konsept "Sea Wolf": öne uzanan, ağzı açık hırlayan kurt başı, geriye savrulan yele, koyu tunç + altın (çıkıntılar).
- Parçalar ayrı kuruldu (metaball gövde + kaide, 2 kulak, 2 göz, 20 diş, burun, dil) → gövdeye gömüldü → EXACT boolean
  birleşim → **tek ada, kapalı (manifold) tek mesh**; 45,8k üçgen; UCX 57 köşe; cıvadırayla 1,61 m boşluk; baş parmaklıkları
  kaideye oturuyor. Modül değişimi: `SOCKET_FIGUREHEAD` → tek nesne.

## v033 — faset temizliği
- Minderler bevelli yuvarlak kutu; arma eğrileri 2–2,5×; alemler/rozet göbeği profil sıklaştırma; kıç panosu ve tavan
  yumuşatma; ön çanaklık 64 → 192 nokta (16 → 3,3 mm); flandra alt bölme. Hatalı nesne 27 → 23.

## v032 — friz kesintisiz, kıç arması yönü
- Gövde rumi frizi yalnız lumbar arkasında kesilir; kıç armasında yıldız hilalin açık tarafında (arkadan bakana göre).

## Durum
- **Gate A: ONAYLA** (yön: hibrit, "Osmanlı esintili frigate").
- **2. karar:** Kullanıcı "kalyon istemiyorum, topları frigate'e göre düzenle; demo bölgesi gemisi (veya brig)" dedi.
  - Tip: üç direkli, tek batarya güverteli frigate. Referansların hepsi üç direkli olduğu için brig değil.
  - Çapa: HMS *Lyme* (1748): 35,92 m × 10,31 m. Su çekimi 4,5 m (tahmin).
  - Top: 24 batarya (12/borda) + 4 kıç kasarası + 2+2 kovalama lumbarı.
  - Ayrıntı: `reports/MODELLEME_PLANI.md`.
- `ship_spec.yaml` frigate'e göre güncellendi. Kalyon değerleri `archived_*` altında.
- **Blender:** bulut oturumunda `bpy` 5.0.1 (headless) ile Hull Core v001 üretildi.
  - `.blend`: `Blender/versions/OTTOMAN_FRIGATE_1780_ISTANBUL_v001.blend`
  - Betik: `scripts/build_hull_v001.py`. Yerelde `blender --background --python scripts/build_hull_v001.py` ile de çalışır.
  - Audit: `reports/scene_audit_v001.json`
  - Renderlar: `renders/v001/` (baş, kıç, iki profil, baş omzu, kıç omzu, güverte)

## Kararlar (2026-09-25)
- Ölçüler ONAYLANDI. Klasör `OTTOMAN_FRIGATE_1780_ISTANBUL` oldu.
- Baş kovalama lumbarı 2; ayrıca pruva mahmuzu (ram). Kasara yüksekliği 2,0 m.
- Her yer gezilebilir ve tırmanılabilir (AC tarzı).
- **Kıç:** kullanıcı görseli tarzında yüksek, merdivenle çıkılan kıç üstü güverte; üzerinde dümen → v005'te yapıldı. Kullanıcı ileride eklenecek bir şey olursa söyleyecek.

## Skill
- `skills/tersane/SKILL.md`: bu gemide öğrenilenler (gemi bitene kadar güncellenir; kullanıcı daha sonra skill'lere ekleyecek).

## v031 (son sürüm) — Osmanlı süslemeleri + kuşak tahtası
- Anahtar: Outliner → `00_CONTROLS/CTRL_SUSLEME` → Custom Properties → `susleme_acik` (1 açık / 0 sade). Modüller: `25_MODULES_ORNAMENT`.
- Kuşak tahtaları lumbarların üstüne taşındı; zincir levhaları lumbar önünden çekildi (kullanıcının gösterdiği "kalmış parça").
- Dokular: `Textures/ornaments/` (BC + H); UE için H → normal bake, altın maskesi renkten (metalik).
- Sıradaki: süsleme renderlarını gözden geçir; kalan küçük fasetler (kıç panosu, minder köşesi); direk çanaklık kenarı;
  gövde kıç tuck; bozkurt figürü nihai model; top C UV/bake.

## v030 — kalite testi (low-poly yasağı denetimi)
- Rapor: `reports/KALITE_TESTI_v030.md` (+ `kalite_testi_v029.json` / `kalite_testi_v030.json`). Hatalı nesne 86 → 23,
  faset kenar 15.249 m → 343 m, havada parça 35 → 0. Araçlar Tersane skill'inde: `quality_audit.py`, `resegment.py`.
- Küpeşte/silme/bordalar yeni profil; lumbar çerçeveleri gövdeye oturuyor (artık çubuk giderildi); halat/seren/direk/bigot
  kiriş sapması ≤ 1,5 mm; gövde Subdivision viewport = render = 2; fıçılar tek mesh + 282 örnek; merdivenler güverteye
  basıyor; 17 yönlendirme makarası; gabya bigotları/bumba çatalı/cıvadıra başlığı/raf kancaları/palanga halkası yerinde.
- Kalan (raporda): direk çanaklık D köşeleri, gövde kıç tuck bölgesi, filika uçları, eşiğe yakın küçükler; figür BLOCKOUT.
- Sıradaki: v031 Osmanlı süslemeleri (iç + dış) — dokular hazır: `Textures/ornaments/` (`scripts/make_ottoman_ornaments.py`).

## v029 — yelken anahtarı
- Outliner → `00_CONTROLS/CTRL_YELKEN` seç → Object Properties → Custom Properties → `yelken_acik` 0 = sarılı, 1 = açık.
- Ya da 3D Görünüm → N → "Gemi" sekmesi → "Yelkenleri Aç/Sar" (Auto Run kapalıysa Scripting → `yelken_anahtari.py` → Run Script).
- Yedek: Outliner'da `21_MODULES_SAILS/SAILS_SARILI` ve `SAILS_ACIK` koleksiyonlarının onay kutuları.

## v028 — Osmanlı tunç topu C
- `MOD_CANNON_OTTOMAN_C` 28 top (namlu 16,8 k, kızak 5,3 k üçgen), 40 yan palanga, 10 alet rafı. Tuğra/kitabe STİLİZE (gerçek metin değil).

## v027
- `scripts/pass_v027_frigate_lower_stairs.py`: FRIGATE kararı (hat gemisi ayrıntısı yok); alt güverte yükseltmesi 3+3 top, dengeli ve şaşırtmalı, ortak salvo grubu; ambar ağızları yeniden açıldı; merdiven çakışmaları giderildi. §5ac.

## v026
- `scripts/pass_v026_lods.py`: LOD zinciri (`50_LODS`). `scripts/bake_tile_textures.py`: 11 malzeme için BaseColor/Normal/ORM tile dokuları (`Textures/tiles/`). §5aa.
- Top varyantları (gemide kullanılmaz): `FBX/Modules/Cannons/`, `Blender/versions/CANNON_VARIANTS_v001.blend`. §5ab.
- Kullanıcının belirlediği sıra tamamlandı: yelkenler, toplar, bozkurt (blockout), halat ve makaralar, bayrak, ambar, LOD ve bake.

## v025
- `scripts/pass_v025_hold.py`: ambar iç mekânı. §5z.

## v024
- `scripts/pass_v024_flags.py`: sancak (gaf ucunda) ve flama. §5y.

## v023
- `scripts/pass_v023_running_rigging.py`: hareketli arma ve makaralar. §5x.

## v022
- `scripts/pass_v022_sailset.py`: sarılı yelkenler (varsayılan) + açık yelken varyantı + lale/rumi motif modülleri. §5w.
- Kullanıcının belirlediği sıra (aksi söylenmedikçe): halat ve makaralar → bayrak → ambar içi → LOD ve doku bake.

## v021
- `scripts/pass_v021_figurehead_bozkurt.py`: bozkurt figürü — BLOCKOUT (yer tutucu). §5v.

## v020
- `scripts/pass_v020_cannon_realistic.py`: `MOD_CANNON_9PDR_B` gerçekçi top. §5u.

## v019
- `scripts/pass_v019_qa_fixes.py`: UCX kalite düzeltmeleri (filika UCX'i sadeleşti, tırmanma UCX adları UE kuralına uydu). Geometri v018 ile aynı. §5t.

## v018
- `scripts/pass_v018_battery_dressing.py`: alt güverte asma dirsekleri, halka cıvataları, brok halatları, gülle rafları, 2 tulumba. §5s.
- Ölçülü pafta: `renders/v018/olculu/` (`annotate_views.py` artık armalı gemiyi kadraja sığdırıyor; alt güverte ve direk tepesi ölçüsü eklendi).

## v017
- `scripts/pass_v017_boat_anchor_capstan.py`: filika + kızaklar, 2 ana çapa + kedi başları, ırgat. Ölçüler TAHMİN. §5r.

## v016
- `scripts/pass_v016_cabin_interior.py`: kaptan kamarası eşyaları (masa, sandalyeler, yazı masası, asma yatak, sandık, büfe, kıç sediri, fener); ayrı `InteriorSet` modülleri. Üst ve alt güvertenin kıç aynasına kadar uzanmayan kısmı kapatıldı. Ayrıntı: MODELLEME_PLANI §5q.

## v015
- `scripts/pass_v015_rigset.py`: 3 direk + çanaklıklar + 9 seren + gaf/bumba + cıvadıra; sabit arma, iskalarya, 12 tırmanma rotası, UCX. Oranlar TAHMİN (Lees ile doğrulanmalı). Filika soketi taşındı. §5p.

## v014
- `scripts/pass_v014_cannon_9pdr.py`: `MOD_CANNON_9PDR_A` (kızak + namlu ayrı); 24 top takılı, alt güverte 20 soket boş. 216 soket güverte yüzeyine oturtuldu. §5o.

## v013
- `scripts/pass_v013_hull_b_lower_deck.py`: **Hull_B** (kullanıcı kararı "1"). Gemi suda +1,00 m yükseldi (su çekimi 3,95 m); alt top güvertesi (üstün 2,2 m altı), 10+10 kapaklı lumbar, 3 ambar ağzı, 2 iniş merdiveni, subay bölmesi, 8 fener, 100 yeni top/mürettebat soketi. §5n.

## v012
- `scripts/pass_v012_guns20.py`: 20 borda (10/borda) + 4 kovalama. Alt güverte topları ileride yükseltme olarak eklenecek (yüksek bordalı Hull varyantı gerekir).

## v011
- `scripts/pass_v011_lower_stern.py`: kıç kasarası yok; tek yükseltilmiş kıç üstü (ana güverte + 2,64 m) + altında kaptan kamarası (kapı belde); köşe merdivenleri; 22 ana top + 4 kovalama. Ayrıntı: MODELLEME_PLANI §5l.
- **Kaptan kamarası = kıç üstü altı.** Ek kamara yok.

## v010 (geri alındı: alt kamara duvarı v011'de kaldırıldı)
- `scripts/pass_v010_great_cabin.py`: kıç kasarası altı kapılı kaptan kamarası; kıç kasarası merdivenleri duvar boyunca köşelere; ana batarya yeniden dizildi. Ayrıntı: MODELLEME_PLANI §5k.
- Kamara içi boş (mobilya yok).

## v009
- `scripts/pass_v009_fc_stairs_corners.py`: baş kasarası merdivenleri köşelerde; ana batarya 1-11 yeniden dizildi. Ayrıntı: MODELLEME_PLANI §5j.

## v008
- `scripts/pass_v008_access_stairs.py`: bel → kıç kasarası ve bel → baş kasarası (ikişer merdiven), yeni ön korkuluklar; 12. top çifti baş kasarası altına. Ayrıntı: MODELLEME_PLANI §5i.
- Sıradaki aday: direkler ve arma (tırmanma işaretleriyle) ya da alt güverte / ambar iç mekânı.

## v007
- `scripts/pass_v007_scale.py`: gemi eşit oranda ×1,10 (kullanıcı izni). Net tavanlar 2,01-2,06 m; güverte boyu 39,51 m, en 11,34 m, su çekimi 4,95 m.
- **ÖNEMLİ:** v007+ dünya = 1,10 × tasarım uzayı. Yeni pass'lerde `scripts/ship_scale.py` sarmalayıcısını kullan.

## v006
- `scripts/pass_v006_stairs_corners.py`: kıç üstü merdivenleri köşelere (kullanıcı: "biri sağ biri sol köşede"); kıç kasarası topları -10,0 / -7,7. Ayrıntı: MODELLEME_PLANI §5g.

## v005
- `scripts/pass_v005_stern.py`: poop + kamara + 2 merdiven + balüsterler + kafesli kıç/yan galeriler + güneş tepelik + fener + dümen; kıç kasarası topları ileri alındı; 68 UCX. Ayrıntı: MODELLEME_PLANI §5f.

## v004
- `scripts/pass_v004_gameplay_sockets.py`: mahmuz, dümen ve komuta istasyonları, 128 mürettebat noktası, batarya grupları; top soketi yönleri düzeltildi.

## v003
- `scripts/pass_v003_collision.py`: yalnız çarpışma yeniden kuruldu. 50 sade UCX: gövde, yürünebilir güverteler, küpeşte duvarları; bel açık. Çarpışma viewport'ta gizli.
- Fab referans raporu geldi. Çıkarımlar `reports/MODELLEME_PLANI.md` §5d'de. Ana ders: dış kabuk hafif, detay dokuda. Bizim kabuk için LOD0 ve bake gerekli.

## v002
- `scripts/pass_v002_fix_stern_keel.py`: v001'i açar ve yalnız gövde kabuğu, omurga, bodoslamalar, dümen ve UCX'i yeniden üretir.
- Kullanıcı bulguları (kıç/dümen kopukluğu, baş omurga açıklığı) giderildi. Ayrıntı: `reports/MODELLEME_PLANI.md` §5b.
- Renderlar: `renders/v002/`, ölçülü pafta: `renders/v002/olculu/`

## Kalıcı kurallar
- `reports/URETIM_GEREKSINIMLERI.md`: UE 5.8, fotogerçekçi ve game-ready, modüler yapı, yürünebilir güverte, versiyonlu kayıt, her pass sonunda render ve audit, gerekmedikçe tüm gemiyi yeniden kurmama.
- Toplar mürettebatla yönetilir. Komuta zinciri: oyuncu → 2. kaptan → topçu subayı.

## Açık kararlar
- Kasara güvertesi yüksekliği: 2,0 m (tarihe yakın, UE kapsülü için dar) mı, 2,3 m (oynanış) mı?
- Oynanabilir alan kapsamı: yalnız açık güverteler mi, alt güverte ve kıç kamarası da dahil mi?
- Frigate ölçülerinin onayı (Gate A revizyonu): ONAYLA / DEĞİŞTİR.
- Burun: 2 kovalama lumbarı (frigate) mı, konseptteki 3 top mu (varyant)?

## Fab referansı
- Rapor: `reports/reference_audit/age_of_sail/` (render adımı kullanıcı ortamında görsel üretmedi). Varlığın kendisi repoya girmez.

## Sıradaki adım
- Kullanıcı incelemesi: v013-v016 renderları (`renders/v013` … `renders/v016`).
- Aday işler: SailSet (yelkenler; sarılı mı açık mı kararı), hareketli arma (halat/makara), figür (at başı), bayrak/fener seti, iç postalar, ambar (hold) iç mekânı, UV/PBR bake ve LOD.
- Arma oranları için Lees tablosuyla doğrulama (yerelde kitap/PDF varsa).

## Eski sıradaki adım notları (v002 dönemi)
- v002: kıç aynası ve galeri (`SternModule`), lumbar kapakları, güverte donanımı, bocurumlar.
- Sonra: RigSet (direk boyları için kaynak), CannonBattery, SailSet.
