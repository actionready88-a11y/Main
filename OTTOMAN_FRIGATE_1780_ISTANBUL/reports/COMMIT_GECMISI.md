# Commit geçmişi — dal `claude/amazing-meitner-keq46t` (73 commit, eskiden yeniye)

`main`'in 71 commit önünde. Üretim: `git log --reverse` (2026-09-26).

| # | Commit | Tarih | Mesaj |
|---|---|---|---|
| 1 | 18d82d8 | 2026-09-25 | Initial commit |
| 2 | 2493f8f | 2026-09-26 | Add Ottoman frigate folder |
| 3 | 9a2fd0b | 2026-09-25 | Frigate revizyonu: modelleme planı, spec güncellemesi ve Hull Core v001 |
| 4 | c995711 | 2026-09-25 | Üretim gereksinimlerini kalıcı kurallar olarak ekle |
| 5 | eef3f6b | 2026-09-25 | v001 ölçülü 4 görünüş paftası ve referans denetim betiği |
| 6 | 3b68387 | 2026-09-25 | Pass v002: kıç/dümen kopukluğu ve baş omurga açıklığı düzeltmesi |
| 7 | 24b36de | 2026-09-25 | v002 ölçülü 4 görünüş paftası |
| 8 | 33a27ea | 2026-09-26 | Add reference quality audit for Fab age-of-sail ship blend |
| 9 | ccabbce | 2026-09-25 | Pass v003: sade oyun çarpışması, bel açık, viewport temizliği |
| 10 | 8782894 | 2026-09-25 | Klasörü OTTOMAN_FRIGATE_1780_ISTANBUL yap; kararları işle; pass v004 oynanış soketleri |
| 11 | 1622c94 | 2026-09-25 | Yeniden adlandırma sonrası içerik güncellemeleri ve pass v004 |
| 12 | 90b2fe5 | 2026-09-26 | Pass v005: yüksek kıç üstü güverte, merdivenler, dümen, kıç galerisi ve fener |
| 13 | 1e16c51 | 2026-09-26 | Pass v006: kıç üstü merdivenleri sancak ve iskele köşelerine |
| 14 | 5d66d9b | 2026-09-26 | Pass v007: gemi eşit oranda ×1,10 (oyun ölçeği) |
| 15 | 98c2c53 | 2026-09-26 | Pass v008: bel → kıç kasarası ve bel → baş kasarası merdivenleri |
| 16 | 62e54a0 | 2026-09-26 | Pass v009: baş kasarası merdivenleri sağ/sol köşelere |
| 17 | 896d38b | 2026-09-26 | Pass v010: kıç kasarası altında kaptan kamarası |
| 18 | e923dee | 2026-09-26 | Pass v011: kıç kasarası kaldırıldı; kıç üstü ve kaptan kamarası ana güverteye indi |
| 19 | e7e1899 | 2026-09-26 | Pass v012: 20 borda + 4 kovalama topu |
| 20 | eebebff | 2026-09-26 | Pass v013-v016: Hull_B alt güverte, 9 librelik top, RigSet, kamara içi |
| 21 | 2908464 | 2026-09-26 | Pass v017-v018: filika, çapalar, ırgat, batarya ayrıntıları; v015 çanaklık düzeltmesi; renderlar |
| 22 | d00711e | 2026-09-26 | Pass v019: UCX kalite düzeltmeleri; v015 renderları |
| 23 | 47efaf0 | 2026-09-26 | v016 kamara renderları |
| 24 | 4b5b381 | 2026-09-26 | v014/v017/v018 renderları ve v018 ölçülü pafta |
| 25 | f5b25b3 | 2026-09-26 | Pass v020-v022: gerçekçi top (9PDR_B), bozkurt figürü (blockout), SailSet + Osmanlı motifleri |
| 26 | db31e17 | 2026-09-26 | Pass v023: hareketli arma, makaralar, palanga parmaklıkları; v020 renderları |
| 27 | e0971e1 | 2026-09-26 | Pass v024: Osmanlı donanma sancağı (gaf ucunda) ve flama |
| 28 | 825de37 | 2026-09-26 | Pass v025-v026: ambar iç mekânı, LOD zinciri; v022-v025 renderları |
| 29 | 90b7169 | 2026-09-26 | Doku bake (tile BC/N/ORM), top varyantları (FBX, gemide kullanılmaz), belgeler |
| 30 | bc1a30b | 2026-09-26 | Pass v027: frigate kararı — alt güverte 3+3 top (dengeli, ortak salvo), ambar ağızları açıldı, merdiven çakışmaları giderildi |
| 31 | dea652c | 2026-09-26 | Tersane skill'i: gemi yapımında öğrenilenler (canlı belge) |
| 32 | 0b97605 | 2026-09-26 | Tersane skill: taşınabilir betikler (geom, stairs, ship_checks, lods, bake); pruva konsept referansı; v027 renderları |
| 33 | 28b8b1f | 2026-09-26 | v028 Osmanlı tunç topu C (tuğra, kitabe, yunus kulplar, palanga, alet rafları); v029 yelken aç/kapa anahtarı (CTRL_YELKEN + N paneli) |
| 34 | f45c064 | 2026-09-26 | Belgeler: yelken anahtarı kullanımı, Tersane skill notları |
| 35 | 96635ab | 2026-09-26 | Tersane skill: çekirdek SKILL.md + references/ ayrıntı dosyaları, betik tablosu, tersane.zip paketi |
| 36 | ab74ec5 | 2026-09-26 | v030 kalite testi: low-poly yasağı ölçülebilir (kiriş sapması ≤ 1,5 mm); küpeşte/silme/borda profilleri, gövdeye oturan lumbar çerçeveleri, yeniden dilimleme, gövde subsurf 2, fıçı örnekleme, havada parçalar ve merdiven ayakları, yönlendirme makaraları; Tersane: quality_audit.py + resegment.py |
| 37 | afbec67 | 2026-09-26 | v031 Osmanlı süslemeleri (dış: gövde rumi frizi, kıç panoları + hilal-yıldız arma, kasara alnı, kedi başı rozetleri, alemler; iç: çini kuşağı, kalemişi, tavan, Uşak halısı, sedir minderleri) + CTRL_SUSLEME anahtarı; kuşak tahtaları lumbar üstüne, zincir levhaları lumbar önünden çekildi |
| 38 | 2ec3ef4 | 2026-09-26 | Belgeler: MODELLEME_PLANI §5ad–§5ag, KALDIGIM_YER v031 |
| 39 | bc325e7 | 2026-09-26 | v031 ilk doğrulama renderı (baş kasara küpeştesi: artık lento giderildi) |
| 40 | 3e67794 | 2026-09-26 | v032: gövde frizi kesintisiz (yalnız lumbar arkasında kesilir), kıç arması yönü düzeltildi (yıldız hilalin açık tarafında) |
| 41 | eb46095 | 2026-09-26 | gitignore: __pycache__ |
| 42 | 531772d | 2026-09-26 | v031 kasara alnı renderı |
| 43 | 82fb0fb | 2026-09-26 | Masaüstü devir paketi (TESLIM/ iki zip, v032) + KALDIGIM_YER devir bölümü |
| 44 | b0112e5 | 2026-09-26 | v033 faset temizliği (minder, arma, alem, ön çanaklık, tavan, flandra) + devir paketi v033 + KALDIGIM_YER |
| 45 | c242c28 | 2026-09-26 | v034 bozkurt figürü B: parçalar (gövde, kaide, kulak, göz, 20 diş, burun, dil) ayrı kurulup EXACT boolean ile tek kapalı parça (1 ada, manifold); 45,8k üçgen, UCX 57 köşe, cıvadırayla 1,61 m boşluk |
| 46 | 9f5b862 | 2026-09-26 | KALDIGIM_YER v034 + Tersane dersleri (tek parça figür, metaball) |
| 47 | e64a660 | 2026-09-26 | v035 bozkurt figürü B2: SDF yontusu (anatomik kafa, açık çene, dişler, burun delikleri, hırlama kıvrımları, oyuklu kulaklar, yüzeye yatan 319 tüy tutamı, altın gadroon/rumi kaide), tek parça kapalı mesh 260k üçgen; baş parmaklıkları kaideden bordaya gömülü yeni yol + yuvarlak profil + destekler; Tersane: sdf_sculpt.py |
| 48 | 115ae6d | 2026-09-26 | v035: renderlar, KALDIGIM_YER, tersane skill güncellemesi, teslim zipleri |
| 49 | 3305834 | 2026-09-26 | v036: bozkurt figürü B3 — yele tek oyma kütle, patinalı bronz, malzeme sınırı temizliği |
| 50 | 8506214 | 2026-09-26 | v037: faset temizliği 2. tur — çanaklıklar, halat dönüşleri, seçici Catmull-Clark (23 → 3 nesne) |
| 51 | 2a4cb56 | 2026-09-26 | v038 hazırlık: kanvas dokusu (T_Sail_Canvas_B), yelken pass betiği, LOD gizli nesne matris düzeltmesi |
| 52 | 91439e0 | 2026-09-26 | v038: açık yelkenler B — dolgun karın, kıvrımlar, kenar halatı, camadan, kanvas dokusu, yıpranma |
| 53 | 2bd10bb | 2026-09-26 | Meshy pruva figürü |
| 54 | d30d499 | 2026-09-26 | Meshy pruva figürü |
| 55 | c1c6c14 | 2026-09-26 | v039: bozkurt figürü C — kullanıcının Meshy AI modeli (250k üçgen, 4K dokular), pruvaya yerleştirildi |
| 56 | aaf0492 | 2026-09-26 | Figür C dokuları: uzantıyla uyumlu gerçek PNG (Meshy gömülü JPEG'di) |
| 57 | 903f765 | 2026-09-26 | Kızıl Sancak uyarlama planı (taslak, Gate A onayı bekliyor) |
| 58 | 01a2511 | 2026-09-26 | v040: Kızıl Sancak dış kimliği — konsept arması, sancak/flandra, kızıl bant, kıç arması, top mührü, ad levhası |
| 59 | 26e7277 | 2026-09-26 | v041: iç düzen 1 — kıç kamarası: CaptainOffice (makam) + kaptan kamarası + çırak rıhtımı, bölmeler, oda kimlikleri |
| 60 | 82f5cfa | 2026-09-26 | v042: kıç topları kaldırıldı (20+2), çırak yatakhanesi ayrı bölmede, alt güverte yaşamı (hamak, sofra, subay odası, revir, atölyeler, ocak, su, tuvalet) |
| 61 | 1a5bfca | 2026-09-26 | v043: ambar — kurşun kaplı cephanelik, fener odası, hazırlama odası (ıslak perde), erzak odası, gülle dolapları, ambar hasar kontrol istasyonu, oda kimlikleri |
| 62 | 54a8086 | 2026-09-26 | Yeni kurt figürü |
| 63 | 3457d6c | 2026-09-26 | v044 betiği + lod_store: LOD'lar ayrı _LOD.blend dosyasında (GitHub 100 MB sınırı); Tersane skill günlüğü v038–v044 |
| 64 | 6390d67 | 2026-09-26 | Add Kurt Gemi Figürü model |
| 65 | b5b07a6 | 2026-09-26 | Yerel çalışma güncellemeleri |
| 66 | 6aef00c | 2026-09-26 | v044: top güvertesi hazır servis dolapları (8), güverte başına hasar kontrol istasyonları, rüzgâr hortumu, oda kimlikleri; LOD'lar ayrı _LOD.blend |
| 67 | aeb68b6 | 2026-09-26 | Yerel çalışma güncellemeleri |
| 68 | 3eac419 | 2026-09-26 | Merge branch 'claude/amazing-meitner-keq46t' of https://github.com/actionready88-a11y/Main into claude/amazing-meitner-keq46t # Please enter a commit message to explain why this merge is necessary, # especially if it merges an updated upstream into a topic branch. # # Lines starting with '#' will be ignored, and an empty message aborts # the commit. |
| 69 | 36efdfd | 2026-09-26 | Merge remote-tracking branch 'origin/claude/amazing-meitner-keq46t' into claude/amazing-meitner-keq46t |
| 70 | cc61338 | 2026-09-26 | lod_store: doku yolları göreli kaydedilir (mutlak bulut yolu kullanıcıda pembe malzeme veriyordu) |
| 71 | cab2491 | 2026-09-26 | v045 betikleri: Kurt figürü — ay-yıldızdaki yıldızlar silinir (alın + iki omuz, hilal kalır), bordaya gömülü yerleşim |
| 72 | d7c4d3f | 2026-09-26 | v045: pruva figürü D — Kurt Gemi Figürü (ay-yıldızdan yıldızlar silindi, hilal kaldı), baş kıvrımı kaldırıldı, bodoslamaya gömülü; doku yolları göreli |
| 73 | dcdf6b9 | 2026-09-26 | v046: pruva mahmuzu (ram) + figür yuvası, baş parmaklıkları (çubuklar) kaldırıldı, SOCKET_RAM burna taşındı |
