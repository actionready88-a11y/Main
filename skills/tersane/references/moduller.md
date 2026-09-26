# Tersane — Top, figür, iç mekân modülleri

> SKILL.md'nin ayrıntı dosyası. Bölüm numaraları SKILL.md ile aynıdır.

## 12. Top modülü

- Namlu ve kızak ayrı mesh; namlu kızağın çocuğu, pivot muylu ekseni; mesh soketleri MUZZLE / TOUCHHOLE.
- Gerçekçilik için: kaskabel topuz/boyun, taban halkası (ogee), falya astragalı + yastığı, takviye halkaları,
  kovan astragalı, ağız şişkinliği ve dudak, iç namlu; muylu kök bileziği. Kızak: tek parça basamaklı yanak
  profili (kutu yığını değil), muylu yuvası, bombeli tekerler + demir göbek + perno, takoz sapı, muylu kapakları,
  halkalar, cıvata başları. Dökme demir malzemesi (pürüzlülük gürültüsü + hafif pas).
- Varyant paketi (gemide kullanılmayan): ayrı `.blend` + `FBX/Modules/<Aile>/SM_*.fbx` + manifest.

## 13. Figür (heykel)

- **Skin modifier ile prosedürel hayvan/insan figürü oyuncak gibi görünür** (denendi: bozkurt). Blockout olarak işaretle
  (`quality = blockout`), soket/ölçü/malzeme yuvasını hazırla; nihai model için sculpt, AI 3D (ücretli servis — kullanıcı
  onayı) ya da lisanslı hazır varlık öner.

## 14. İç mekân

- Kamara, subay bölmesi, alt güverte, ambar: eşyalar ayrı `InteriorSet` modülleri (orijin zeminde, soketli).
- Yerleşimden önce mürettebat/kovalama topu noktalarını ve gövde sınırını denetle (hull_point − 0,24 iç yüz).
- Yük (fıçı vb.) bütçesi: fıçı ~130 üçgen; 300 fıçı ≈ 60 k. Daha fazlası için UE instanced mesh öner.
- Önizleme ışığı (render-only) ayrı; oyunda UE ışığı — soketlerde `light` notu.

### Figür — tek parça (v034 dersi)
- Oyunda pruva figürü **tek parça** olur ve öyle değişir: parçaları (gövde, kulak, göz, diş, dil) ayrı kur → gövdeye
  değmeyenleri yüzeye en yakın doğrultuda ~8 mm göm → EXACT boolean UNION (material_mode TRANSFER) → ada sayısı = 1 ve
  manifold doğrula; UCX ≤ 64 köşe (nokta örneğini seyrelt).
- Metaball yüzeyi eleman yarıçapının ≈ 0,67'sinde oluşur (threshold 0,6, stiffness 2): yarıçapları buna göre büyüt, gövde
  zincirine köprü elemanları koy. "En büyük adayı tut" adımı kopuk göğsü/kaideyi sessizce atabilir → atılan sayısını raporla.
- Kaide, çevredeki baş parmaklıkları ve baş kıvrımına oturmalı (kalite testi "havada ada" ile doğrula).

### Figür — SDF yontusu (v035 dersi)
- Metaball ile yapılan kurt "oyuncak" göründü; kullanıcı reddetti. `sdf_sculpt.py` ile: temel hacimler (kafatası, burun, çene)
  yumuşak birleşim; oymalar (burun deliği, dudak, kulak içi) yumuşak çıkarma; dişler/göz/dil ayrı malzeme kimliğiyle aynı
  alanda → tek parça. Tüy: tohum → yüzeye yansıt → eşit aralık → akış yönünde uzun, sivri, basık tutam (boy/en ≈ 5).
- Önizleme döngüsü: figürü boş sahnede 3 açıdan 16 örnekle render et (≈ 1 dk), oranları gözle düzelt; 3–5 tur gerekir.
- Uzak alan sabit değer → yüzeye yansıtmada birleşim bölgelerine ≥ 10 cm pay ver; başlangıç noktaları yüzeye yakın.

### Figür — yele ve malzeme (v036 dersi)
- Yuvarlak kesitli ayrı tutamlar + çıkıntıya altın (pointiness) = yakından "solucan" görüntüsü. Çözüm: tutamları yumuşak
  kaynat (k ≈ 0,012, kabarma düşük) → tek oyma kütle; malzemede çukur koyu patina / çıkıntı aşınmış bronz, altın yalnız
  kaide gibi mimari parçada.
- Tutam sırtına oluk çıkarma (subtract) voksel ≤ oluk yarıçapı/2 değilse çukur-delik bırakır; 6 mm vokselde yapma.
- Voksel malzeme kimliği ince parçaların (diş) sınırında tek-yüz tırtık üretir → kenar komşuluğunda çoğunluk süzgeci
  (`wolf_sdf2.clean_mats`).
