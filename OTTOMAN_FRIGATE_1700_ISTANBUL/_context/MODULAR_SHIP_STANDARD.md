# Hybrid Modular Ship Standard

Durum: ZORUNLU PROJE MİMARİSİ V2 — Unreal ve Blender uzman incelemesi işlendi.

## Kesin karar

Gemiler `hibrit modüler` üretilir:

- Fizik, yüzdürme ve ana siluet için tek güvenilir `Hull Core`.
- Oyuncunun tersanede değiştireceği her sistem bağımsız, socket uyumlu modül.
- Her tahta/çivi ayrı runtime parçası yapılmaz.
- Bütün gemi tek mesh içinde birleştirilmez.

Bu yaklaşım fizik kararlılığı, performans, tarihsel uyumluluk ve oyuncu özelleştirmesi arasında en iyi dengedir.

# Katmanlar

## 1. Hull Core — normalde değiştirilemez

Hull Core içinde birleşebilecek yapılar:

- Omurga ve ana gövde kabuğu
- Sabit iç yapı/postalar (görünür olması gerekiyorsa)
- Sabit ana güverte ve temel bordalar
- Top portlarının gövdeye ait sabit açıklıkları
- Sabit baş/kıç taşıyıcı yapılar
- Su hattı/fizik referansı
- Basitleştirilmiş root collision
- Buoyancy sample noktaları ve center-of-mass referansı

Hull Core tek fizik otoritesidir. Ayrı modüller bağımsız rigid-body olarak gemiyi parçalamaz.

## 2. Tersanede değiştirilebilir ana modüller

- `RigSet`: direkler, serenler, sabit arma ve rig-profile tanımı
- `SailSet`: yelken geometrisi, hareketli arma bağı ve performans verisi
- `SailSkin`: kumaş materyali, renk, amblem, yama/yıpranma; geometri/fizik değiştirmez
- `CannonBattery`: top tipi, araba/kızak, güverte/port uyumluluğu
- `Rudder`: tarihsel tip ve manevra istatistiği
- `Figurehead`: baş figürü/dekor
- `SternModule`: kıç galeri/kabin varyantı; yalnız uyumlu hull sınıflarında
- `DeckUtility`: vinç, ırgat, yük donanımı, ağ/balıkçılık seti, varil/kasa düzeni
- `AnchorSet`: çapa ve zincir/halat düzeni
- `BoatSet`: longboat/chalupa/jolly boat ve taşıma yuvası
- `LanternFlagSet`: fener, sancak, flama ve fraksiyon görselleri
- `ArmorProtectionSet`: tarihsel ve fiziksel olarak uygun sınırlı koruma eklentileri

## 3. Hasar modülleri

- Her değiştirilebilir modül ayrı sağlık/durum verisi taşıyabilir.
- Hasarlı görsel normal modülün varyantı veya material/mesh state'i olur.
- Kırılan modül root physics'i devralmaz; gemi fizik otoritesi Hull Core'da kalır.
- Direk kırılması sail force/center-of-effort değerini kapatır veya azaltır.
- Uzak NPC gemilerinde assembled/baked damage varyantları kullanılabilir.

# Yelken Değiştirme Kuralları

## Seviye A — SailSkin değişimi

Oyuncu şunları anında değiştirebilir:

- Kumaş rengi ve PBR seti
- Amblem/fraksiyon işareti
- Temizlik, yama, yıpranma ve ıslaklık varyantı

Aynı SailSet geometrisi ve aynı RigSet korunur. Performans yalnız izin verilen küçük kalite katsayılarıyla değişebilir.

## Seviye B — SailSet değişimi

Oyuncu aynı `RigProfile` içinde:

- Daha hafif/ağır kumaş
- Resiflenmiş/tam yelken seti
- Aynı seren/direk düzenine uyan farklı kesim
- Tarihsel olarak uyumlu performans varyantı

değiştirebilir.

## Seviye C — Rig conversion

