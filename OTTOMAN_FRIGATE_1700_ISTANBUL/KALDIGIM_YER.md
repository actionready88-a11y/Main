# Kaldığım Yer — Hull Core v003 (2026-09-25)

Branch: `claude/amazing-meitner-keq46t` (repo: actionready88-a11y/Main, klasör: `OTTOMAN_FRIGATE_1700_ISTANBUL/`)

## Durum
- **Gate A: ONAYLA** (yön: hibrit, "Osmanlı esintili frigate").
- **2. karar:** Kullanıcı "kalyon istemiyorum, topları frigate'e göre düzenle; demo bölgesi gemisi (veya brig)" dedi.
  - Tip: üç direkli, tek batarya güverteli frigate. Referansların hepsi üç direkli olduğu için brig değil.
  - Çapa: HMS *Lyme* (1748): 35,92 m × 10,31 m. Su çekimi 4,5 m (tahmin).
  - Top: 24 batarya (12/borda) + 4 kıç kasarası + 2+2 kovalama lumbarı.
  - Ayrıntı: `reports/MODELLEME_PLANI.md`.
- `ship_spec.yaml` frigate'e göre güncellendi. Kalyon değerleri `archived_*` altında.
- **Blender:** bulut oturumunda `bpy` 5.0.1 (headless) ile Hull Core v001 üretildi.
  - `.blend`: `Blender/versions/OTTOMAN_FRIGATE_1700_ISTANBUL_v001.blend`
  - Betik: `scripts/build_hull_v001.py`. Yerelde `blender --background --python scripts/build_hull_v001.py` ile de çalışır.
  - Audit: `reports/scene_audit_v001.json`
  - Renderlar: `renders/v001/` (baş, kıç, iki profil, baş omzu, kıç omzu, güverte)

## v003 (son sürüm)
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
- Klasör adı: "1700" tiple uyumsuz. Öneri `OTTOMAN_FRIGATE_1780_ISTANBUL`; yeniden adlandırılmadı.
- Burun: 2 kovalama lumbarı (frigate) mı, konseptteki 3 top mu (varyant)?

## Fab referansı
- Rapor: `reports/reference_audit/age_of_sail/` (render adımı kullanıcı ortamında görsel üretmedi). Varlığın kendisi repoya girmez.

## Sıradaki adım
- v002: kıç aynası ve galeri (`SternModule`), lumbar kapakları, güverte donanımı, bocurumlar.
- Sonra: RigSet (direk boyları için kaynak), CannonBattery, SailSet.
