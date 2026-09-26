# OSMANLI FRIGATE — Araştırma Briefi

Bu dosya `OTTOMAN_FRIGATE_1700_ISTANBUL` üretiminin **Gate A** öncesi
tarihsel araştırma görevidir. Görevin model üretmek DEĞİL, doğru gemiyi
tanımlamaktır.

## Kapsam

17. yüzyıl Osmanlı donanmasında bir **frigate (kırk iki gemi / kırk iki
galliot sinifi)** tipi savaş gemisi. 16. yüzyıl güneş batımı esintileri
(osmanlı denizciliğinin İspanyol-Osmanlı savaşları dönemi) ve 18. yüzyıl
sonu esintileri olabilir — hangi yıl aralığına oturduğunu **sen** araştır
ve gerekçelendir.

`C:\Users\Murat\Desktop\Ships\_meta\GEMI_SINIFLARI_URETIM_KATALOGU.md`
dosyasını önce oku: bu katalog Osmanlı adayları içeriyor. Sonucu ondan
bağımsız doğrula, katalogla çelişirse kaynakla belgelenmiş tarafı seç ve
çelişkiyi `uncertainties` altına yaz.

## Zorunlu cevaplar

1. **Gemi adı ve tipi.** Osmanlı terminolojisinde bu sınıfın adı ne?
   (kırk iki gemi, kırk iki galliot, vs.) Somut bir örnek kayıt ismi ver.
2. **Donanma bağlamı.** 16.-18. yy Osmanlı savaş gemileri sınıfları:
   kayık/kalabra, kıç gemi, kadırga, galiont, kürk, firkate. Bu "frigate"
   hangisinin altında, hangisiyle karışmamalı?
3. **Ritim (mast → sail → yard).** Kaç direk, hangi yelken tipleri?
   Osmanlı gemilerinin kendine özgü yelken donanımı var mı (ör. geniş
   kenarlı üçgen "sandal"/"miskal" yelkenleri, sivri burun, Balıkçı
   biçimli burun yelkeni)? Lateen ne zaman, hangi sınıfta?
4. **Silüet ayırt edicileri.** Bir Osmanlı savaş gemisini bir Venedik
   kadırgasından ilk bakışta ayıran 3-5 geometrik özellik. Bunlar
   referans görsel doğrulamasında kullanılacak.
5. **Boyutlar.** Seçtiğin yıla ait tipik bir sınıf için metre cinsinden
   LOA, beam, draft, direk yüksekliği, top sayısı ve top çapını **kaynakla**
   ver. Tahmin ile kaynak arasındaki farkı belirt.
6. **Top dizilişi.** Batı tipi tek sıra borda (full broadside) mı, yoksa
   burun/kıç kalonları üzerine daha farklı mı yerleşiyordu?
7. **Şekil/ornament.** Sancak, flama, kıç lambası, figür başı, gövde
   boyası (Osmanlı gemilerde tipik renk ve süsleme), kıç galerisi.
8. **En az 3 güvenilir kaynak.** Tercih sırası: akademik (Atlantis, Isis
   Ottoman Studies, Cambridge History of Turkey), İBB/İstanbul
   Denizciler Odası, Deniz Müzesi katalogları, ardından Çelikyal ve
 Bostan'ın Osmanlı denizcilik çalışmaları. Blog/Türkçe hobby
   siteleri kanıt değildir — ancak birincil kaynağa götürüyorsa
   ikincil olarak listelenebilir.

## Yapma

- Gemi **modelleme**. Bu görev tamamen araştırma ve spec yazımı.
- Web'de erişemediğin bir kaynağı varmış gibi yazma. Erişemediysen
  `uncertainties` altına "erişilemedi" diye kaydet.
- 19. yüzyıl ve sonrası gemileri referans alma (yanlış çağ).

## Çıktı

Tek dosya: `C:\Users\Murat\Desktop\Ships\OTTOMAN_FRIGATE_1700_ISTANBUL\reports\research_brief.md`

Yapısı:
```markdown
# Osmanlı Frigate — Tarihsel Araştırma Özeti

## Seçim ve gerekçe
## Silüet ayırt edicileri (3-5, ölçülebilir)
## Donanma tablosu (mast / sail / yard / halat)
## Boyut tablosu (metre, kaynak sütunuyla)
## Top dizilişi
## Görsel kimlik (renk, sancak, figür başi, kıç)
## Kaynaklar (tam referans + URL + erişim durumu)
## Belirsizlikler (ne bilinmiyor, hangi noktada tahmin yaptın)
```

Ayrıca `ship_spec.yaml` dosyasını bu bulgularla doldur:
`identity`, `historical_basis` (period, primary_sources,
secondary_sources, uncertainties), `dimensions_m`. `approved_draft`
değerini **ölçülebilir** bir değere çek, uydurma sayı yazma — kaynak
veremiyorsan `null` bırak ve belirsizliklere yaz.