Kare yelkenden latin/gaff/schooner düzenine geçmek gibi büyük değişikliklerde yalnız yelken mesh'i değiştirilmez. Şunlar paket olarak değişir:

- Direkler
- Serenler
- Sabit arma
- Hareketli arma bağlantıları
- SailSet
- Center-of-effort ve sail force profili
- Gerekirse güverte mast-step/partner adaptörü

Bu paket `RigSetBundle` olarak doğrulanır. Tarihsel ve yapısal olarak desteklenmeyen dönüşüm tersanede gösterilmez.

# Slot ve Socket Sistemi

Önerilen slot aileleri:

- `SLOT_RIG_PRIMARY`
- `SLOT_SAIL_SKIN`
- `SLOT_CANNON_PORT_01..N`
- `SLOT_CANNON_STARBOARD_01..N`
- `SLOT_RUDDER`
- `SLOT_FIGUREHEAD`
- `SLOT_STERN_MODULE`
- `SLOT_DECK_UTILITY_A..N`
- `SLOT_ANCHOR_PORT`, `SLOT_ANCHOR_STARBOARD`
- `SLOT_BOAT_PRIMARY`
- `SLOT_FLAG_STERN`, `SLOT_FLAG_MAST`

Blender Empty / Unreal socket adları birebir aynı olur:

- `SOCKET_RIG_PRIMARY`
- `SOCKET_RUDDER`
- `SOCKET_FIGUREHEAD`
- `SOCKET_CANNON_P_01`
- `SOCKET_CANNON_S_01`
- `SOCKET_DECK_A`

Socket transformları versiyonlandıktan sonra keyfî değiştirilmez. Değişiklik manifest sürümünü artırır ve tüm bağımlı modüller yeniden doğrulanır.

# Uyum Etiketleri

Her hull ve modül veri tabanlı etiket taşır:

- `Ship.Era.16`, `Ship.Era.17`, `Ship.Era.18`
- `Ship.Size.Boat`, `Small`, `Medium`, `Large`, `Capital`
- `Hull.CHALUPA_REDBAY`
- `Rig.Rowing`, `Rig.SingleMast`, `Rig.Square`, `Rig.Lateen`, `Rig.Gaff`, `Rig.FullShip`
- `Role.Fishing`, `Transport`, `Trade`, `War`, `Exploration`
- `Region.Basque`, `Atlantic`, `Mediterranean`, vb.
- `Slot.Rig`, `Slot.Sail`, `Slot.Cannon`, `Slot.Rudder`, vb.

Bir modül yalnız şu kontrolleri geçerse takılır:

1. Slot tipi eşleşir.
2. Hull/size etiketleri izin verir.
3. Dönem ve bölge kuralı izin verir.
4. RigProfile bağımlılıkları çözülür.
5. Fizik/mass/center-of-effort sınırları geçilir.
6. Socket/manifest sürümü uyumludur.

# Unreal Runtime Mimarisi

Önerilen ana actor: `AModularShipActor`.

- Root: `HullCorePhysics` static/skeletal mesh component.
- Buoyancy ve collision yalnız root hull otoritesinde.
- Basit görsel modüller: attached StaticMesh/SkeletalMesh Components.
- Kendi mantığı/animasyonu/hasarı olan modüller: component veya gerektiğinde Child Actor.
- Modüllerin collision'ı çoğunlukla query-only/no-physics; root ile çift fizik oluşturmaz.
- Toplar, yelken kuvveti ve direk hasarı kendi gameplay component'lerinden root gemiye kuvvet/istatistik bildirir.

Veri varlıkları:

- `UShipHullDefinition`
- `UShipModuleDefinition`
- `UShipRigSetDefinition`
- `UShipSailSetDefinition`
- `UShipLoadoutDefinition`
- `FShipSlotDefinition`
- `FShipModuleCompatibility`

Loadout kaydı asset referansı yerine kararlı kimlikler ve sürüm taşır:

