# Kızıl Sancak Uyarlama Planı — dış ve iç düzen

Durum: **ONAYLANDI (Gate A, kullanıcı, 2026-09-26)** — "Onaylıyorum, figürü en son uyarlarız".

## 0. Kullanıcı kararları

- **Yelkenler:** ana mayistra ve ana gabyada kızıl bant (orta 4 bez eni) + arma amblemi.
- **Figür:** ay-yıldızdaki yıldız silinir, hilal kalır. Figür en son uyarlanacak.
- **Gemi adı:** "Kızıl Pençe" (şimdilik).
- **Kıç topları:** kaldırıldı (v042). Toplam 20 borda + 2 baş topu.
- **Çırak rıhtımı:** kaptan dairesinde değil, subay kabinlerinden de ayrı. Alt güvertede baş tarafta perdeli çırak yatakhanesi olarak (v042).
- **Toplar:** değiştirilmez. Yalnız birebir tuğra mühürle değiştirildi; istenirse geri alınır.
- **Konsept görseli:** kullanıcı, paketi GPT'ye okutarak bir konsept üretti. **Arma bu konseptten alındı** (ilk taslaktaki "Yelken Hilali" yerine):
  - yukarı açık hilal;
  - içinden geçen lale uçlu mızrak;
  - pusula biçimli, uzun ışınlı gök yıldızı (birebir Osmanlı 8 köşeli yıldızı değil);
  - altta üç dalga.
  - Konseptteki slogan: "Dalgalarda Daima".
- **Konseptten sonraki eklemeler için referans:**
  - kızıl-altın küpeşte baklava deseni;
  - süslü kıç fenerleri;
  - dalga, top/gök gürültüsü ve lalevari motifleri;
  - renk paleti: koyu ahşap, siyah, kızıl, altın, halat, kanvas, demir.
Kaynak: kullanıcının "Project Pirate Tasarım" paketi (depoya konmadı; yalnız özet ve sayfa göndermeleri).

- Bütün Ciltler, s. 13–17: devlet ilhamı ve sancak dili.
- Bütün Ciltler, s. 44–54: Kızıl Sancak İmparatorluğu.
- Ek Cilt II, s. 81–100: bölme, oda ve yaşam alanları.
- Ek Cilt II, s. 111–115: cephanelik.

## 1. Bağlayıcı kurallar (kaynaktan)

**Kimlik**

- Gemi **Kızıl Sancak İmparatorluğu** donanmasına aittir.
  - Başkent ve ana üs: **Sancakkale** (boğaz şehri).
  - Donanma kurumu: **Kızıl Deniz Meclisi**. En yüksek deniz görevlisi: **Büyük Kaptan**.
  - Hanedan: **Alkan Hanedanı** (kurucu: Alkan Beyran). Hükümdar unvanı: **Yüce Sancaktar**.
- İlham kuralları (s. 13–15, On İlke 1):
  - "Osmanlı ruhundan ilham alır; onun kopyası değildir."
  - "Yüzde Yetmiş Özgünlük Kuralı": birebir hükümdar, kurum, birlik adı ve sembol kullanılmaz.
  - Mimari, sanat ve denizcilik kültürü ilham olabilir.

**Sancak dili (s. 17)**

- Kızıl zemin.
- **Hilal benzeri özgün gök sembolü**.
- Altın işlemeler.
- Sancak kıvrımları.
- En fazla birkaç güçlü sembol; uzaktan okunur olmalı.

**Kuruluş efsanesi (s. 44)**

- Beyran, parçalanmış **kırmızı bir gemi yelkenini** sancak yaptı.
- Kırmızı yelken hanedanın, ordunun ve **denizcilerin** ana sembolüdür.

**Donanma doktrini (s. 53)**

- Asker ve top taşıma kapasitesi.
- Kıyı bataryalarıyla ortak hareket.
- Güçlü topçu.

**İç düzen (Ek Cilt II)**

- Aşağıdaki çiftler ayrı şeylerdir:
  - `CompartmentID ≠ RoomLabel ≠ OperationalStationID ≠ WatertightZoneID` (s. 81)
  - `StructuralDeck ≠ HabitableDeck` (s. 95–99)
  - `MaximumEmergencyPersons ≠ SustainableCrewCapacity` (s. 95–99)
- **Kaptan kamarası (yaşam) ile CaptainOffice (makam) ayrı alanlardır.** "Kaptan kamarası makam alanıdır, kişisel miras değildir." (s. 98)
- Hamak, hot-bunking ve vardiya dinlenmesi gerçek alan ister (s. 95).
- Galley, sanitasyon ve içme suyu noktaları (s. 96).
- Hastane, havalandırma ve atölye alanları (s. 97).
- Genç CharacterID (Vasiyet Yolcusu) **junior yolcu / çırak rıhtımı** kullanır (s. 99).
- Cephanelik, hazırlama odası ve **ready-service dolabı** ayrı fiziksel alanlardır (s. 112, 115).
- Hasar kontrol stokları fiziksel ve dağıtılmıştır (s. 87).

## 2. Mevcut gemide kuralla çelişenler

