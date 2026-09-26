# OSMANLI "FRIGATE" — Araştırma Görevi (Gate A öncesi)

Rol: Bu gemi üretiminin tarih araştırmacısısın. Bu aşamada Blender/model
YAPMA. Doğru gemiyi tanımla, kaynakla, spec'i doldur ve DUR. Tüm çıktılar
Türkçe olacak.

Not: Bu görev kullanıcının açık isteğiyle Claude Opus 5.5'e verildi.
`_context/AGENTS.md`'deki ajan/dispatch kuralları bu görev için istisnadır
(ayrıntı: `CLAUDE.md`). Diğer bütün kurallar geçerli: Gate A, low-poly
yasağı, klasör koruması.

Tüm yollar depo köküne göredir. Depo kökü = bu geminin klasörü.

## Kullanıcının isteği (aynen)

> "bana bir tane Osmanlı Frigate yapsın gene 16-17 ve 18yy esintileri olsun
> Ozamanın Osmanlı gemilerini araştırsın"

Kullanıcının dönem seçimi (aynen): **"16. yy sonu — İspanyol-Osmanlı
savaşları dönemi"**. Yaklaşık 1560-1590 aralığı; referans olaylar: Cerbe
1560, Malta 1565, İnebahtı 1571, Tunus 1574. Ana sınıf, gövde ve silüet bu
döneme ait olmalı. 17./18. yy yalnızca "esinti": süsleme ve detay katmanıdır,
sınıfı değiştirmez.

## Çözmen gereken ana gerilim — varsayma, kaynakla doğrula

