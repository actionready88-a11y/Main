---
name: tersane
description: Oyun için (Unreal Engine 5.x) fotogerçekçi, game-ready, modüler tarihî yelkenli gemi üretimi — Blender bpy (headless) ile sürümlü pass zinciri, gövde/güverte/kıç/arma/yelken/top/iç mekân/çarpışma/soket/LOD/bake/FBX. Kullanıcı yeni bir gemi (frigate, brig, kalyon, kadırga, çalupa…) istediğinde, mevcut bir gemiye pass eklerken, gemi modellerini denetlerken veya UE teslim paketi hazırlarken kullan. OTTOMAN_FRIGATE_1780_ISTANBUL projesinde öğrenilen kurallar, yöntemler ve hatalar.
---

# Tersane — Gemi Yapım Skill'i

Bu skill, `OTTOMAN_FRIGATE_1780_ISTANBUL` gemisi (v001–v027) yapılırken öğrenilenleri toplar. Amaç sonraki gemileri
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
  Ama bütçe gözetilir (bkz. §9).
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

## 4. Koordinat, ölçek, su hattı

- Blender metre; X ileri (baş), +Y sancak, Z yukarı; **su hattı Z = 0**; kök orijin orta hat / referans kesit.
- **Tasarım uzayı ↔ dünya:** gemi sonradan büyütülürse (ör. ×1,10 oyun ölçeği) tüm tasarım fonksiyonları tasarım
  uzayında kalır; dünya = K × tasarım (+ su hattı kaydırması). `ship_scale.py` sarmalayıcısı, `W(p)` yardımcısı.
- Gövde suda yükseltilecekse (ör. +1,00 m): mesh'leri veride (`data.transform`) taşı → pivot su hattında kalır;
  orijini sıfır olmayanlarda `location.z` artır. Yüzdürme soketlerini yeni su hattına göre yeniden hesapla.
- Tavan/kafa payı: oyun karakteri için **kiriş altı ≥ 1,85–1,90 m**; kasara/kamara altı ≥ 2,0 m. Gerekirse gemiyi
  oransal büyüt (kullanıcı izni ile).

## 5. Gövde (Hull Core) yöntemi

- Kesit: su hattı altı süper elips (`fullness(s)`), üstü tumblehome; `plan(s)` en dağılımı; `deck_z(s)` sheer;
  `top_z(s)` küpeşte; `stern_x`, `bow_x`, `stern_close` (ayna altı kapanış). Izgara NS×NZ, satır dağılımı `row_z` kancası.
- Kabuk: yarım gövde ızgarası ×2 + ayna ızgarası (n-gon yok) + alt dikiş; kenarlara `crease_edge`; Subdivision +
  Solidify (içe, iç yüz malzemesi ayrı). Malzeme bandı yüksekliğe göre.
- Şeritler (wale, silme) `band_strip`; güverte `deck_surface` (kamburluk 0,12 m tasarım, Solidify 0,10).
- **Güverte kıç ucu** aynaya kadar uzanmalı (`s0 ≈ 0.006`), yoksa kamarada/alt güvertede 0,2–0,6 m boşluk kalır.
- Lumbarlar: kesici küpler + Boolean; çerçeveler ayrı nesne. İkinci top sırası = yeni hull sınıfı (§1).

## 6. Boolean ve delikler — MUTLAKA DOĞRULA

- **EXACT boolean mesh değişince sessizce başarısız olabilir** (hata vermez, delik açılmaz). v016'da güverte mesh'i
  yenilendi, ambar ağızları kapandı, merdivenler güvertenin içinden geçti; ancak v027'de fark edildi.
- Güverte gibi ince katılarda `solver = "FLOAT"` kullan; her delik için **ışın testi** yap
  (`scene.ray_cast` yukarıdan aşağı: isabet yoksa açık) ve sonucu audit'e yaz.

## 7. Merdiven, ambar ağzı, erişim

- Merdiven kirişleri eğimden dolayı üst uçta güverte kalınlığına/koaminge, altta güverteye girer.
  **Kırp:** ayak `p0.z + 0,06`, üst uç `run − 0,14` (bkz. `pass_v027` `stair_clipped`).
