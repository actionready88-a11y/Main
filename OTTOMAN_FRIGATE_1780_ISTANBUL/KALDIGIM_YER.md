# Kaldığım Yer — v038 (2026-09-26)

Branch: `claude/amazing-meitner-keq46t` (repo: actionready88-a11y/Main, klasör: `OTTOMAN_FRIGATE_1780_ISTANBUL/`)

## ► MASAÜSTÜNDE DEVAM (buradan başla)
- **Son sürüm:** `Blender/versions/OTTOMAN_FRIGATE_1780_ISTANBUL_v038.blend` (her pass önceki sürümü açar, yenisini kaydeder;
  var olanın üzerine yazılmaz). Betikler `scripts/pass_vNNN_*.py`; çalıştırma: `python3.11 scripts/pass_vNNN_x.py --no-render`
  (bpy 5.0.1 modülü) ya da yerelde `blender -b --python scripts/pass_vNNN_x.py -- --no-render`.
- **İndirilebilir paket:** `TESLIM/` klasöründe iki zip (GitHub 100 MB sınırı nedeniyle ikiye bölündü):
  `..._1_blend_betik_belge.zip` (son blend, betikler, raporlar, belgeler, Tersane skill) ve `..._2_doku_referans_fbx.zip`.
  İkisini aynı klasöre açınca proje klasörü tamamlanır. (GitHub'da branch → Code → Download ZIP de tüm geçmişi verir.)
- **Blender içi anahtarlar:** `00_CONTROLS/CTRL_YELKEN.yelken_acik` (0 sarılı/1 açık; N paneli "Gemi" sekmesinde buton),
  `00_CONTROLS/CTRL_SUSLEME.susleme_acik` (1 süslemeler açık / 0 sade).
- **Kurallar:** Türkçe çıktı; kaynaksız sayı yok ([BİRİNCİL]/[İKİNCİL]/TAHMİN); Gate A insan onayı; low-poly yasağı ölçülür:
  her pass sonunda `python3.11 ../skills/tersane/scripts/quality_audit.py <blend> --out reports/kalite_testi_vNNN.json`
  (faset = kiriş sapması > 1,5 mm; düz gölge; havada ada). Yuvarlak parça dilimi: `resegment.required_segments(r)`.
- **Sıradaki işler (öncelik sırası):**
  1. Kalan küçük fasetler (v037 sonrası 3 nesne, `reports/kalite_testi_v037.json`): gövde kıç "tuck" (su altı, çoğu ≈ 2 mm,
     en kötü 7 mm; subsurf 3 gövdeyi 2,2 M üçgene çıkarır → bölgesel çözüm gerek), kıç galerisi (2,6 mm; Catmull-Clark
     12,7 mm saptırdığı için geri alındı), filika (1,8 mm).
  2. Bozkurt figürü: v036'da patinalı bronz, yele tek oyma kütle (`scripts/wolf_sdf2.py`; v035 kaynağı `wolf_sdf.py`
     değişmeden duruyor). Kullanıcı onayı bekliyor. Hazır varlık: bulut ortamında Sketchfab/Poly Haven/Free3D/Printables
     ağ politikası nedeniyle kapalı → masaüstünde CC0/CC-BY kurt başı bakılabilir (lisanslı Fab varlığı depoya girmez).
     UE için curvature/AO bake → BC + ORM (malzeme pointiness kullanıyor — UE'de yok).
  3. Top C modülü UV + bake (`Textures/Modules/Cannon_C/`), gövde/modül FBX dışa aktarımı, UE malzemeleri.
  4. Direk çanaklık kenarı sıklaştırma; gövde kıç "tuck" bölgesi; Gate B incelemesi; arma oranlarını Lees ile doğrula.
- **Tuzaklar (kısa):** eski pass üreticilerini yeniden çağırmak konumu kaydırabilir (pass zinciri yamaları) → mesh düzeyinde
  düzelt; `pgrep -f`/`pkill -f` deseni kendi kabuğunu öldürür → PID ile durdur; subsurf viewport = render seviyesi.
  Ayrıntılı ders listesi: `skills/tersane/SKILL.md`.

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
