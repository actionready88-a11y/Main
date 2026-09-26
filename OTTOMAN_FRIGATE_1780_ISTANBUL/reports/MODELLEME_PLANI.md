# Modelleme Planı — Osmanlı Esintili Frigate (demo bölgesi gemisi)

Tarih: 2026-09-25
Durum: **Hull Core v001 üretildi (inceleme taslağı).** Ölçüler Gate A revizyonu için kullanıcı onayı bekliyor.

## 1. Yön değişikliği (kullanıcı kararı, 2026-09-25)

Kullanıcı: *"Kalyon istemiyorum, topları frigate'e göre tekrar düzenle; bu, demo bölgesine yerleştireceğim gemilerden biri olacak (veya brig)."*

- **Çapa artık kalyon değil.** "Beyaz At başlı" kalyonun 41,69 m boyu, 13,64 m eni ve 63 topu (brief §17) bu gemi için **geçersiz**. Brief §17'nin yalnız süsleme kararları (at başı, kırmızı kuşak, fener, sancak) geçerli kalıyor.
- **Tip:** üç direkli, **tek batarya güverteli frigate** ("true frigate"). Topların tamamı üst (batarya) güvertede ve kasaralarda. Alt güvertede top yok.
- **Neden frigate, brig değil:** Referans görsellerin hepsi (kullanıcı konsepti, 5 ChatGPT, 5 Gemini) **üç direkli**. Brig iki direklidir; brig seçilirse arma, gövde boyu ve referans paketinin baştan kurulması gerekir. Brig ayrı bir gemi olarak ileride üretilebilir (bkz. §8).

## 2. Ölçüler (kaynaklı)

Kaynak kuralı: sayfalara doğrudan erişim bu ortamda ağ politikası yüzünden engellendi (Wikipedia, RMG, threedecks, dergipark). Aşağıdaki değerler **web arama özetlerinden** alındı ve **[İKİNCİL, sayfa açılamadı]** diye işaretlendi. Yerelde doğrulanmalı.

| Ölçü | Değer | Kaynak / durum |
|---|---|---|
| Boy (gundeck) | **35,92 m** (117 ft 10 in) | HMS *Lyme* (1748), 28 toplu altıncı sınıf frigate. Wikipedia "HMS Lyme (1748)"; RMG plan kaydı rmgc-object-385550 [İKİNCİL, sayfa açılamadı] |
| En | **10,31 m** (33 ft 10 in) | HMS *Lyme* (1748) [İKİNCİL] |
| Ambar derinliği | 3,00 m (9 ft 10 in) | HMS *Lyme* (1748) [İKİNCİL] |
| Su çekimi | **4,50 m — TAHMİN** | Kaynak yok. Türetilmiş: en × 0,41-0,48 (Vasa/Kronan oranları, brief §17.3) = 4,2-4,9 m; ortası alındı |
| Batarya güvertesi yüksekliği (su hattından) | 1,90 m — TAHMİN | Kaynak yok; ambar derinliği + güverte kalınlığından oranlandı |
| Kasara güverte yüksekliği | batarya güvertesi + 2,0 m — TAHMİN | Kaynak yok |
| Direk yerleri (kıçtan, boyun oranı) | mizana 0,245 · ana 0,54 · pruva 0,815 | `HIBRIT_CHATGPT_03.webp` profilinden ölçüldü (stil referansı, tarihsel değil) |
| Direk boyları | **null** | Kaynak yok; RigSet aşamasında araştırılacak |

**Karşılaştırma analogları:**
- Fransız *Médée* (1741, Brest, Blaise Ollivier): ilk "gerçek frigate" kabul edilir; iki güverteli, yalnız üst güvertede top. 26 × 8 librelik top; gundeck 37,2 m, omurga 31,8 m, en 9,9 m. Wikipedia "French frigate Médée (1741)"; Naval History (USNI) Nisan 2023 "The Evolution of Frigates in the Age of Sail" [İKİNCİL, sayfa açılamadı].
- *Lyme*, ele geçirilen Fransız *Tygre*'nin ölçüleri biraz küçültülmüş kopyasıdır [İKİNCİL].
- **Osmanlı bağlamı:** Osmanlı fırkateynleri üç direkli ve tek ambarlıdır, 30-70 top taşır, boyları ortalama 35,5 zirâ (26,90 m) ile 57,5 zirâ (43,58 m) arasındadır. Osmanlı'da fırkateyn inşası 1770 Çeşme sonrasında, Cezayirli Gazi Hasan Paşa döneminde başladı. Kaynak: Ş. Kocakaplan, "III. Selim Dönemi Fırkateyn İnşa Faaliyetleri", *Istranca Tarih Araştırmaları Dergisi* 2/1 (2024) [İKİNCİL, arama özeti; tam metin açılamadı]. Seçilen 35,92 m bu aralığın içinde.

**Anakronizm notu:** Tek batarya güverteli frigate 1740'lardan sonraki bir tiptir. Osmanlı fırkateyni ise 1770 sonrasına aittir. Gemi hibrit ve tarihsel doğruluk iddiası yok (`historical_accuracy_claim: false`). Eski klasör adındaki "1700" bu tiple uyuşmuyordu. **Kullanıcı kararıyla (2026-09-25) klasör `OTTOMAN_FRIGATE_1780_ISTANBUL` olarak yeniden adlandırıldı.** v001-v003 dosyaları da yeni adla yeniden adlandırıldı (içerikleri aynı).

## 3. Top düzeni (frigate)

| Konum | Sayı | Not |
|---|---|---|
| Batarya güvertesi | **24 (12 / borda)** | *Lyme*: 24 × 9 librelik. Lumbar 0,62 × 0,56 m, eşik güverteden 0,55 m (lumbar ölçüleri TAHMİN) |
| Kıç kasarası | **4 (2 / borda)** | *Lyme*: 4 × 3 librelik |
| Baş kovalama | 2 lumbar | Batarya güvertesinin baş toplarından biri kaydırılarak kullanılır. Ayrı top eklenmez |
| Kıç kovalama | 2 lumbar (kıç aynasında) | Aynı mantık |
| Döner top (swivel) | 12 × ½ librelik — **v001'de yok** | *Lyme* [İKİNCİL]; DeckUtility aşamasında küpeşte soketleri eklenecek |