- Hull ID
- Slot → Module ID
- Modül varyant/skin ID
- Dayanıklılık/hasar state'i
- Manifest version

Server loadout'u doğrular; satın alma ve modül değişimi server-authoritative olur. SaveGame yalnız doğrulanmış loadout'u saklar.

# Fizik Kuralları

- Hull collision ve buoyancy shape modül değişiminde sabit kalır; yapısal hull değişimi yeni hull sınıfıdır.
- Modül kütlesi sayısal olarak root toplam kütlesine eklenir.
- Center of mass, onaylı loadout değerleriyle sınırlı şekilde güncellenir.
- Yelken kuvveti SailSet/RigSet'in center-of-effort noktasından root'a uygulanır.
- Ağır toplar trim, dönüş ve ivmeyi etkileyebilir; fakat ayrı rigid bodies gemiyi titreştirmez.
- Su hattı Blender'da `Z=0`; seçilen geminin tarihsel draft'ı kullanılır. Genel 7 m kuralı küçük teknelere uygulanmaz.

# Blender Koleksiyon Standardı

Her gemi master `.blend` içinde:

- `00_REFERENCE`
- `10_HULL_CORE`
- `20_MODULES_RIG`
- `21_MODULES_SAILS`
- `22_MODULES_CANNONS`
- `23_MODULES_DECK`
- `24_MODULES_DECOR`
- `30_SOCKETS`
- `40_COLLISION`
- `50_LODS`
- `90_EXPORT`

Adlandırma örnekleri:

- `CORE_HULL_CHALUPA_1565`
- `MOD_RIG_CHALUPA_ROWLING_A`
- `MOD_SAILSET_CHALUPA_SQUARE_A`
- `MOD_SAILSKIN_CANVAS_PATCHED_01`
- `MOD_RUDDER_STEERING_OAR_A`
- `SOCKET_RIG_PRIMARY`

Tüm modüllerde:

- Transform uygulanmış
- Ölçek ve eksen standardı aynı
- Pivot socket birleşim noktasında
- UV ve texel density doğrulanmış
- PBR materyal slotları stabil
- LOD ve collision isimleri manifest ile eşleşmiş

# Performans

- Her dekoru runtime component yapma; yalnız oyuncunun değiştireceği veya hasar göreceği anlamlı kümeleri ayır.
- Tekrarlanan makaralar, halatlar ve küçük detaylar gerektiğinde instancing/atlas kullanır.
- Ortak trim sheet/material library draw-call sayısını azaltır.
- Oyuncu gemisi tam modular kalabilir; uzak NPC gemiler assembled/baked temsil kullanabilir.
- Her modül kendi LOD zincirine sahip olur; uzak mesafede assembled proxy/HLOD kullanılabilir.

# QA Hard Fails

- Swappable modül Hull Core'a join edilmiş.
- Socket adı/transformı manifest ile uyuşmuyor.
- RigSet ile SailSet uyumsuz.
- Modül çift fizik/collision üretiyor.
- Modül değişimi su hattını veya root hull collision'ı geçersiz kılıyor.
- Tarih/bölge etiketi uyumsuz modül takılabiliyor.
- Save/load sonrası loadout farklı kuruluyor.
- Eksik PBR, UV, LOD veya damage state.

# İlk CHALUPA İçin Başlangıç Slotları

Chalupa küçük olduğu için gereksiz karmaşıklık yapılmaz:

- `SLOT_RIG_PRIMARY`: kürek-only veya kaynak doğrulanırsa küçük direk/yelken paketi
- `SLOT_SAIL_SKIN`: doğal/yamalı/işaretli kumaş
- `SLOT_RUDDER`: steering oar/dümen kanıtına göre
- `SLOT_DECK_UTILITY_A`: balıkçılık veya balina avı donanımı
- `SLOT_CARGO_A`: varil/halat/av ekipmanı
- `SLOT_FLAG_STERN`: yalnız tarihsel bağlam uygunsa