- Her pass sonunda **BVH çakışma testi** (merdiven × tüm CORE/MOD mesh'leri) → hedef 0 çift.
- Merdiven açısı: güverte arası 41–44°, ambar/alt güverte iniş merdiveni 53–58°; basamak ~0,23–0,25 m.
- Merdivenler kullanıcı tercihine göre köşelerde; ambar ağızları mürettebat şeritlerinin (|y| < 1 m orta yol) içinde,
  direklerden ≥ 2 m uzakta.
- Kapı/erişim için navlink soketleri (`SOCK_NAVLINK_*_{TOP,BOTTOM}` / `_{OUT,IN}`).

## 8. Soketler ve oynanış verisi

- Adlar: `SOCKET_*` (modül takma), `SOCK_*` (oynanış noktası). Özellikler: `manifest_version`, `mount_id`
  (uuid5), `module_family`, `slot`, `battery_group`, `fire_group` (BROADSIDE_STARBOARD/PORT), `fire_level`, `upgrade`.
- Top soketi yerel eksen: +X namlu yönü (dışa). Mürettebat: A nişancı (−1,9;0), B doldurucu (0,1;0,95),
  C tokmakçı (0,1;−0,95), D manivela (−1,0;0,95) — ×ölçek.
- **Soketleri güverte yüzeyine ışınla oturt** (kamburluk + sheer yüzünden orta hat yüksekliği 0,1–0,3 m hatalı).
- Denetimler: mürettebat güverte içinde mi, merdiven/bölme/eşya ile çakışıyor mu, ırgat/tulumba/yataklar
  mürettebata ≥ 0,9 m.
- Yükseltme topları: dengeli yerleşim (bordada simetrik, eşit aralık, ortalama x ≈ üst batarya merkezi),
  üst lumbarlarla şaşırtmalı; varsayılan kapalı kapak + `default_enabled=false`.
- Bir soketin üstünden geçen başka bir parça olmasın (filika ↔ ana direk, bayrak direği ↔ randa bumbası):
  audit'e mesafe testi koy.

## 9. Çarpışma (UCX)

- Sade dışbükey parçalar (`C3.convex`), **≤ 64 köşe**; ad `UCX_<RenderMesh>_NN`, `ucx_purpose`, `owner_mesh`
  özelliği; iki aşamalı yeniden adlandırma (`_tmp_` → son ad) ile `.001` çakışmasını önle.
- İç mekân varsa gövdeyi dolu yapma: ambar altı dolu dilim + borda duvarları + güverte levhaları.
- Güverte levhaları delik farkında (`deck_pieces(..., holes=[...])`), ambar ağzı koamingleri ayrı.
- Tırmanma: çarmıh düzlemi başına ince levha (`climb_shrouds`), çanaklık/kıstak yürünür, seren/cıvadıra kutusu.
- 40_COLLISION koleksiyonu viewport'ta gizli.

## 10. Arma (RigSet) — oranlar TAHMİN (Lees ile doğrula)

- Ana alt direk = (güverte boyu + en)/2; çap yarda başına 1 inç; pruva 8/9 ana; mizana 0,86; gabya 0,6 × alt direk;
  babafingo 0,5 × gabya; ana alt seren 0,56 × güverte boyu; gabya 0,72 × alt; babafingo 0,66 × gabya; cıvadıra
  0,6 × ana direk, eğim ~25°. Yatıklık 0 / 1,5 / 3°.
- Çanaklık: D biçimli tek parça (ışınsal halka ızgara; kareli ızgara tırtıklı görünür), lubber deliği, kıç korkuluğu.
- Seren: ayrı nesne, pivot askıda (brasya dönüşü); altında basamak halatı + üzengiler.
- Sabit arma: kuşak tahtası (küpeşte üst − 0,35), bigotalar + savlo, çarmıhlar (9/9/5), iskalarya 0,40 m, futtock,
  gabya/babafingo çarmıhları, patrisalar, istralyalar. Hareketli arma: kaldırıcı, mandar, brasya → makaralar →
  palanga parmaklığı (fife rail) pinleri; parmaklıkları mürettebat/tulumbadan uzak koy.
- Tüp halatlar: 4–6 dilim; toplam arma ~65 k üçgen (sabit) + ~20 k (hareketli).

## 11. Yelken, bayrak, motif

- Varsayılan **sarılı** (seren üstünde rulo + gasket), açık yelken **gizli varyant** (`sail_state`), UE'de kumaş.
- Motif/decal: yelken yüzeyini izleyen ayrı iki yüzlü mesh + saydam PNG (PIL'de 2× çizip küçült). Modül + soket
  (`SOCKET_SAIL_EMBLEM_*`). Sarılı yelkende desen görünmez — kullanıcıya söyle.
- **Blender içi anahtar şart** (kullanıcı betik çalıştırmadan açıp kapayabilmeli): `CTRL_YELKEN` boşu + `yelken_acik` 0/1
  özelliği, her yelkenin hide_viewport/hide_render'ı basit ifade sürücüsüyle bağlı (Auto Run gerekmez); ayrıca N paneli
  butonu (`use_module` metin bloğu) ve Outliner'da `SAILS_SARILI` / `SAILS_ACIK` alt koleksiyonları. Başka her varyant
  (lumbar kapağı açık/kapalı, bayrak, alt güverte yükseltmesi) için aynı desen.
- Bayrak: dalgalı ızgara (UE kumaş için), orijin gönderde. Kıçta bumba varsa sancak gaf ucundan çekilir.
  Osmanlı donanma sancağı: 1793'te resmî (kırmızı, beyaz hilal + 8 köşeli yıldız) [İKİNCİL] — tarih farkını not et.

## 12. Top modülü

- Namlu ve kızak ayrı mesh; namlu kızağın çocuğu, pivot muylu ekseni; mesh soketleri MUZZLE / TOUCHHOLE.
- Gerçekçilik için: kaskabel topuz/boyun, taban halkası (ogee), falya astragalı + yastığı, takviye halkaları,
  kovan astragalı, ağız şişkinliği ve dudak, iç namlu; muylu kök bileziği. Kızak: tek parça basamaklı yanak
  profili (kutu yığını değil), muylu yuvası, bombeli tekerler + demir göbek + perno, takoz sapı, muylu kapakları,
  halkalar, cıvata başları. Dökme demir malzemesi (pürüzlülük gürültüsü + hafif pas).
- Varyant paketi (gemide kullanılmayan): ayrı `.blend` + `FBX/Modules/<Aile>/SM_*.fbx` + manifest.

## 13. Figür (heykel)

- **Skin modifier ile prosedürel hayvan/insan figürü oyuncak gibi görünür** (denendi: bozkurt). Blockout olarak işaretle
  (`quality = blockout`), soket/ölçü/malzeme yuvasını hazırla; nihai model için sculpt, AI 3D (ücretli servis — kullanıcı
  onayı) ya da lisanslı hazır varlık öner.

## 14. İç mekân

- Kamara, subay bölmesi, alt güverte, ambar: eşyalar ayrı `InteriorSet` modülleri (orijin zeminde, soketli).
- Yerleşimden önce mürettebat/kovalama topu noktalarını ve gövde sınırını denetle (hull_point − 0,24 iç yüz).
- Yük (fıçı vb.) bütçesi: fıçı ~130 üçgen; 300 fıçı ≈ 60 k. Daha fazlası için UE instanced mesh öner.
- Önizleme ışığı (render-only) ayrı; oyunda UE ışığı — soketlerde `light` notu.

## 15. LOD, bake, export

- LOD (`pass_v026_lods.build_lods`): ≥ 2000 üçgenli benzersiz mesh'ler; modifier yığını uygulanmış kopya → Decimate
  %50/%20 (gövde +%8); `50_LODS`, gizli, `<Kaynak>_LOD<n>`. Paylaşılan mesh bir kez. Geometri değişince yeniden üret.
- Tile bake (`bake_tile_textures.py`): UV'ler metre ölçekli → her prosedürel malzeme 4×4 m düzleme; iki UV
  (`UVMap` metre = active_render, `BakeUV` 0–1 = active); DIFFUSE(COLOR) / ROUGHNESS / NORMAL; ORM paket R=AO G=R B=M;
  normal G ters (DirectX). UE'de UV×0,25. Dünya-Z'ye bağlı ton (su hattı altı) UE'de world position ile.
- FBX: `apply_unit_scale`, `FBX_SCALE_UNITS`, `add_leaf_bones=False`, `use_triangles=True`, `mesh_smooth_type=FACE`;
  her modül ayrı dosya, orijin sokette; export sonrası **temiz sahneye geri yükle** ve ölçek/soket/UCX kontrol et;
  manifestte sha256 + boyut. UE re-import kullanıcı ortamında.

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
