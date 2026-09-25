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

**Anakronizm notu:** Tek batarya güverteli frigate 1740'lardan sonraki bir tiptir. Osmanlı fırkateyni ise 1770 sonrasına aittir. Klasör adındaki "1700" bu tiple uyuşmuyor. Gemi hibrit ve tarihsel doğruluk iddiası yok (`historical_accuracy_claim: false`). Yine de ad değişikliği önerisi: `OTTOMAN_FRIGATE_1780_ISTANBUL`. Yeniden adlandırma yapılmadı; karar kullanıcıda.

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

## 6. Sıradaki adımlar

1. **Kullanıcı incelemesi:** v001 renderları (`renders/v001/`) ve ölçüler (§2). Gate A revizyonu: ONAYLA / DEĞİŞTİR.
2. **v002 gövde incelikleri:** kıç aynası ve galeri (`SternModule`), baş kasarası küpeştesi, lumbar kapakları, iç postalar ve güverte kirişleri, ırgat, ambar ağızları, merdivenler, bocurum/zincir tahtaları (chain wales).
3. **RigSet:** direk ve seren boyları için kaynak araştırması (Steel ya da Lavery oranları); cıvadıra dahil üç direk.
4. **CannonBattery:** 9 librelik ve 3 librelik top + ahşap kızak; 28 soket.
5. **SailSet ve SailSkin**, **LanternFlagSet**, **Figurehead** (at başı), **BoatSet**, **AnchorSet**.
6. **UV/PBR bake**, LOD zinciri, UCX sadeleştirme (her parça ≤ 32 köşe hedefi), Gate B, FBX paket.

## 7. Bilinen sınırlamalar (v001)

- Kıç aynası düz bir kapak; galeri ve pencereler yok. Kıç bodoslamasının alt ucunda küçük bir gölgelendirme artefaktı var (ayna şeridi ile bodoslama birleşimi).
- Baş kıvrımı (knee of the head) ve yan rayları gövdeye bağlanmıyor, havada duruyor. v002'de baş platformu ve grating ile yeniden kurulacak.
- Gövde silüeti hâlâ dolgun: alt gövde uçlarda yükselmiyor (deadwood yok). Hat planı (lines plan) kaynağı bulununca kesitler güncellenecek.
- Lumbar kapakları, iç yapı, merdiven ve güverte donanımı yok.
- Dümen basit profil; iğne ve dişi menteşeler yok.
- UCX parçaları yüksek köşe sayılı (convex hull). Unreal için sadeleştirilecek.
- Materyaller prosedürel. Dış doku dosyası ve bake edilmiş harita yok.
- `computer_use` görsel doğrulaması yapılmadı (bu oturumda yok). Renderlar gözle incelendi.

## 8. Brig alternatifi (ayrı gemi olarak)

Katalog: "Brig esas olarak 18. yy için güvenlidir" (`_context/GEMI_SINIFLARI_URETIM_KATALOGU.md`, #30). İki direkli ve kare armalı olur. Bu frigate'in malzeme kütüphanesini, top modüllerini ve soket şemasını yeniden kullanabilir. Kendi Gate A araştırması gerekir: ölçü, arma ve en az üç kaynak.
