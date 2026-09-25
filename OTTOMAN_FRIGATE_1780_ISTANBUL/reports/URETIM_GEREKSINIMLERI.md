# Üretim Gereksinimleri — Kalıcı Kurallar

Kaynak: kullanıcı talimatı, 2026-09-25. Bu gemi ve sonraki bütün pass'ler için geçerlidir.
`_context/AGENTS.md` ve `_context/MODULAR_SHIP_STANDARD.md` kurallarına eklenir, onları değiştirmez.

## 1. Hedef

| Konu | Kural |
|---|---|
| Kullanım | Oyun üretimi; gemi demo bölgesinde yer alacak |
| Motor | **Unreal Engine 5.8** |
| Kalite | **Fotogerçekçi ama game-ready.** Low-poly, stilize ya da blockout görünümlü final yasak |
| Mimari | **Modüler**: Hull Core + tersanede değiştirilebilir modüller + socket/manifest (`MODULAR_SHIP_STANDARD.md`) |
| Oynanış alanı | **Yürünebilir güverteler ve oynanabilir alanlar** zorunlu |

## 2. Çalışma disiplini

1. **Versiyonlu kayıt:** her pass yeni bir dosya üretir: `Blender/versions/{SHIP_ID}_v00N.blend`. Önceki sürüm asla üzerine yazılmaz.
2. **Her pass sonunda:** render seti (baş, kıç, iki profil, baş omzu, kıç omzu, güverte) + kısa audit (`reports/scene_audit_v00N.json` ve sohbette birkaç satırlık özet).
3. **Gerekmedikçe tüm gemi yeniden kurulmaz.** v002'den itibaren her pass bir önceki `.blend`'i açar, yalnız hedef nesneleri ekler ya da değiştirir ve yeni sürüm olarak kaydeder. Betikler: `scripts/pass_v00N_<konu>.py`. `build_hull_v001.py` yalnız temel gövdeyi kurar. Hull shell ancak geometrisi gerçekten değişmesi gerekiyorsa yeniden üretilir ve bunun nedeni pass notuna yazılır.
4. Her pass'in değiştirdiği nesneler audit JSON'da `pass_changes` listesinde kayıt altına alınır.

## 3. Oynanış: mürettebatla yönetilen toplar

Kullanıcı tanımı:
- Topları **mürettebat** doldurur ve ateşler.
- **Oyuncu** hedef alır ve ateş emrini verir.
- Oyuncu gemide değilse emri **2. kaptan**, o da yoksa **topçu subayı** verir.

Bu bir oynanış (Unreal) mantığıdır. Modelleme tarafında gerektirdikleri:

| Gereksinim | Blender'daki karşılığı |
|---|---|
| Her top için mürettebat pozisyonları | Her top soketinin çevresinde `SOCK_CREW_<top soketi>_A..D` boş nesneleri: nişancı, doldurucu, tokmakçı/süngerci, manivela. Kişi sayısı **oyun parametresidir**, tarihsel iddia değildir |
| Geri tepme ve servis alanı | Top arkasında engelsiz güverte bölgesi. Ölçüsü top modeli yapılınca `CannonBattery` manifestine yazılır |
| Mühimmat akışı | Top yanında gülle rafları, ambar ağızları ve merdivenler (`DeckUtility`). NPC'nin alt güverteye inip çıkabilmesi için navmesh bağlantı noktaları (`SOCK_NAVLINK_*`) |
| Komuta zinciri istasyonları | `SOCK_STATION_CAPTAIN` (kıç kasarası, dümen yanı), `SOCK_STATION_SECOND_CAPTAIN`, `SOCK_STATION_GUNNERY_OFFICER` (bel, topların ortası) |
| Top gruplama | Top soketleri manifestte `battery_group` taşır: `PORT_MAIN`, `STARBOARD_MAIN`, `PORT_QD`, `STARBOARD_QD`, `CHASE_BOW`, `CHASE_STERN`. Emir bu gruplara verilir |
| Hasar ve durum | Her top bağımsız durum taşır (standart: `CannonBattery` modülü). Mürettebat kaybı oynanış tarafında hesaplanır |

## 4. Yürünebilir güverte gereksinimleri

| Konu | Kural |
|---|---|
| Çarpışma | Gövde fiziği `UCX_CORE_HULL_*` (dışbükey, sade) olarak kalır. Güverteler için ayrı, basit yürüme çarpışması: `UCX_DECK_*` kutuları, rampa ve merdiven hacimleri, küpeşte duvarları (düşmeyi engeller) |
| Tavan yüksekliği | Kasara altındaki bel ve batarya güvertesinde karakter kapsülü rahat geçmeli. **Açık karar:** v001'de kasara güvertesi batarya güvertesinin 2,0 m üstünde. Kiriş ve kalınlık düşülünce net yükseklik yaklaşık 1,7 m kalıyor; bu, UE varsayılan karakter kapsülü (176 cm) için yetersiz. Öneri: 2,3 m (oynanış sapması, tarihsel değil) |
| Geçişler | Bel ile kasaralar arasında merdivenler; ambar ağızlarından alt güverteye merdivenler |
| Hareketli gemi | Karakterler hareketli gemi üzerinde yürüyecek. Güverte çarpışması Hull Core root'una bağlıdır, ayrı fizik gövdesi yoktur |
| Oynanabilir alanlar | Kapsam kararı bekliyor: yalnız açık güverteler mi, yoksa alt güverte ve kıç kamarası da dahil mi? |

## 5. Unreal Engine 5.8 teslimat notları

- Birim 1 m = 100 cm. Eksen dönüşümü ve sancak yönü FBX smoke-test ile doğrulanır (`MODULAR_SHIP_STANDARD.md`).
- Standarttaki LOD zinciri korunur. Nanite kullanımı, hedef platform ve performans testine göre ayrıca kararlaştırılacak. Nanite varsayılıp LOD üretimi atlanmaz.
- Doku seti: BaseColor, DirectX Normal, ORM (R=AO, G=Roughness, B=Metallic). Prosedürel Blender materyalleri Gate B öncesi dokuya bake edilir.