| Öğe | Şimdi | Sorun |
|---|---|---|
| Sancak / flandra | Kırmızı zemin, beyaz ay-yıldız | Gerçek Osmanlı / Türk bayrağı → "birebir sembol" |
| Top C | Stilize tuğra + kitabe | Tuğra birebir Osmanlı kurumu sembolü |
| Kıç arması | Hilal madalyon + rumi kanat | Hilal serbest, ama özgün gök sembolüne çevrilmeli |
| Figür C (Meshy) | Göğüs ve plakada **ay-yıldız** kabartması | Birebir sembol (geometride oyulmuş) |
| Kamara | Tek oda: yatak + masa birlikte | Kaptan kamarası / CaptainOffice ayrımı yok |
| Mürettebat yaşamı | Hamak, ocak, revir, atölye, çırak rıhtımı yok | Ek Cilt II s. 95–99 |
| Cephanelik | Yalnız gülle rafları | Cephanelik / hazırlama odası / hazır dolap yok |
| Adlandırma | `OTTOMAN_…_ISTANBUL` | Teknik klasör adı kalır; oyun içi kimlik Kızıl Sancak / Sancakkale |

Kurala uygun olup korunacaklar:

- Rumi, lale, kalemişi, çini ve halı desenleri (s. 13: "sanat, mimari" ilhamı).
- Kızıl-siyah gövde ve altın silmeler.
- Bozkurt figürü; sembol düzeltmesi dışında.

## 3. Dış düzen değişiklikleri

1. **Kızıl Sancak sancağı** (yeni doku + kumaş):
   - Kızıl zemin, altın işleme kenar.
   - Özgün gök sembolü **"Yelken Hilali"**: hilal biçiminde, iç kenarı yırtık bir yelkenin kıvrımıyla oluşur (kuruluş efsanesi); yıldız yok.
   - Uçta **sancak kıvrımı**: çatal ya da alev biçimli uç.
   - Flandra: kızıl, altın kenar, uzun çatal uç.
2. **Yelkenler:** kurucu kırmızı yelken simgesi (seçim soruda).
3. **Top C:** tuğra ve kitabe kaldırılır. Yerine **Alkan mührü** (Yelken Hilali + hanedan kıvrımı) ve topçu ocağı damgası gelir.
4. **Kıç arması:** hilal madalyon Yelken Hilali olur. Rumi kanatlar ve kızıl-altın sancak kıvrımları eklenir. Kıç panosuna küçük gök sembolleri.
5. **Figür C:** ay-yıldız kabartmaları (seçim soruda).
6. **Kimlik özellikleri** (UE için):
   - `faction = KIZIL_SANCAK`
   - `home_port = Sancakkale`
   - `navy = Kızıl Deniz Meclisi`
   - Gemi adı sorulacak.

## 4. İç düzen değişiklikleri

Her oda şu kayıtları alır:

- `CompartmentID`, `RoomLabel`, `OperationalStationID`, `WatertightZoneID` özellikleri.
- Bir UE soket boşu (`ROOM_*` / `STATION_*`).

| Alan | Yer | İçerik |
|---|---|---|
| **CaptainOffice (makam)** | Kıç kamara, ön yarı (bölmeyle ayrılır) | Makam masası; harita masası; **sancak dolabı** (resmî sancak, ferman kutusu, Kızıl Deniz Meclisi mühürleri); duvarda Kızıl Sancak; gelen-giden yazı rafı |
| **Kaptan kamarası (yaşam)** | Kıç kamara, arka / yan (kapılı) | Asma yatak (cot), sandık, lavabo dolabı, kişisel raf |
| **Junior / çırak rıhtımı** | Kamara bölmesi yanında küçük kabin | Dar ranza, sandık, ders ve harita tahtası |
| **Subay kamaraları** | Alt güverte kıç, gunroom bölmesinin gerisi | 2–4 perdeli kabin (yarı yükseklik perde) |
| **Mürettebat hamakları** | Alt güverte, top aralarında kirişlere | Asılı ve sarılı hamaklar; vardiya düzeni (yarı dolu) |
| **Galley (ocak)** | Top güvertesi, baş kasara altı | Tuğla ocak, kazan, baca; içme suyu fıçısı ve ölçü kabı |
| **Sanitasyon** | Baş (bodoslama yanları) | Tahliye oturakları (heads), bir alt kademede |
| **Revir** | Alt güverte, baş tarafı | 2–3 yatak, cerrah sandığı, fener, perde |
| **Atölyeler** | Alt güverte / ambar üstü | Marangoz (tezgâh, alet), yelkenci (bez topu, iğne), cebeci (mengene) |
| **Cephanelik** | Ambar, en alt, su hattı altı | Kurşun kaplı bölme, barut fıçıları (mühürlü), fener odası camı |
| **Hazırlama odası** | Cephaneliğin önü | Barut torbası dolum tezgâhı, ıslak perde (yangın) |
| **Ready-service dolapları** | Top güvertesinde toplar arası | Kapaklı, sınırlı sayıda torba |
| **Hasar kontrol istasyonları** | Her güvertede 2 nokta | Tapa, kalafat, kereste, kova (dağıtılmış stok) |
| **Havalandırma** | Güverte | Rüzgâr hortumu (windsail), ızgaralar |

Sınıf notu: frigat sınıf kuralı korunur. Tek top güvertesi korunur; odalar mevcut güverte kotlarına yerleşir, gövde değişmez.

## 5. Uygulama sırası (her biri ayrı sürüm, render + kalite testi)

- **v041:** sancak, flandra, Yelken Hilali dokuları; kıç arması; top C mührü; figür sembol düzeltmesi.
- **v042:** kamara bölünmesi (CaptainOffice / yaşam / junior rıhtım) + subay kabinleri.
- **v043:** alt güverte yaşamı: hamak, revir, atölyeler.
- **v044:** galley, su, sanitasyon, havalandırma; cephanelik / hazırlama odası / ready dolapları; hasar kontrol istasyonları.
- **v045:** oda kimlikleri, soketler, UE notları; genel iç ve dış render turu.