Hipotez (Hermes'in ön bilgisi, doğrulanmadı): 16. yy Osmanlı donanması
ağırlıkla kürekli gemilere dayanıyordu (kadırga, baştarda, kalyata, fırkata;
İnebahtı sonrası mavna). O dönemde "fırkata" büyük olasılıkla küçük, kürekli
bir gemiydi. Üç direkli yelkenli savaş gemisi anlamındaki "firkateyn" ise
18. yy'a aittir.

Bu hipotezi kaynakla doğrula ya da çürüt. Sonra Gate A için İKİ seçenek
hazırla:

- **Seçenek A — döneme sadık:** 16. yy sonu Osmanlı fırkatası. Kaynaklar
  daha uygun olduğunu gösterirse kadırga ya da kalyata öner, gerekçesini yaz.
  Gerçek donanımı, kürek düzeni ve yelkenleriyle.
- **Seçenek B — "frigate" kelimesine sadık:** 16. yy'da Osmanlı donanmasında
  bulunmuş bir YELKENLİ savaş gemisi. Doğrulanacak adaylar: göke (Kemal
  Reis, 1499 Zonchio/Sapienza), barça, kalyon. Anakronizm riskini açıkça
  yaz: dönemde gerçekten var mıydı, hangi kaynak gösteriyor?

Her iki seçenek için destekleyen kaynakları göster. Seçimi kullanıcı yapar;
sen bir öneri sun.

## Önce oku (salt okunur)

- `CLAUDE.md`: bu oturumun kuralları ve istisnaları
- `_context/AGENTS.md`: proje kuralları, Gate A
- `_context/MODULAR_SHIP_STANDARD.md`
- `_context/GEMI_SINIFLARI_URETIM_KATALOGU.md`: Osmanlı adayı varsa kullan.
  Kaynakla çelişen nokta olursa kaynaklı tarafı seç ve çelişkiyi yaz.
- `ship_spec.yaml`

Depo dışına çıkma. Yerelde çalışıyorsan üst klasördeki diğer gemileri OKUMA;
bu görev için gerekmiyorlar.

## Cevaplanacak sorular

1. **Sınıf:** Osmanlıca terim ve Batı karşılığı. Mümkünse somut bir
   tarihsel örnek ver: gemi, kaptan ya da sefer.
2. **Sınıf tablosu (16. yy sonu):** Her sınıf için kürek oturağı (bank)
   sayısı, direk, yelken, top, tayfa ve kürekçi sayısı. Kaynak sütunu zorunlu.
3. **Donanım:** Direk sayısı, yelken tipi ve seren düzeni. Kürek sistemi
   alla sensile mi, a scaloccio mu; hangi yıllarda? Burun savaş platformu
   (rambade) ve kıç köşkü.
4. **Silüet ayırt edicileri:** Aynı dönemin Venedik ve İspanyol
   kadırgalarından ayıran, ölçülebilir 3-5 özellik. Örneğin kıç köşkünün
   biçimi, mahmuz/burun, top yerleşimi, süsleme. Render doğrulamasında
   bunlar kontrol listesi olacak.
5. **Boyutlar (metre):** LOA, beam, draft, fribord, direk yüksekliği, kürek
   sayısı ve uzunluğu, top sayısı ve kalibresi. Her sayıya kaynak ver.
   Kaynağı olmayan değeri "tahmin" diye işaretle.
6. **Top düzeni:** Burun bataryası (merkez top ve yan toplar), kıç ya da
   borda topları; konum ve sayı.
7. **Görsel kimlik:** Gövde rengi ve boyası, kıç köşkü, fenerler, sancak ve
   flamalar. Sancak döneme uygun olsun: ay-yıldızlı kırmızı bayrak büyük
   olasılıkla geç döneme aittir. Tarihini doğrula; 16. yy'a aitse kullan,
   değilse dönemin gerçek sancağını bul.
8. **17./18. yy esintileri:** Sınıfı bozmadan eklenebilecek detaylar
   (süsleme, fener, oyma). Her birine anakronizm notu düş.

## Kaynak kuralları

Başlangıç listesi aşağıda. Künyeleri ve erişimi DOĞRULA, uydurma künye
yazma:

- İdris Bostan: "Kürekli ve Yelkenli Osmanlı Gemileri"; "Osmanlı Bahriye
  Teşkilâtı: XVII. Yüzyılda Tersâne-i Âmire"
- Kâtip Çelebi: "Tuhfetü'l-Kibâr fî Esfâri'l-Bihâr" (1656)
- Pîrî Reis: "Kitâb-ı Bahriye" (gemi tasvirleri)
- Matrakçı Nasuh minyatürleri (1543 Nice/Toulon seferi gemi tasvirleri)
- John F. Guilmartin: "Gunpowder and Galleys"
- Colin Imber: Osmanlı donanması üzerine makaleleri
- İstanbul Deniz Müzesi "Tarihi Kadırga": ayakta kalan tek özgün kadırga
  olarak bilinir. Tarihlendirmesini doğrula. Ölçüleri ve fotoğrafları
  birincil fiziksel kaynaktır.
- Robert Gardiner (ed.): "The Age of the Galley" (Conway)

Kurallar:

- Blog ve hobi siteleri kanıt sayılmaz. Birincil kaynağa götürüyorsa ikincil
  olarak listelenebilir.
- Erişemediğin kaynağı okumuş gibi yazma. "erişilemedi" diye kaydet.
- 403 veya paywall veren bir sayfada iki denemeden sonra ısrar etme. Bütçe
  sınırlı; aynı aramayı tekrarlama.
- 19. yy ve sonrası gemileri (ör. Mahmudiye, Ertuğrul) referans alma.

## Yazma sınırları

- YALNIZ şunlara yaz: `reports/`, `references/`, `ship_spec.yaml`.
- `_context/`, `CLAUDE.md` ve bu dosya salt okunur.
- Depo dışına hiçbir şey yazma. Yerelde çalışıyorsan üst klasördeki diğer
  gemilere, özellikle `WAR_SLOOP_1700_PRIVATEER` ve `XEBEC_1690_ALGIERS`'a
  dokunma.
- Klasör/depo adındaki "1700" geçicidir; Gate A'da seçilen yıla göre
  değiştirilecek. Sen yeniden adlandırma, önerdiğin adı rapora yaz.

## Çıktılar

1. `reports/research_brief.md` şu bölümlerden oluşsun: Seçim ve gerekçe,
   Seçenek A, Seçenek B, Sınıf tablosu, Silüet ayırt edicileri, Donanım,
   Boyut tablosu (kaynak sütunlu), Top düzeni, Görsel kimlik, 17./18. yy
   esintileri, Kaynaklar (tam künye, URL, erişim durumu), Belirsizlikler.
2. `ship_spec.yaml`: `identity`, `historical_basis` ve `dimensions_m`
   alanlarını doldur. Kaynaksız sayı yazma; bilinmeyeni `null` bırak ve
   `uncertainties` altına ekle. `approved_draft: 7.0` şablondan kalma bir
   değer, bu gemi için geçersiz. Kaynaklı bir değer yaz ya da `null` bırak.
3. `references/REFERENCE_SOURCES.md`: Görsel referans olabilecek birincil
   görseller (minyatür, müze fotoğrafı, çizim); her biri için URL ve
   lisans/erişim durumu.
4. `references/GORSEL_PROMPTLARI.md`: Kullanıcının GPT ve Gemini ile
   referans görsel üretmesi için, Seçenek A ve B'nin her biri için 4 açılı
   (baş omzu, borda, kıç omzu, tam kıç) prompt. Promptlar silüet ayırt
   edicilerini açıkça içersin.
5. Son mesajın: Seçenek A ve B için 5'er satırlık özet, önerin ve Gate A'da
   kullanıcıya sorulacak tek soru.

Bulut oturumunda çalışıyorsan: iş bitince tüm çıktıları tek commit'te topla
ve kendi branch'ine push et. main'e merge ETME.

İş bitince DUR. Blender'a GEÇME; kullanıcının Gate A onayı gerekiyor.