Chalupa'ya top bataryası, büyük kıç kabini veya uyumsuz ağır rig slotları eklenmez.

# V2 Uzman İncelemesiyle Eklenen Runtime Ayrıntıları

## Önerilen Unreal sınıf ağacı

```text
AShipPawn / AModularShipActor
├─ UStaticMeshComponent PhysicsHull       // root, tek Chaos rigid body
├─ UShipBuoyancyComponent
├─ UShipLoadoutComponent                  // kurulu modüller + FastArray
├─ UShipStatsComponent                    // deterministic aggregate/cache
├─ UShipDamageComponent
├─ UShipMountRegistryComponent
├─ Stable USceneComponent mount points
└─ Attached module actors/components
```

- Modüller root'a attach edilir fakat `SimulatePhysics=false` kalır ve root body'ye weld edilmez.
- Kritik mount noktaları yalnız render-mesh socket'ine bağlı kalmaz; stabil `USceneComponent` hiyerarşisi ve değişmez `MountId/FGuid` taşır.
- Socket, sanatçı hizalamasıdır; `MountId`, save/load ve replication kimliğidir.
- Kendi hasarı, animasyonu veya etkileşimi olan top/dümen/yelken modülleri Actor/Gameplay Component olabilir.
- Figür, fener ve küçük dekorlar mesh component veya ISM/HISM olur; yüzlerce replicated Actor yapılmaz.
- Attached modül transformları ayrıca replicate edilmez; yalnız loadout state'i replicate edilir.

## Mount point veri modeli

```text
MountId: değişmez FGuid
SocketName: sanatçı bağlantısı
SlotTag: Ship.Slot.*
CompatibilityTags: era/region/size/rig
LocalOffset: kontrollü düzeltme
MountGroup: direk–arma–yelken dependency grubu
MaxSupportedMass: yapısal sınır
```

Her manifest slotunda `id + mount_id + socket` birlikte bulunur. Socket adı değişse bile migration tablosu MountId üzerinden eski kayıtları korur.

## Data Asset ve Data Table ayrımı

- `UShipModuleDefinition : UPrimaryDataAsset`: mesh/actor class, fizik kütlesi, local CoM, compatibility query, LOD/proxy, tarih ve teknik bağımlılıkların tek doğruluk kaynağı.
- `UShipHullDefinition`: hull taban istatistikleri, mount registry, buoyancy ve güvenli CoM sınırları.
- `UShipLoadoutDefinition`: kurulu modül kimlikleri ve manifest sürümü.
- Data Table: yalnız ekonomi, tersane fiyatı, faction erişimi ve balance değerleri.
- Aynı fizik/uyumluluk alanı Data Asset ve Data Table'da yinelenmez.

## Deterministik stat toplama

```text
HullBase
+ FlatModuleModifiers
+ AdditivePercentModifiers
× MultiplicativeModifiers
+ RuntimeDamage/Condition
= FinalStats
```

Hesaplanan ana değerler: displacement/dry mass, cargo, top kapasitesi, sail area, thrust, drag, turn rate, stability, crew, health, center of mass ve center of effort.

Her tick hesaplanmaz. Modül değişimi, kargo, kritik hasar, su alma veya yelken durumu değişiminde dirty edilir ve bir kez yeniden hesaplanır.

## Save/load ve multiplayer

- Save dosyası Actor/mesh yolu değil `SchemaVersion + Hull PrimaryAssetId + MountId→Module PrimaryAssetId + condition/state` saklar.
- Yükleme sırası: hull → mount registry → dependency modülleri → diğer modüller → stats → buoyancy.
- Eski/eksik modül için migration ve fallback bulunur.
- `UShipLoadoutComponent`, `FFastArraySerializer` ile yalnız MountId, ModuleId, condition/state ve skin ID replicate eder.
- Client tersane önizlemesi yapar; kurulum, envanter, maliyet ve compatibility kararı server-authoritative olur.
- Server root fiziğin otoritesidir; client transform/velocity interpolate eder.

