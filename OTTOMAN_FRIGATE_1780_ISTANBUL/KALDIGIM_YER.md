# Kaldığım Yer — v012 (2026-09-26)

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

## v012 (son sürüm)
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
- v002: kıç aynası ve galeri (`SternModule`), lumbar kapakları, güverte donanımı, bocurumlar.
- Sonra: RigSet (direk boyları için kaynak), CannonBattery, SailSet.