**Referans görsellerden fark:** Konseptte burunda 3 kovalama topu vardı (kadırga mirası). Frigate düzeninde bu 2 lumbar oldu. İstenirse `CannonBattery` varyantı olarak geri eklenebilir.

## 4. Referans görsellerin kullanım haritası

| Bileşen | Birincil referans | İkincil | Karar |
|---|---|---|---|
| Gövde oranı, sheer, kasaralar | `HIBRIT_CHATGPT_03` (profil) | `HIBRIT_CHATGPT_02` / `04` | Yüksek kıç kasarası, alçak bel, kısa baş kasarası |
| Kıç aynası ve galeri | `HIBRIT_CHATGPT_05` (tam kıç) | `HIBRIT_GEMINI_04` | Kafesli pencereli ölçülü galeri, tek fener → `SternModule` |
| Baş yapısı | `HIBRIT_CHATGPT_02` | `HIBRIT_GEMINI_02` | Yaldızlı kıvrık baş + beyaz at başı figürü → `Figurehead` |
| Boya düzeni | `HIBRIT_GEMINI_02`, `HIBRIT_CHATGPT_03` | kullanıcı konsepti | Katranlı koyu gövde, küpeşte altında kırmızı kuşak, sarı-altın silmeler |
| Arma | `HIBRIT_CHATGPT_03` | `HIBRIT_GEMINI_02` | Kare pruva ve ana, latin mizana, cıvadıra; flok yok |
| Bayrak ve flama | `HIBRIT_GEMINI_02` | — | Yıldızsız kırmızı sancak, çatal uçlu yeşil filandıra; ay-yıldız `FlagSet` varyantında |
| Zırh | kullanıcı konsepti | — | `ArmorProtectionSet`, varsayılan kapalı |

## 5. Blender yapısı (v001'de kurulan)

Denetim özeti (`reports/scene_audit_v001.json`): 186.974 render üçgeni; sınırlar X -19,10…+22,57 m (baş kıvrımı dahil), yarı en 5,19 m, Z -4,50…+6,23 m; su çekimi 4,50 m; eksik UV / malzeme / doku yok; tüm ölçekler 1.

Eksen: X ileri, Z yukarı, su hattı Z = 0, 1 birim = 1 m. Proje standardına uyularak **+Y = sancak** alındı. Blender sağ elli olduğu için bu ayna bir eşlemedir; FBX smoke-test'te Unreal'daki sancak yönü doğrulanmalı.