## Atomik yelken/rig swap

```text
Client preview
→ ServerRequestInstallModule
→ Envanter + ücret + compatibility doğrulaması
→ Yeni assetleri async load
→ Yeni seti hidden attach et
→ Rig/material/condition state aktar
→ Loadout FastArray commit
→ Stats + sail area + center of effort hesapla
→ CoM/fizik değerlerini atomik uygula
→ Yeni seti görünür yap
→ Eski seti kaldır
→ Save dirty
```

Direk, arma ve yelken dönüşümü tek transaction'dır. Kısmi başarısızlıkta eski konfigürasyon aktif kalır ve rollback yapılır.

## CoM ve buoyancy uygulaması

- Hull sınıfına göre 8–24 sabit buoyancy sample/pontoon noktası kullanılabilir; küçük botlarda daha azı testle yeterli olabilir.
- Buoyancy noktaları modül swap'ında değişmez; hidrostatik gövdeyi temsil eder.
- Modül kütlesi ve local CoM, root toplamına eklenir; sonuç güvenli hull sınırlarına clamp edilir.
- CoM değişimi birkaç fizik frame'inde filtrelenir ve swap commit sonrası yalnız bir kez uygulanır.
- Yelken kuvveti center-of-effort noktasından root'a uygulanır; yatma momenti ve stabiliteyi etkiler.

## Runtime LOD/proxy

- Yakın: tam modüler loadout.
- Orta: düşük LOD modüller, sade arma ve azaltılmış cloth/tick.
- Uzak: `HullId + LoadoutHash` anahtarıyla cached/baked ship proxy.
- Çok uzak: impostor veya tek düşük detaylı siluet.
- Halatlar uzak mesafede kart/texture/sade mesh olur.
- Significance Manager animasyon, cloth, tick, audio ve component görünürlüğünü kademeli kapatır.
- Hareketli özelleştirilebilir gemilerde yalnız standart world HLOD'ye güvenilmez.

# V2 Blender ve Export Ayrıntıları

## Koordinat, origin ve ölçek

- Blender Metric, `Unit Scale = 1.0`; 1 Blender unit = 1 metre.
- Import smoke-test: Blender'daki 1 m test küpü Unreal'da 100 cm olmalı.
- Mantıksal eksen: X ileri, Y sancak, Z yukarı.
- Root origin: X/Y tasarım orta hattı ve referans orta kesit; Z su hattı = 0.
- Gerçek ağırlık merkezi ayrı `SOCK_COM`/manifest verisiyle tanımlanır.
- Modül origin'i attachment socket'iyle örtüşür.
- Export objelerinde scale 1/1/1, uygulanmış rotation/scale, negatif scale ve gizli parent offset yoktur.

## Socket authoring ve Unreal export

- Mantıksal slot ID: `SLOT_RIG_PRIMARY` gibi kararlı gameplay kimliği.
- Blender authoring Empty: kısa `SOCK_*` adı kullanılabilir.
- Unreal static-mesh FBX auto-socket gerektiğinde Empty adı `SOCKET_<RenderMeshName>_<SocketName>` biçimine export edilir.
- Exporter/re-import testi manifestteki MountId ile engine socket eşleşmesini doğrular.
- Port/starboard numaraları baştan kıça artar.

## Rig ve Sail family metadata

```text
HullSocketSchema = RBC_01
MastRigFamily    = RBC_SINGLEMAST_A
SailFamily       = RBC_SINGLEMAST_A
SkeletonVersion  = RBC_RIG_01
```

- SailSet yalnız aynı MastRigFamily ve skeleton sürümüyle bağlanır.
- Bone adları sürüm içinde değişmez.
- Mast ailesi değişirse mast + sabit arma + hareketli arma + SailSet birlikte değişir.
- Blender curve halatlar FBX öncesi kontrollü mesh'e bake edilir veya Unreal spline rig olarak yeniden kurulur.

