# Kaldığım Yer — v022 (2026-09-26)

Branch: `claude/amazing-meitner-keq46t` (repo: actionready88-a11y/Main, klasör: `OTTOMAN_FRIGATE_1780_ISTANBUL/`)

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

## v022 (son sürüm)
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
