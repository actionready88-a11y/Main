# Tersane — Gövde, boolean, merdiven, soket, çarpışma

> SKILL.md'nin ayrıntı dosyası. Bölüm numaraları SKILL.md ile aynıdır.

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
