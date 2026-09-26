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
