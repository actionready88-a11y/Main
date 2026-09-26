# Tersane — Arma, yelken, bayrak, motif

> SKILL.md'nin ayrıntı dosyası. Bölüm numaraları SKILL.md ile aynıdır.

## 10. Arma (RigSet) — oranlar TAHMİN (Lees ile doğrula)

- Ana alt direk = (güverte boyu + en)/2; çap yarda başına 1 inç; pruva 8/9 ana; mizana 0,86; gabya 0,6 × alt direk;
  babafingo 0,5 × gabya; ana alt seren 0,56 × güverte boyu; gabya 0,72 × alt; babafingo 0,66 × gabya; cıvadıra
  0,6 × ana direk, eğim ~25°. Yatıklık 0 / 1,5 / 3°.
- Çanaklık: D biçimli tek parça (ışınsal halka ızgara; kareli ızgara tırtıklı görünür), lubber deliği, kıç korkuluğu.
- Seren: ayrı nesne, pivot askıda (brasya dönüşü); altında basamak halatı + üzengiler.
- Sabit arma: kuşak tahtası (küpeşte üst − 0,35), bigotalar + savlo, çarmıhlar (9/9/5), iskalarya 0,40 m, futtock,
  gabya/babafingo çarmıhları, patrisalar, istralyalar. Hareketli arma: kaldırıcı, mandar, brasya → makaralar →
  palanga parmaklığı (fife rail) pinleri; parmaklıkları mürettebat/tulumbadan uzak koy.
- Tüp halatlar: 4–6 dilim; toplam arma ~65 k üçgen (sabit) + ~20 k (hareketli).

## 11. Yelken, bayrak, motif

- Varsayılan **sarılı** (seren üstünde rulo + gasket), açık yelken **gizli varyant** (`sail_state`), UE'de kumaş.
- Motif/decal: yelken yüzeyini izleyen ayrı iki yüzlü mesh + saydam PNG (PIL'de 2× çizip küçült). Modül + soket
  (`SOCKET_SAIL_EMBLEM_*`). Sarılı yelkende desen görünmez — kullanıcıya söyle.
- **Blender içi anahtar şart** (kullanıcı betik çalıştırmadan açıp kapayabilmeli): `CTRL_YELKEN` boşu + `yelken_acik` 0/1
  özelliği, her yelkenin hide_viewport/hide_render'ı basit ifade sürücüsüyle bağlı (Auto Run gerekmez); ayrıca N paneli
  butonu (`use_module` metin bloğu) ve Outliner'da `SAILS_SARILI` / `SAILS_ACIK` alt koleksiyonları. Başka her varyant
  (lumbar kapağı açık/kapalı, bayrak, alt güverte yükseltmesi) için aynı desen.
- Bayrak: dalgalı ızgara (UE kumaş için), orijin gönderde. Kıçta bumba varsa sancak gaf ucundan çekilir.
  Osmanlı donanma sancağı: 1793'te resmî (kırmızı, beyaz hilal + 8 köşeli yıldız) [İKİNCİL] — tarih farkını not et.