## FBX/glTF

- Unreal gameplay ana yolu: her teslimat birimi için ayrı FBX/Interchange asset.
- `Add Leaf Bones: Off`.
- Deterministik triangulation export kopyasında uygulanır.
- Custom normals/tangent politikası proje genelinde sabitlenir.
- Her FBX temiz Blender sahnesine ve Unreal'a re-import edilerek boyut, pivot, socket ve materyal karşılaştırılır.
- glTF yalnız review, materyal kontrolü ve arşiv interchange için ikincil yoldur.

## LOD/collision/PBR

- Hull öneri başlangıcı: LOD0 %100, LOD1 ~%50, LOD2 ~%20, LOD3 ~%8; siluet ve test sonuçlarına göre ayarlanır.
- Büyük modüller başlangıç: %100/%50/%20.
- Her LOD aynı origin, bounds ve socket uzayını korur.
- Physics hull birkaç sade convex `UCX_*` parçadır; moving ship için Complex-as-Simple kullanılmaz.
- Gameplay modülleri bağımsız 0–1 UV; hull tile/trim wood + unique mask/decal UV kullanabilir.
- ORM kanal standardı: R=AO, G=Roughness, B=Metallic; Unreal için DirectX normal.
- Her modül material slot/draw-call bütçesine uyar.

## Damage variant standardı

- Küçük hasar: material mask, decal, vertex paint.
- Orta hasar: aynı origin/socket şemasını koruyan lokal swap mesh.
- Kopma: sınırlı chunk veya Geometry Collection.
- Devre dışı kalan socket manifestte `disabled` işaretlenir.
- Tam gemi her hasar seviyesi için kopyalanmaz.

# Zorunlu Nihai Teslimat Paketi

Her gemi tamamlandıktan ve Gate B onayı alındıktan sonra çıktılar birbirinden ayrı klasörlere alınır:

```text
{SHIP_ID}/
├─ Blender/
│  ├─ {SHIP_ID}_master.blend
│  ├─ versions/
│  └─ backups/
├─ Materials/
│  ├─ {SHIP_ID}_materials.blend
│  ├─ material_manifest.yaml
│  └─ previews/
├─ Textures/
│  ├─ Hull/
│  ├─ Wood/
│  ├─ Metal/
│  ├─ Rope/
│  ├─ Canvas/
│  └─ Decals/
├─ FBX/
│  ├─ HullCore/
│  ├─ Modules/
│  └─ export_manifest.yaml
├─ references/
├─ renders/
├─ reports/
└─ _archive/
```

## Paket kuralları

- Final master `.blend` gemi köküne değil `Blender/` altına yazılır.
- `Blender/versions/` sürümlü kaynakları; `Blender/backups/` kritik işlem öncesi kopyaları saklar.
- `Materials/` içinde yeniden kullanılabilir Blender material-library `.blend`, manifest ve gerekirse materyal önizlemeleri bulunur.
- `Textures/` dış PBR görsellerinin gerçek kaynağıdır. Blender texture yolları gemi paketine göre relative yapılır.
- Texture'ların `.blend` içine pack edilmesi yalnız yedektir; dış texture dosyalarının yerini tutmaz.
- `FBX/HullCore/` fizik/görsel gövde birimini; `FBX/Modules/` her bağımsız gameplay modülünü ayrı dosya olarak tutar.
- `FBX/export_manifest.yaml` source `.blend` sürümü, export zamanı, eksen/ölçek, modül kimliği, dosya hash'i ve re-import sonucunu kaydeder.
- Materyal dosyaları ile texture görselleri karıştırılmaz: materyal tanımı `Materials/`, piksel haritaları `Textures/` altında kalır.
- Paket yalnız klasörlerin varlığıyla tamamlanmaz; beklenen dosyalar non-empty olmalı, relative texture yolları çözülmeli ve FBX temiz sahne/Unreal re-import kontrolünden geçmelidir.