| Koleksiyon | v001 içeriği |
|---|---|
| `10_HULL_CORE` | `CORE_HULL_SHELL` (süper elips kesitli loft, Subdivision, Solidify 0,24 m, Boolean lumbarlar), omurga, bodoslama, kıç bodoslaması, baş kıvrımı ve rayları, 2 wale, 3 silme şeridi, lumbar çerçeveleri, 3 güverte (batarya, kıç kasarası, baş kasarası) |
| `24_MODULES_DECOR` | `MOD_RUDDER_STERNPOST_A` (dümen; Hull Core'a birleştirilmez) |
| `30_SOCKETS` | 3 direk soketi + `SOCKET_RIG_PRIMARY`, dümen, figür, kıç modülü, 28 top soketi (12+2 / borda), 4 kovalama, 2 çapa, bot, kıç bayrağı, `SOCK_COM`, 16 `SOCK_BUOY_*` |
| `40_COLLISION` | 4 dilimli dışbükey `UCX_CORE_HULL_SHELL_00..03` |

Materyaller şimdilik **prosedürel PBR**: UV'ye bağlı tahta kaplama, ek yerleri, damar ve kir. Dış doku dosyası yok. Gate B öncesi `Textures/` altına BaseColor, DirectX Normal ve ORM olarak bake edilecek.

Üretici betik: `scripts/build_hull_v001.py`. Aynı betik `.blend`, audit JSON ve renderları yeniden üretir.

## 5b. Pass v002: kıç ve omurga bağlantı düzeltmesi (2026-09-25)

Kullanıcı bulgusu (v001 ölçülü pafta): kıçta su hattında dümen gövdeden kopuk görünüyor, başta omurga ile bodoslama arasında açıklık var.

| Bulgu | Kök neden | Düzeltme |
|---|---|---|
| Kıçta boşluk | Kıç bodoslaması 0,03 m'lik ince levha olarak üretilmişti (kesit yönü hatası) ve gövdenin 0,22 m arkasında kalıyordu. Ayrıca Subdivision, gövdenin kıç ve baş kenarlarını içeri çekiyordu | Bodoslama 0,48 m kalınlıkta, gövdeye ve dümene bindirmeli. Gövde kenarlarına crease (kıç, bodoslama, omurga dikişi) |
| Baş omurga açıklığı | Omurga bodoslamadan yaklaşık 0,9 m önce bitiyordu | Omurga bodoslamanın alt ucuna bindirildi, kıçta topuğa kadar uzatıldı |
| Açık renkli bodoslama ve dümen boşluk gibi okunuyordu | Ham meşe malzemesi | Omurga, bodoslama, kıç bodoslaması ve dümen katranlı gövde malzemesinde (su hattı tonu dahil) |
| Kıç altında benek | İki yarının iç yüzeyleri tam çakışıyordu (z-fighting) | Orta hat payı 0,12 → 0,15 m |
| Kırmızı ayna rengi su altına iniyordu | Ayna malzemesi tüm kıç yüzeyindeydi | Ayna alt kenarı (Z_TR = 1,05 m) altı koyu gövde rengi |

Değişen nesneler: `CORE_HULL_SHELL`, `CORE_KEEL`, `CORE_STEM`, `CORE_STERNPOST`, `MOD_RUDDER_STERNPOST_A`, `UCX_CORE_HULL_SHELL_00..03`. Diğer nesneler v001'den aynen alındı. Soket taşınmadı (`reports/scene_audit_v002.json` → `pass`).

## 5c. Pass v003: oyun çarpışması (2026-09-25)

Kullanıcı bulgusu: Blender'da gövde "tel örgü / yırtık" görünüyor. Görünen, gövde değil v001-v002'nin çarpışma parçalarıydı. Sorunları:
- viewport'ta görünür bırakılmışlardı,
- yoğun mesh'in dışbükey kabuğu oldukları için yaklaşık 24 bin ince üçgen içeriyorlardı,
- beli kasaralar arasında kapak gibi örtüyorlardı.

Yeni düzen (`scripts/pass_v003_collision.py`; geometri değişmedi):

| Amaç | Parça | Not |
|---|---|---|
| `hull` | 6 | Omurga altından batarya güvertesine; fizik ve yüzdürme gövdesi |
| `deck_gun` / `deck_quarter` / `deck_forecastle` | 10 / 4 / 2 | Sheer ve kamburluğu izleyen yürüme yüzeyleri |
| `bulwark_port` / `bulwark_starboard` | 14 / 14 | Küpeşte duvarları, düşmeyi engeller |

- Toplam 50 UCX, parça başına en fazla 36 köşe (sınır 64), toplam 976 üçgen. Bel açık.
- `40_COLLISION` ve `CUT_GUNPORTS` viewport'ta varsayılan gizli.
- Önizleme: `renders/v003/*collision*.png`
- Eksik: bel ile kasaralar arası merdiven ve rampa çarpışması (merdivenler modellenince eklenecek).

## 5d. Fab "Age of Sail" referansından çıkarımlar (`reports/reference_audit/age_of_sail/`)

| Konu | Fab gemisi | Bize etkisi |
|---|---|---|
| Gövde bölünmesi | `Hull` koleksiyonu 14 nesne, yaklaşık 79 bin üçgen: `HullBelow` 2,9 bin, `SidesWalls` 6,5 bin, `SidesPlanks`, `SidesDecoration`, `gunportEdges`, `Keel`, `Deck` 26 bin, `Structure` 35 bin, `InternalWalls` | Dış kabuk hafif, detay dokuda. Bizim `CORE_HULL_SHELL` render seviyesinde 139 bin üçgen; **oyun LOD0 için alt seviye + bake edilmiş normal** gerekli |
| Modifier düzeni | Mirror + Solidify + "Auto Smooth" (geometry nodes) | Bizde ayna yarımı elle üretiliyor. Export öncesi aynı sonucu verir; ek iş gerekmiyor |
| Doku | 45 doku, çoğu 2K-3K; albedo, roughness ve normal ayrı; bir parçada DirectX normal | Hedefimiz (BaseColor + DX Normal + ORM, 2K-4K) ile uyumlu. Prosedürel materyaller bu çözünürlükte bake edilecek |
| Arma | 1.541 nesne, yaklaşık 2,1 milyon üçgen; halatlar tek tek 24-28 bin üçgen | Oyun için fazla. Bizde halatlar kart/instanced mesh ve LOD ile, uzak mesafede sade |
| Yelken | 400 nesne, 325 bin üçgen; kenar maskesi ve transmission dokuları | SailSkin ve SailSet'te transmission ve kenar maskesi kullanılacak |
| Uyarı | Tarihsel kaynak değil; lisanslı, repoya girmez | Yalnız kalite kıyası |

## 5e. Pass v004: oynanış soketleri (2026-09-25)

`scripts/pass_v004_gameplay_sockets.py` (geometri değişmedi):
- **Mahmuz:** `SOCKET_RAM` pruvada, su hattının 0,35 m altında (oynanış modülü `MOD_RAM_*`; tarihsel değil).
- **Komuta:** `SOCKET_HELM`, `SOCK_STATION_CAPTAIN`, `SOCK_STATION_SECOND_CAPTAIN`, `SOCK_STATION_GUNNERY_OFFICER`. Komuta zinciri: oyuncu → 2. kaptan → topçu subayı.
- **Mürettebat:** 32 top soketinin her birine 4 nokta, toplam 128 `SOCK_CREW_*`. Roller: nişancı, doldurucu, tokmakçı-süngerci, manivela. Tüm noktaların güverte içinde kaldığı doğrulandı.
- **Top soketi özellikleri:** `battery_group` (`PORT_MAIN` 12, `STARBOARD_MAIN` 12, `PORT_QD` 2, `STARBOARD_QD` 2, `CHASE_BOW` 2, `CHASE_STERN` 2), `slot`, `mount_id` (UUID5), `manifest_version = 2`.
- **Düzeltme:** v001-v003'te 28 borda top soketi gemi içine bakıyordu. Sancak topları +Y, iskele topları -Y yönüne çevrildi; manifest sürümü 1'den 2'ye çıktı.
- Önizleme: `renders/v004/*soketler*.png`

## 5f. Pass v005: yüksek kıç, merdivenler, dümen, kıç galerisi (2026-09-26)

Kullanıcı isteği (görsel referansla): kıç normalden yüksek, merdivenle çıkılan bir alan olsun ve orada şimdilik dümen dursun. `scripts/pass_v005_stern.py`:

| Öğe | Değer | Not |
|---|---|---|
| Kıç üstü güverte (poop) | Kıç kasarası güvertesinin 2,0 m üstünde; ön bölme x = -13,90 m; güverte boyu 5,24 m | Oynanış ve stil; 18. yy frigate'inde tipik değil (hibrit) |
| Kaptan kamarası | Poop altında; net tavan (orta hat, ön) 1,88 m; kapı 0,90 × 1,85 m | Gezilebilir iç mekân |
| Merdivenler | İki adet, kapının iki yanında (\|y\| 0,85-1,75 m); 10 basamak, basamak yüksekliği 21,6 cm, eğim 42° | UE varsayılan yürünebilir açı 44,76° altında. İki yanda tırabzan |
| Korkuluk | Torna balüsterler (0,70 m) 0,30 m dolu küpeşte üstünde; yanlar, kıç ve ön kenar | Ön kenarda merdiven boşlukları |
| Kıç aynası | 5 kafesli pencere (gerçek açıklık: `CUT_STERN_WINDOWS`), pilastr, eşik ve korniş | `MOD_STERN_GALLERY_A` (SternModule) |
| Yan galeriler | İki yanda 3'er kafesli pencere, saçaklı çatı, altın topuzlu sarkıt | SternModule içinde |
| Tepelik ve fener | Kemerli pano + güneş motifi (§17.4 kararı); üstünde altıgen kıç feneri, tepe yüksekliği 9,51 m | `MOD_LANTERN_STERN_A` (LanternFlagSet), `SOCKET_LANTERN_STERN` |
| Dümen | Tamburlu dümen dolabı, 10 parmaklı dümen (Ø ~1,6 m tutamaklarla), A-ayaklar, dümenci ızgarası | `MOD_HELM_WHEEL_A`, `SOCKET_HELM`; kaptan istasyonu dümenin arkasında |
| Kıç kasarası topları | x = -12,6 / -10,2 → **-10,3 / -7,9** | Merdivenlere yer açmak için; lumbarlar da taşındı |

Gövde kabuğu yeniden üretildi, çünkü üst kenar kıçta 1,2 m yükseldi. Kesit formülü eski üst kenarın altında birebir aynı. Ayrıca kırmızı kuşak sınırına denk gelen bir satır eklendi (`row_z`); kıçta testere dişi görünen malzeme sınırı artık düz.

Soketler (manifest 3):
- **Taşınan:** `SOCKET_HELM`, `SOCK_STATION_CAPTAIN` (poop), `SOCK_STATION_SECOND_CAPTAIN` (kıç kasarası ön kenarı, orta hat), `SOCKET_FLAG_STERN`, kıç kasarası top soketleri ve mürettebatları.
- **Eklenen:** `SOCKET_LANTERN_STERN`, `SOCK_NAVLINK_POOP_STAIR_{P,S}_{BOTTOM,TOP}`, `SOCK_NAVLINK_CABIN_DOOR_{OUT,IN}`.

Çarpışma: 68 UCX. Yeni amaçlar: `deck_poop` (2), `transom` (1), `bulkhead` (3), `stairs` (2 rampa), `rail_poop` (10). Önceki sürümlerde kıç aynası duvarı çarpışması yoktu; eklendi.

## 5g. Pass v006: merdivenler köşelere (2026-09-26)

Kullanıcı geri bildirimi: "Şu an ikisi de ortada gibi duruyor; biri sağ, biri sol köşede duracak."

`scripts/pass_v006_stairs_corners.py` (gövde kabuğu değişmedi):
- **Merdivenler:** Kapının yanından borda duvarına yaslı köşelere taşındı: sancak \|y\| 2,20-3,10 m, iskele simetriği. Dış kenar, iç borda yüzünün en dar yerinden 5 cm içeride. 10 basamak, eğim 41,8°.
- **Ön korkuluk:** Kapının üstünde tek orta parça; köşeler merdiven boşluğu.
- **Kıç kasarası topları:** Merdiven ayağı ile mürettebat arasında pay kalsın diye ileri alındı: x = -10,3 / -7,9 → **-10,0 / -7,7**. Lumbar kesicisi yerinde güncellendi, gövdedeki boolean bağı korundu. Mürettebat noktası ile merdiven çakışması yok (audit: `stairs.crew_conflicts = []`).
- **Soketler (manifest 4):** 4 top soketi, 16 mürettebat noktası ve 4 merdiven navlink'i taşındı.
- **Çarpışma:** 66 UCX (ön korkulukta 3 yerine 1 parça).

## 5h. Pass v007: oyun ölçeği ×1,10 (2026-09-26)

Kullanıcı izni: "Bunlar sıkıntılı oluyorsa hafiften gemiyi büyütebilirsin."
- **Sorun:** Kıç kasarası altı, baş kasarası altı ve kaptan kamarasının net tavanı 1,88-1,90 m'ydi. UE varsayılan karakter kapsülü 1,76 m.
- **Çözüm:** `scripts/pass_v007_scale.py` tüm sahneyi orijine göre eşit oranda 1,10 ölçekledi. Su hattı Z=0 korundu. Ölçek mesh'e uygulandı, nesne ölçeği 1 kaldı. UV'ler de aynı oranla çarpıldı, tahta genişliği değişmedi. Kaplama (0,24 m) ve güverte (0,10 m) kalınlıkları gerçek değerde bırakıldı.
- **Sonuç (audit v007, geometriden):**

| Yer | Net tavan |
|---|---|
| Kıç kasarası altı | 2,06 m |
| Baş kasarası altı | 2,01 m |
| Kaptan kamarası | 2,01 m |

- **Yeni ana ölçüler:**

| Ölçü | Değer |
|---|---|
| Güverte boyu | 39,51 m |
| En | 11,34 m |
| Su çekimi | 4,95 m (tahmin) |
| Toplam boy | 46,6 m |
| Fener tepesi | 10,46 m |

  Osmanlı fırkateyn aralığı (26,90-43,58 m) içinde kalıyor.
- Merdiven eğimi (41,8°), top aralıkları ve oranlar değişmedi. Soket konumları ölçeklendi (manifest 5).
- **Sonraki pass'ler için:** Tasarım fonksiyonları (`build_hull_v001.py`) Lyme ölçeğinde kalıyor. Dünya koordinatı için `scripts/ship_scale.py` sarmalayıcısı kullanılacak (uzunluk × 1,10). Sahnede `ship_scale = 1.10` özelliği var; `annotate_views.py` bunu okuyor.

## 5i. Pass v008: bel → kasara merdivenleri (2026-09-26)

Kullanıcı kararı: "Her yer gezilebilir" için önce ana güverteden kıç kasarasına ve baş kasarasına çıkan merdivenler. `scripts/pass_v008_access_stairs.py` (gövde kabuğu değişmedi; geometri tasarım uzayında kurulup ×1,10 ile yerleştirildi):

| Merdiven | Yer (dünya) | Eğim / basamak yüksekliği | Neden bu yer |
|---|---|---|---|
| Kıç kasarası (2) | Kasara ön kenarı, orta hattın iki yanı (\|y\| 0,39-1,38 m), kıça doğru yükselir | 40,5° / 22,6 cm | Bordalarda batarya topları ve mürettebatı var |
| Baş kasarası (2) | Kasara arka kenarı, ön direğin iki yanı (\|y\| 0,50-1,49 m), başa doğru yükselir | 41,6° / 23,4 cm | Ön direk orta hatta, iki merdivenin arasında (0,99 m boşluk) |

- **12. top çifti** baş kasarası altına alındı: tasarımda x = 12,6 → **14,25** (dünyada 13,86 → 15,68). Lumbar kesicisi ve çerçeveler yeniden üretildi, soketler ve mürettebat taşındı. Top sayısı değişmedi (24 + 4). Pruva dar olduğu için bu çiftin nişancıları orta hatta 0,46 m arayla duruyor.
- **Ön korkuluklar:** İki kasaranın ön korkuluğu kıç üstü stiline çevrildi (kaide + torna balüster + alın kirişi). Merdiven başlarında boşluk var.
- **Soket ve çarpışma:** 8 navlink (`SOCK_NAVLINK_{QD,FC}_STAIR_{S,P}_{BOTTOM,TOP}`), 10 yeni UCX (4 merdiven rampası, 6 korkuluk).
- **Kontrol:** Merdiven ayak izi ile mürettebat noktası çakışması yok. Kontrol, merdivenin alt yüzü baş hizasının üstündeyse o noktayı çakışma saymıyor.
- **Erişim zinciri:** bel → kıç kasarası → kıç üstü ve bel → baş kasarası. Açık güvertelerin tamamına merdivenle çıkılabiliyor.

## 5j. Pass v009: baş kasarası merdivenleri köşelere (2026-09-26)

Kullanıcı isteği (görselle): baş kasarası merdivenleri, kıç üstündekiler gibi sağ ve sol köşede, borda duvarına yaslı olsun. `scripts/pass_v009_fc_stairs_corners.py`:
- **Merdivenler:** \|y\| 2,62-3,61 m (dünya), eğim 41,4°. Ön korkuluk ortada tek parça.
- **Ana batarya:** 1-11. toplar x = -13,4 … 9,55 (tasarım) aralığına eşit dizildi. Top aralığı 2,36 m'den 2,30 m'ye indi, 11. top 0,69 m geri geldi. 12. top baş kasarası altında kaldı. Toplam 20 top soketi ve mürettebatı taşındı, lumbar kesicisi ve çerçeveler yenilendi.
- **Kontrol:** Dört erişim merdiveninin hiçbirinde mürettebat çakışması yok. Çarpışmada eski baş kasarası merdiven ve korkuluk UCX'leri kaldırıldı, yenileri eklendi; UCX adları sıralı yeniden düzenlendi.

## 5k. Pass v010: kıç kasarası altında kaptan kamarası (2026-09-26)

Kullanıcı kararı: "Kıç kasarası altını kapat". Ortadaki merdivenler kalktı. Kıç kasarası altındaki açık alan ön duvarla kapatılıp kaptan kamarası oldu. `scripts/pass_v010_great_cabin.py` (gövde kabuğu değişmedi):

| Öğe | Değer (dünya) |
|---|---|
| Ön duvar | x = -6,22 m; kıç kasarası kenarının altında, kıç üstü bölmesiyle aynı stil (kırmızı panel, sarı pervaz) |
| Kapı | 0,99 × 2,04 m, orta hatta |
| Kamara | Ön duvardan kıç aynasına yaklaşık 14 m; net tavan 2,06 m; içinde 1-4. top çiftleri ve kıç kovalama lumbarları |
| Kıç kasarası merdivenleri | Duvar boyunca enlemesine: kapının yanından (\|y\| 0,68 m) köşelere (\|y\| 2,99 m) yükselir; eğim 43,2° (UE sınırı 44,76°) |
| Ön korkuluk | Orta parça + köşelerde merdiven başı boşluğu |

- **Ana batarya yeniden dizildi:** 1-4. toplar x = -13,4 … -6,9, 5-11. toplar -3,55 … 9,55 (tasarım); 12. top baş kasarası altında. Bu dizilişle 4. topun ön mürettebatı duvarın arkasında, 5. topun arka mürettebatı merdivenin önünde kalıyor. Dört erişim merdiveninin hiçbirinde mürettebat çakışması yok.
- **Soket ve çarpışma:** `SOCK_NAVLINK_GREAT_CABIN_DOOR_{OUT,IN}`, kıç kasarası merdiven navlink'leri güncellendi. Eski kıç kasarası merdiven ve korkuluk UCX'leri kaldırıldı; yeni merdiven, korkuluk ve duvar UCX'leri (`bulkhead_great_cabin`) eklendi.
- **Eksik:** Kamara içi boş; mobilya, bölmeler ve aydınlatma yok. Bir sonraki iç mekân pass'inde yapılacak.

## 5l. Pass v011: kıç kasarası kaldırıldı, kıç üstü ve kaptan kamarası ana güverteye indi (2026-09-26)

Kullanıcı kararı: "Kamara, dümenin altındaki kapılı kısımda olacak; ekstra kaptan kamarası yok. Kıç kasarası altında açık alan kalmayacak; orayı düzle, bu kısmı aşağı taşı, eski kapıyı kapat, merdivenleri aşağı uzat; ek platform olmayacak." Seçenek 1 + "kamara yüksekliği artırılabilir". `scripts/pass_v011_lower_stern.py`:

| Öğe | Değer (dünya) |
|---|---|
| Kıç kasarası | Kaldırıldı: güverte, ön korkuluk, merdivenler, v010 duvarı. Bölge düz ana güverte; borda üst kenarı bel yüksekliğinde |
| Kıç üstü güverte | Ana güvertenin **2,64 m** üstünde (tasarım 2,40); dümen, korkuluk, tepelik ve fener onunla indi |
| Kaptan kamarası | Kıç üstü altında, ana güverte seviyesinde; **net tavan 2,50 m**; kapı belden girilen ön duvarda; 5 kafesli kıç penceresi |
| Merdivenler | Köşelerde, ana güverteden doğrudan kıç üstüne; 11 basamak, 25,6 cm, eğim 43,5° (UE sınırı 44,76°) |
| Toplar | Kıç kasarasının 4 hafif topu kaldırıldı. Ana batarya bordada 11: 10 belde (x = -10,05 … 9,55 tasarım) + 1 baş kasarası altında. 2 baş ve 2 kıç kovalama; kıç kovalamaları kamara pencerelerinden (y = ±2,09 m dünya) ateşler, aynadaki eski kovalama lumbarları kapatıldı |

- Gövde kabuğu, kuşaklar, silmeler ve batarya güvertesi yeni kıç profiline göre yeniden üretildi. Su hattı altı ve baş kasarası aynı kaldı.
- 36 soket silindi (kıç kasarası topları ve mürettebatı, 12. top soketleri, eski navlink'ler). Top ve istasyon soketleri taşındı (manifest 9).
- Çarpışma yeni profille yeniden kuruldu; baş kasarası merdiven ve korkuluk UCX'leri korundu.

## 5m. Pass v012: 20 + 4 top (2026-09-26)

Kullanıcı kararı: "Toplam top sayısını 20'ye indir; oyunda yükseltme ile alt güverteye ekstra toplar eklenebilir." Netleştirme: **20 + 4**.
- **Toplar:** 20 borda topu (bordada 10, üst güvertede, belde; x = -11,06 … 10,50 m dünya) + 2 baş kovalama + 2 kıç kovalama (kamara pencerelerinden). Baş kasarası altındaki sıkışık top çifti kaldırıldı.
- `scripts/pass_v012_guns20.py`: lumbar kesicisi yerinde yenilendi, çerçeveler yeniden üretildi, 10 soket (top + mürettebat) silindi. Gövde değişmedi (manifest 10).
- **Alt güverte yükseltmesi (plan):** Mevcut gövdede alt güverte lumbarları su hattının altında kalıyor. Yükseltme, bordası ~2,2 m yüksek ayrı bir Hull varyantı olarak yapılmalı (`MODULAR_SHIP_STANDARD`: yapısal gövde değişimi yeni hull sınıfıdır). Ayrı pass ve onay gerekiyor. → v013'te yapıldı (§5n).


## 5n. Pass v013: Hull_B, alt top güverteli gövde (2026-09-26)

Kullanıcı kararları: (1) gemi baştan Hull_B olarak kurulur, alt lumbarlar kapalı gelir, yükseltme kapakları açıp topları takar; (2) gemi aynı yükseklikte kalır; (3) güverteler arası 2,2 m; (4) alt güverte su hattının altına düştüğü için **gemi suda yükselir**.
- **Su hattı:** gövde geometrisi değişmedi; bütün gemi +1,00 m taşındı (su hattı Z=0 standardı korunur). Su çekimi 4,95 → **3,95 m**. Gemi sudan 1 m daha yüksek görünür.
- **Seviyeler (dünya, su hattından):** alt güverte 0,89 m (orta kesit), üst güverte 3,09 m. Alt lumbar eşiği en düşük 1,50 m. Kiriş altı net 1,89 m.
- **Alt batarya:** bordada 10 lumbar, üsttekilerin arasına şaşırtmalı (x = -9,86 … 11,70 m). Kesici `CUT_GUNPORTS_LOWER`, çerçeveler `CORE_GUNPORT_FRAMES_LOWER`, lumbarların altında yeni kuşak `CORE_WALE_LOWER_TIER`.
- **Lumbar kapakları:** `MOD_PORT_LID_LOWER_{S,P}_{01-10}` (20 adet, tek paylaşılan mesh). Orijin menteşede; yerel X etrafında +80° açılır. Varsayılan durum kapalı. Soket `SOCKET_PORT_LID_*`.
- **Soketler:** `SOCKET_CANNON_LOWER_*` (20, `default_enabled = false`, `upgrade = lower_deck_battery`), `SOCK_CREW_LOWER_*` (80), `SOCK_STATION_LOWER_BATTERY_OFFICER` (komuta zinciri oyuncu → 2. kaptan → topçu subayı → alt batarya subayı).
- **Ambar ağızları:** kıç ve baş ambar ağzı (merdivenli, 54-55°, basamak yüksekliği 0,24-0,25 m), ana ambar ağzı ızgaralı (üstünde yürünür). Üst güvertede delikler boolean ile açıldı (`CUT_HATCHES`). Kirişler `CORE_DECK_BEAMS_UPPER` ambar ağızlarında kesilir.
- **Subay bölmesi (gunroom):** alt güverte kıçında, ön yüzü x = -11,55 m; kapı 0,94 × 1,81 m. 2 duvar feneri içeride, 6 fener borda duvarlarında (`MOD_LANTERN_WALL_A_*`, `SOCK_LANTERN_LOWER_*`).
- **Çarpışma:** eski dolu "hull" dilimleri (üst güverteye kadar) ve delik açılmamış üst güverte dilimleri kaldırıldı. Yerlerine ambar altı dolu dilimler, iki güverte arası borda duvarları, delikli üst güverte, alt güverte, ambar koamingleri/ızgarası, merdiven rampaları ve bölme duvarı geldi. Toplam 126 UCX.
- **Parça sayısı (Hull Core):** 33 parça + 4 kesici. Gövde grubu 14, güverte grubu 19.
- **Denetim:** mürettebat güverte dışında 0, merdiven/bölme çakışması 0. Ambar ağzı–direk mesafesi en az 2,4 m.

## 5o. Pass v014: 9 librelik top modülü (2026-09-26)

- `MOD_CANNON_9PDR_A`: kızak (truck carriage, 1.912 üçgen) ve namlu (2.172 üçgen) ayrı mesh. Namlu kızağın çocuğu, pivotu muylu ekseninde (yükseliş). Kızak soket orijininde; yerel +X namlu yönü.
- **Ölçüler:** namlu çapı 0,107 m (4,2 inç) [İKİNCİL: IMA, arama özeti]. Namlu boyu 2,44 m, muylu yüksekliği 0,86 m, kızak boyu 1,30 m, teker yarıçapı 0,21/0,19 m: TAHMİN (lumbar merkezine göre).
- 24 top takıldı (20 borda + 4 kovalama). Alt güverte soketleri boş (yükseltme; `module_family_accepts = MOD_CANNON_9PDR_A`).
- Mesh soketleri: `SOCKET_GUN_MUZZLE`, `SOCKET_GUN_TOUCHHOLE` (ana örnek S_01 namlusunda).
- **Soket düzeltmesi:** v004'ten beri top ve mürettebat soketleri güvertenin orta hat yüksekliğindeydi. Kamburluk ve sheer yüzünden bazıları güvertenin 0,1 m altında, kovalama mürettebatı 0,3 m üstündeydi. 216 soket güverte yüzeyine oturtuldu (manifest 12).
- Namlu ağzı lumbardan 0,37 m dışarıda (yerel x = 1,69). Kızakla çakışan mürettebat noktası yok.

## 5p. Pass v015: RigSet — direkler, serenler, sabit arma (2026-09-26)

Kaynak durumu: Lees (*Masting and Rigging of English Ships of War*) ve benzeri tablolar bu ortamda açılamadı. Bu yüzden oranlar **TAHMİN** (dönem kuralları) olarak kullanıldı ve Lees ile doğrulanmalı.
- **Direkler (dünya):** alt direk boyları pruva 22,60, ana 25,43, mizana 21,87 m (ana = (güverte boyu + en)/2; pruva 8/9; mizana 0,86). Çap yarda başına 1 inç (ana 0,71 m). Gabya 0,6 × alt direk (mizana 0,55), babafingo 0,5 × gabya. Yatıklık 0 / 1,5 / 3°. Ana direk topuzu su hattından 39,8 m.
- **Çanaklıklar:** D biçimli platform, lubber deliği, kıç korkuluğu; gabya kıstakları. Ana çanaklık eni 5,09 m.
- **Serenler:** 9 seren (alt, gabya, babafingo × 3 direk) + mizana gaf ve bumba. Ana alt seren 22,13 m. Her seren ayrı nesne; pivot askıda, direk ekseni etrafında brasya (sınır 35°, TAHMİN). Altlarında basamak halatı (footrope) ve üzengiler var (AC tarzı seren yürüyüşü).
- **Cıvadıra:** 15,26 m, eğim 25° (TAHMİN), üstünde flok bumbası; pruva başının hemen üstünden geçer.
- **Sabit arma:** kuşak tahtaları (channels), bigotalar ve savlolar, zincir levhaları. Çarmıh sayısı bordada 9/9/5 (TAHMİN). Alt çarmıhlarda ve gabya çarmıhlarında iskalarya (0,40 m aralık), futtock çarmıhları, babafingo çarmıhları, patrisalar, 8 istralya.
- **Tırmanma:** 12 tırmanma rotası (`SOCK_CLIMB_{MAST}_{S,P}_{LOWER,TOPMAST}_{BOTTOM,TOP}`), `climb_shrouds` UCX'leri. Çanaklık ve kıstaklar yürünür. Direkler, serenler ve cıvadıra için UCX var; lubber deliği çarpışmada kapalı (tırmanış futtock çarmıhlarından). Seren uçlarında `SOCK_YARDARM_*`, SailSet için `sail_slot` özellikleri.
- **Filika soketi:** v001'den beri ana direkle çakışıyordu. Ana ve pruva direkleri arasına alındı. Kızaklar güverteden 2,2 m yüksekte: altından yürünür ve baş ambar merdiveni açık kalır.
- Arma toplamı 65 bin üçgen. Yelken ve hareketli arma (halat, makara) yok.

## 5q. Pass v016: Kaptan kamarası içi (2026-09-26)

- Eşyalar ayrı modüller (`InteriorSet`, orijin zeminde, `SOCK_INTERIOR_*`): harita masası (açık ve dürülmüş haritalar, pergel), 4 sandalye, yazı masası (çekmeceli, seyir defteri, hokka) ve sandalyesi, asma yatak (cot), altında sandık, büfe (sürahi, kadehler), kıç pencere sediri (dolaplı, minderli), asma pirinç fener.
- Yerleşim kıç kovalama toplarının mürettebat noktalarını boş bırakır (denetim: 0 çakışma, oda dışına taşan yok). Masada net tavan 2,49 m.
- **Güverte boşluğu düzeltmesi:** üst güverte kıç aynasından 0,59 m, alt güverte 0,24 m önde bitiyordu (v011/v013'ten kalma açıklık). İki güverte de aynaya uzatıldı, dolgu UCX'leri eklendi.
- Mobilya ölçüleri TAHMİN. Mobilya için tarihsel kaynak kullanılmadı.

## 5r. Pass v017: filika, çapalar, ırgat (2026-09-26)

Plan §6 madde 5 (BoatSet, AnchorSet) ve güverte donanımı (ırgat). Ölçüler TAHMİN.
- **Filika** `MOD_BOAT_CUTTER_A` (7,0 × 2,0 × 0,78 m): bindirme kaplama görünümlü kabuk, küpeşte, omurga, oturaklar, kıç oturağı, 4 kürek. Soketinde (`SOCKET_BOAT_PRIMARY`), ana ve pruva direkleri arasındaki kızakların üstünde duruyor. Filikanın altı güverteden 2,07 m yukarıda; baş ambar merdiveninin çıkışı filikanın altında açık.
- **Kızaklar** `CORE_BOAT_SKIDS`: iki enine kiriş, dört dikme, beşik takozları. Dikmeler |y| = 1,2 m'de, top mürettebatının iç tarafında.
- **Çapalar** `MOD_ANCHOR_BOWER_{STARBOARD,PORT}` (gövde 3,6 m, kollar 2,3 m, ahşap çipo 3,4 m, demir çemberli): kedi başlarından asılı (`state_default = catted`). Çipo baş-kıç doğrultusunda. Dışa açıklık, çapanın her noktası gövdeden ≥ 0,15 m dışarıda kalacak biçimde hesaplandı (1,2 m).
- **Kedi başları** `CORE_CATHEADS`: baş kasarası küpeştesinden dışa uzanan kalaslar.
- **Irgat** `MOD_CAPSTAN_A`: taban, kastanyola çemberi, 8 kamlı gövde, 10 manivela yuvalı başlık. Konum x = -4,10 m (ana ambar ızgarası ile kıç ambar ağzı arası, orta hat). Manivelalar takılı değil. 10 itici noktası (`SOCK_CREW_CAPSTAN_*`) yalnız demir alırken kullanılır (`exclusive_with = battery_manned`). 0,9 m içinde top mürettebatı yok.
- UCX: filika, ırgat, kedi başları, 2 çapa, 2 kızak.

## 5s. Pass v018: batarya ve güverte ayrıntıları (2026-09-26)

Ölçüler TAHMİN.
- **Asma dirsekler** `CORE_KNEES_LOWER_DECK`: alt güvertede kiriş uçlarında, iki bordada 32 dirsek (16 kiriş). Lumbar, fener ve subay bölmesiyle çakışan 7 kiriş atlandı. Dirseklerin yatay kolu kiriş altında kalır, mürettebatın başının üstündedir.
- **Halka cıvataları** `CORE_RING_BOLTS`: her top soketinin iki yanında, iç bordada (üst ve alt güverte, 80 adet).
- **Brok halatları** `MOD_CANNON_BREECHING_{S,P}_A`: üst güvertedeki 20 borda topunda, kaskabelden iki halka cıvatasına sarkık halat. Oyunda geri tepme için UE kablosuyla değiştirilebilir.
- **Gülle rafları** `CORE_SHOT_RACKS`: üst güvertede toplar arasında 18 raf, her birinde 10 gülle (çap 0,10 m, namlu çapına göre).
- **Tulumbalar** `MOD_PUMP_ELM_A_{S,P}`: ana direğin kıçında (x = 0,55, y = ±0,85 m), `SOCKET_PUMP_*` ve `SOCK_CREW_PUMP_*`. Top mürettebatına en yakın mesafe 1,05 m.

## 5t. Pass v019: kalite denetimi düzeltmeleri (2026-09-26)

Geometri değişmedi.
- `UCX_MOD_BOAT_CUTTER_A_00` 294 köşeliydi (sınır 64). Filika kabuğundan seyreltilmiş örneklerle 36 köşe olarak yeniden kuruldu.
- v015 tırmanma UCX'leri rota adıyla adlandırılmıştı. UE kuralı `UCX_<RenderMesh>_NN` olduğu için `UCX_MOD_RIG_STANDING_{MAST}_A_NN` yapıldı; rota adı `climb_route` özelliğinde.
- Son durum: 193 UCX, en fazla 58 köşe; sahibi olmayan UCX ve ad kuralını bozan UCX yok. 382 soketin hepsinde `manifest_version` var.

## 6. Sıradaki adımlar

**Kurallar:** `reports/URETIM_GEREKSINIMLERI.md`: UE 5.8, fotogerçekçi ve game-ready, modüler yapı, yürünebilir güverte, versiyonlu kayıt, her pass sonunda render ve audit. v002'den itibaren her pass önceki `.blend` üzerinde çalışır; tüm gemi baştan kurulmaz.


1. **Kullanıcı incelemesi:** v001 renderları (`renders/v001/`) ve ölçüler (§2). Gate A revizyonu: ONAYLA / DEĞİŞTİR.
2. **v002 gövde incelikleri + oynanış altyapısı:** kasara yüksekliği kararı, yürüme çarpışması (`UCX_DECK_*`), merdivenler, mürettebat ve komuta soketleri, kıç aynası ve galeri (`SternModule`), baş kasarası küpeştesi, lumbar kapakları, iç postalar ve güverte kirişleri, ırgat, ambar ağızları, merdivenler, bocurum/zincir tahtaları (chain wales).
3. **RigSet:** direk ve seren boyları için kaynak araştırması (Steel ya da Lavery oranları); cıvadıra dahil üç direk.
4. **CannonBattery:** 9 librelik ve 3 librelik top + ahşap kızak; 28 soket.
5. **SailSet ve SailSkin**, **LanternFlagSet**, **Figurehead** (at başı), **BoatSet**, **AnchorSet**.
6. **UV/PBR bake**, LOD zinciri, UCX sadeleştirme (her parça ≤ 32 köşe hedefi), Gate B, FBX paket.

## 7. Bilinen sınırlamalar (v001)

- Kıç aynası düz bir kapak; galeri ve pencereler yok. (Kıç altı artefaktı v002'de giderildi.)
- Baş kıvrımı (knee of the head) ve yan rayları gövdeye bağlanmıyor, havada duruyor. v002'de baş platformu ve grating ile yeniden kurulacak.
- Gövde silüeti hâlâ dolgun: alt gövde uçlarda yükselmiyor (deadwood yok). Hat planı (lines plan) kaynağı bulununca kesitler güncellenecek.
- Lumbar kapakları, iç yapı, merdiven ve güverte donanımı yok.
- Dümen basit profil; iğne ve dişi menteşeler yok.
- UCX parçaları yüksek köşe sayılı (convex hull). Unreal için sadeleştirilecek.
- Materyaller prosedürel. Dış doku dosyası ve bake edilmiş harita yok.
- `computer_use` görsel doğrulaması yapılmadı (bu oturumda yok). Renderlar gözle incelendi.

## 8. Brig alternatifi (ayrı gemi olarak)

Katalog: "Brig esas olarak 18. yy için güvenlidir" (`_context/GEMI_SINIFLARI_URETIM_KATALOGU.md`, #30). İki direkli ve kare armalı olur. Bu frigate'in malzeme kütüphanesini, top modüllerini ve soket şemasını yeniden kullanabilir. Kendi Gate A araştırması gerekir: ölçü, arma ve en az üç kaynak.
