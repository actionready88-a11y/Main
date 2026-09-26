# Kalite testi — v029 → v030 (low-poly yasağı denetimi)

Tetikleyen: kullanıcı bildirimi — baş kasara küpeştesinde artık çubuk, yakından low-poly görünen parçalar, ambar fıçıları.
Araç: `skills/tersane/scripts/quality_audit.py` (Tersane skill'ine eklendi). Kural (TAHMİN değil, geometrik):

- **Faset:** yumuşak gölgeli kenarda yerel yay sapması (w/2)·tan(θ/4) > **1,5 mm** ve eğrilik sürekli
  (4° altı ve tekil ≥ 60° köşe sayılmaz). Kiriş sapması kuralının kenar karşılığı: seg ≥ π / acos(1 − 0,0015 / r).
- **Düz gölge:** eğri parçada düz gölgeli yüz oranı > %20.
- **Havada ada:** bağımsız parça başka geometriye 3 cm'den yakın değil ve kesişmiyor.

## Özet

| | v029 | v030 |
|---|---|---|
| Hatalı nesne | 86 / 109 | 23 / 110 |
| Faset kenar toplamı | 15.249 m | 343 m |
| Havada parça içeren nesne | 35 | 0 |

v029 değerleri aynı (son) ölçütle yeniden ölçüldü.

## Örnek nesneler (faset uzunluğu / en kötü sapma, üçgen)

| Nesne | v029 | v030 | Üçgen |
|---|---|---|---|
| `CORE_MOULDING_RAIL` | 82,5 m / 18,4 mm | 0,0 m / 0,0 mm | 3.464 → 28.012 |
| `CORE_MOULDING_BAND_LOW` | 1,8 m / 6,7 mm | 0,0 m / 0,0 mm | 3.464 → 8.336 |
| `CORE_WALE_MAIN` | 170,2 m / 4,9 mm | 0,0 m / 0,0 mm | 3.464 → 7.676 |
| `CORE_GUNPORT_FRAMES` | düz gölge | 0,0 m / 0,0 mm | 960 → 31.680 |
| `MOD_RIG_STANDING_MAIN_A` | 68,2 m / 4,9 mm | 0,0 m / 0,0 mm | 12.288 → 30.160 |
| `MOD_RIG_YARD_MAIN_COURSE_A` | 318,5 m / 8,3 mm | 1,7 m / 2,3 mm | 788 → 3.232 |
| `MOD_RIG_MAST_MAIN_A` | 710,8 m / 15,9 mm | 2,8 m / 16,1 mm | 8.332 → 16.292 |
| `MOD_RIG_RUNNING_MAIN_A` | 18,9 m / 109,7 mm | 2,5 m / 116,3 mm | 6.736 → 13.744 |
| `CORE_POOP_BALUSTRADE` | 536,7 m / 3,0 mm | 0,0 m / 0,0 mm | 16.168 → 43.384 |
| `CORE_SHOT_RACKS` | 148,8 m / 2,2 mm | 0,0 m / 0,0 mm | 18.648 → 30.888 |
| `CORE_RING_BOLTS` | 23,1 m / 4,0 mm | 0,0 m / 0,0 mm | 7.176 → 20.176 |
| `MOD_HOLD_CARGO_A` | 4129,7 m / 14,3 mm | 6,0 m / 1,9 mm | 59.308 → 29.860 |
| `MOD_SAIL_FURLED_MAIN_COURSE_A` | 315,6 m / 14,0 mm | 0,0 m / 0,0 mm | 3.248 → 29.964 |
| `CORE_HULL_SHELL` | 2211,1 m / 22,7 mm | 151,3 m / 7,3 mm | 141.864 → 557.592 |
| `MOD_BOAT_CUTTER_A` | 117,4 m / 33,4 mm | 40,2 m / 7,2 mm | 3.216 → 14.352 |

## Yapılanlar (v030)

1. **Küpeşte, altın silme, üç borda:** 4 köşeli kesit + 2 segmentli bevel yerine yuvarlatılmış profil (küpeşte 35, diğerleri
   16 nokta); bel–kasara yükselişinde istasyonlar Catmull-Rom ile sıklaştırıldı (121 → 250–412).
2. **Lumbar çerçeveleri (üst 20 + alt 6):** gövdeye ışınla oturan yarım yuvarlak silme; baş lumbardaki artık lento giderildi.
3. **Yeniden dilimleme** (`resegment.py`): halat, seren, direk, bigot, balüster, makara, gülle, pin, çember — kiriş sapması
   kuralı; eğri yol ve profiller sıklaştırıldı (halka cıvatası, brok, kangal, bodoslama, dümen).
4. **Bevel:** 56 modifier ≥ 3 segment + harden normals.
5. **Gövde:** Subdivision viewport 1 / render 2 idi (FBX ve oyun seviye 1 alıyordu) → ikisi de 2 (557.592 üçgen);
   20 lumbar deliği ışınla açık doğrulandı; omurga orta hat dikişi keskin.
6. **Ambar fıçıları:** tek `SM_PROP_CASK_A` (32 dilim, 16 çıta yivi, 4 çember, kapak girintisi; 2.364 üçgen) +
   282 örnek → UE'de Instanced Static Mesh.
7. **Sarılı yelkenler:** kesit 14 → 48 dilim, kıvrım dalgası metreye bağlı (1,75 m), boyuna sıklık 10 cm.
8. **Filika:** gövde ızgarası 28×10 → 56×24, omurga dikişi keskin.
9. **Havada parçalar:** gabya bigotları (22 adet, çanaklıktan 10–18 cm yukarıdaydı), bumba çatalı, cıvadıra başlığı,
   takım rafı kancaları, top kızağı arka palanga halkası (28 top) yerlerine oturtuldu; **merdiven/iskele kirişleri güverteye
   indirildi** (v027'de çakışma önlemi olarak 6 cm havada bırakılmıştı — yanlış çözümdü).
10. **Hareketli arma:** halatlar direk dibinde makarasız havada kırılıyordu (V biçimi) → 17 yönlendirme makarası.
11. **Top palangaları:** kutu makaralar → elipsoit makara + kayış.
12. **Fenerler:** düz camlı panolar keskin kenarlı (yumuşak gölge camı bükük gösteriyordu).

## Kalan (23 nesne) — açıkça

| Nesne | Faset | En kötü sapma |
|---|---|---|
| `CORE_HULL_SHELL` | 151,3 m | 7,3 mm |
| `MOD_BOAT_CUTTER_A` | 40,2 m | 7,2 mm |
| `MOD_STERN_GALLERY_A` | 6,9 m | 2,6 mm |
| `MOD_LANTERN_STERN_A` | 6,3 m | 2,6 mm |
| `MOD_HOLD_CARGO_A` | 6,0 m | 1,9 mm |
| `MOD_HELM_WHEEL_A` | 5,7 m | 1,6 mm |
| `MOD_CAPSTAN_A` | 5,6 m | 4,6 mm |
| `MOD_FLAG_PENNANT_OTTOMAN_A` | 5,4 m | 2,7 mm |
| `MOD_RIG_RUNNING_MIZZEN_A` | 2,9 m | 120,9 mm |
| `MOD_RIG_MAST_MAIN_A` | 2,8 m | 16,1 mm |
| `MOD_RIG_MAST_FORE_A` | 2,8 m | 15,7 mm |
| `MOD_RIG_MAST_MIZZEN_A` | 2,6 m | 15,9 mm |
| `MOD_RIG_RUNNING_MAIN_A` | 2,5 m | 116,3 mm |
| `MOD_RIG_RUNNING_FORE_A` | 2,3 m | 96,3 mm |
| `CORE_WALE_LOWER_TIER` | 2,1 m | 3,2 mm |
| `MOD_RIG_YARD_MAIN_COURSE_A` | 1,7 m | 2,3 mm |
| `MOD_RIG_YARD_FORE_COURSE_A` | 1,5 m | 2,0 mm |
| `MOD_RIG_YARD_MAIN_TOPSAIL_A` | 1,2 m | 1,7 mm |
| `MOD_RIG_YARD_MIZZEN_COURSE_A` | 1,2 m | 1,6 mm |
| `MOD_PUMP_ELM_A_S` | 1,0 m | 1,7 mm |
| `CORE_STEM` | 0,8 m | 1,9 mm |
| `MOD_SAIL_FURLED_JIB_A` | 0,8 m | 2,1 mm |
| `MOD_SAIL_FURLED_SPANKER_A` | 0,5 m | 2,1 mm |

Notlar:
- Hareketli arma: kalan fasetler halatın **yönlendirme makarası içinde** döndüğü halkalar (makara gövdesi örtüyor).
- Direkler: çanaklık dış hattının D köşeleri (64 eşit açılı nokta). Direği üreticisiyle yeniden kurmak denendi; eski pass
  zinciri yamaları yüzünden konum 3–13 m kaydı → uygulanmadı. Mesh düzeyinde çözüm sıradaki işte.
- Gövde: kıç "tuck" bölgesi (kıç bodoslaması yanı, su hattı altı) — gövde kafesinin yerel sıklaştırılması gerekir.
- Filika: gövde ızgarasında kalan 7 mm (baş/kıç uçları).
- Figür: **BLOCKOUT istisnası** — nihai model `references/KONSEPT_PRUVA_BOZKURT_01` ile yapılacak.
- Diğerlerinin çoğu eşiğe çok yakın (1,6–3 mm).

## Bütçe

Toplam render üçgeni (örnekler dahil): 931.094 → 1.424.918. Gövde, küpeşte ve
arma LOD zinciriyle (%50/%20, gövde +%8) yeniden üretildi (74 kaynak). Tekrarlanan parçalar örnekli (fıçı, top).
