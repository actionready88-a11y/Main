# Referans Görsel Promptları (GPT ve Gemini)

**Kullanım:** Her prompt tek başına kopyalanıp yapıştırılabilir. Aynı seçeneğin dört açısını aynı sohbette sırayla üret; tutarlılık için ilk görseli sonraki promptlara referans olarak ekle.
**Oran:** Borda için 16:9, diğer açılar için 4:3 önerilir.
**Tarihsel kaynak:** `reports/research_brief.md`, bölüm §6 (silüet listesi S1-S5), §9 (görsel kimlik) ve §11 (konsept harmanı).
**Kaynaksız öğeler:** Gövde rengi ve kıç tendası stil tercihidir.

Her prompta eklenecek ortak negatif satır:
> Kullanma: demir zırh plakası, ay-yıldızlı bayrak, yıldız motifi, logo, filigran, yazı, buhar bacası, 18. yy firkateyn arması, low-poly ya da çizgi film stili.

## NİHAİ HARMAN: ChatGPT + Gemini + tarih (brief §17.4)

**Kullanım:** `HIBRIT_CHATGPT_03.webp` (profil) ve `HIBRIT_GEMINI_02.webp` (süsleme) görsellerini referans olarak ekle, sonra promptu yapıştır.

### H5. Nihai konsept sayfası
> Referanslardaki gemiyi birleştir: gövde oranı ve direk düzeni ilk referanstan, süsleme karakteri ikinci referanstan gelsin. Yaklaşık 1700 yılına ait bir Osmanlı kalyonu, boyu 42 metre, eni 13,6 metre. Üç direk: ön ve ana direkte kare yelkenler ve gabya yelkenleri, mizana direğinde latin yelken, bowsprit altında kare cıvadıra yelkeni. Bowsprit üzerinde üçgen flok yelkeni YOK. Baş figürü: yaldızlı lale-palmet oyma çerçeve içinde beyaz bir at başı. Burunda üç kovalama topu. Borda boyunca kırmızı kapaklı top lumbarları. Katranlı, koyu kırmızı-kahve ahşap gövde; küpeşte boyunca geniş kırmızı kuşak ve sarı-altın silmeler; ölçülü yaldız, ağır Barok süsleme yok. Kıç aynasında yaldızlı güneş motifi ve kafesli pencereler; kıçta tek büyük pirinç fener. Kıç gönderinde yıldızsız kırmızı ipek sancak; ana direk tepesinde çatal uçlu yeşil filandıra. Görünümler: baştan, kıçtan, iskele profili, sancak profili; gri arka plan; ayrıntılı, gerçekçi malzemeler.
> Kullanma: demir zırh plakası, ay-yıldız, yıldız motifi, logo, filigran, yazı, etiket, flok yelkeni, insan figürlü baş heykeli.

**Varyantlar:**
- **İki sıra lumbar (tarihe daha uygun):** "Borda boyunca kırmızı kapaklı top lumbarları" cümlesi yerine "iki sıra halinde kırmızı kapaklı top lumbarları" yaz.
- **Amiral varyantı:** Fener cümlesi yerine "kıçta üç büyük pirinç fener" yaz.

---

## GÜNCEL: Hibrit frigate (Gemini için, 2026-09-25)

**Kullanım:** Kullanıcı konseptini (`KULLANICI_KONSEPT_ottoman_armored_frigate.webp`) Gemini'ye referans görsel olarak ekle, sonra promptu yapıştır. Aşağıdaki promptlar varsayılan zırhsız hali ve dönem sancağını üretir.
- **Zırhlı modül varyantı için** son cümleyi şununla değiştir: "Su hattına yakın alt gövdede perçinli, yıpranmış demir zırh plakaları."
- **Ay-yıldızlı bayrak varyantı için** bayrak cümlesini şununla değiştir: "kırmızı zemin üzerinde beyaz hilal ve yıldız."

### H0. Konsept sayfası (4 görünüm)
> Referans görseldeki konsept sayfası düzeninde yeni bir sayfa: baştan görünüm, kıçtan görünüm, iskele profili, sancak profili. Osmanlı esintili üç direkli savaş gemisi (hibrit frigate), boyu yaklaşık 38 metre. Ön ve ana direkte kare yelkenler, mizana direğinde latin yelken. Yüksek, oymalı kıç kasarası; kafesli kıç pencereleri; kıç aynasında tek büyük pirinç fener. Baş bodoslamasının tepesinde yaldızlı lale-palmet oyması. Burunda üç kovalama topu (bir merkez, iki yan). Tek sıra borda top lumbarı. Koyu, yıpranmış, katranlı meşe gövde; küpeşte boyunca kırmızı-altın bordür şeritleri ve Osmanlı rumî-palmet süslemeleri. Tek görselde kullanıcı konseptiyle aynı gemi ve aynı stil: ayrıntılı dijital konsept çizimi, gri arka plan. Bayrak: yıldızsız kırmızı sancak ve yeşil kumandan flaması. Zırh plakası YOK, logo YOK, yazı YOK.

### H1. Baş omzu
> Sancak baş omzundan 3/4 açıyla, göz hizasından görünüm. Osmanlı esintili üç direkli savaş gemisi (hibrit frigate), boyu yaklaşık 38 metre. Ön ve ana direkte kare yelkenler, mizana direğinde latin yelken. Yüksek, oymalı kıç kasarası; kafesli kıç pencereleri; kıç aynasında tek büyük pirinç fener. Baş bodoslamasının tepesinde yaldızlı lale-palmet oyması. Burunda üç kovalama topu (bir merkez, iki yan). Tek sıra borda top lumbarı. Koyu, yıpranmış, katranlı meşe gövde; küpeşte boyunca kırmızı-altın bordür şeritleri ve Osmanlı rumî-palmet süslemeleri. Tek görselde kullanıcı konseptiyle aynı gemi ve aynı stil: ayrıntılı dijital konsept çizimi, gri arka plan. Burundaki üç top ve lale oyması net görünsün. Bayrak: yıldızsız kırmızı sancak ve yeşil kumandan flaması. Zırh plakası YOK, logo YOK, yazı YOK.

### H2. Borda
> Tam iskele profili, ortografik yakın kamera, gemi kadrajda tam görünüyor. Osmanlı esintili üç direkli savaş gemisi (hibrit frigate), boyu yaklaşık 38 metre. Ön ve ana direkte kare yelkenler, mizana direğinde latin yelken. Yüksek, oymalı kıç kasarası; kafesli kıç pencereleri; kıç aynasında tek büyük pirinç fener. Baş bodoslamasının tepesinde yaldızlı lale-palmet oyması. Burunda üç kovalama topu (bir merkez, iki yan). Tek sıra borda top lumbarı. Koyu, yıpranmış, katranlı meşe gövde; küpeşte boyunca kırmızı-altın bordür şeritleri ve Osmanlı rumî-palmet süslemeleri. Tek görselde kullanıcı konseptiyle aynı gemi ve aynı stil: ayrıntılı dijital konsept çizimi, gri arka plan. Üç direğin yelken planı ve tek sıra top lumbarı net görünsün. Bayrak: yıldızsız kırmızı sancak ve yeşil kumandan flaması. Zırh plakası YOK, logo YOK, yazı YOK.

### H3. Kıç omzu
> İskele kıç omzundan 3/4 açıyla görünüm. Osmanlı esintili üç direkli savaş gemisi (hibrit frigate), boyu yaklaşık 38 metre. Ön ve ana direkte kare yelkenler, mizana direğinde latin yelken. Yüksek, oymalı kıç kasarası; kafesli kıç pencereleri; kıç aynasında tek büyük pirinç fener. Baş bodoslamasının tepesinde yaldızlı lale-palmet oyması. Burunda üç kovalama topu (bir merkez, iki yan). Tek sıra borda top lumbarı. Koyu, yıpranmış, katranlı meşe gövde; küpeşte boyunca kırmızı-altın bordür şeritleri ve Osmanlı rumî-palmet süslemeleri. Tek görselde kullanıcı konseptiyle aynı gemi ve aynı stil: ayrıntılı dijital konsept çizimi, gri arka plan. Oymalı kıç kasarası, kafesli pencereler ve fener ön planda. Bayrak: yıldızsız kırmızı sancak ve yeşil kumandan flaması. Zırh plakası YOK, logo YOK, yazı YOK.

### H4. Tam kıç
> Tam arkadan simetrik görünüm. Osmanlı esintili üç direkli savaş gemisi (hibrit frigate), boyu yaklaşık 38 metre. Ön ve ana direkte kare yelkenler, mizana direğinde latin yelken. Yüksek, oymalı kıç kasarası; kafesli kıç pencereleri; kıç aynasında tek büyük pirinç fener. Baş bodoslamasının tepesinde yaldızlı lale-palmet oyması. Burunda üç kovalama topu (bir merkez, iki yan). Tek sıra borda top lumbarı. Koyu, yıpranmış, katranlı meşe gövde; küpeşte boyunca kırmızı-altın bordür şeritleri ve Osmanlı rumî-palmet süslemeleri. Tek görselde kullanıcı konseptiyle aynı gemi ve aynı stil: ayrıntılı dijital konsept çizimi, gri arka plan. Kıç aynası süslemesi, fener ve dümen palası ortada. Bayrak: yıldızsız kırmızı sancak ve yeşil kumandan flaması. Zırh plakası YOK, logo YOK, yazı YOK.

**Hibrit kontrol listesi:**
- 3 direk: kare ön ve ana, latin mizana.
- Yüksek oymalı kıç ve fener.
- Lale-palmet baş süsü.
- Burunda 3 top.
- Varsayılan halde zırh yok.
- Bayrakta yıldız yok (varyant hariç).
- Logo yok.

---

> **Arşiv (Seçenek A ve B):** Aşağıdaki promptlar hibrit yön seçilmeden önceki tarihsel seçeneklere aittir.

## Seçenek A: Osmanlı kadırgası, 1572 (25 oturak)

> **Güncelleme (2026-09-25):** Kullanıcı "kürekleri olmasın" dedi. Aşağıdaki promptlarda "25 uzun kürek … suya inmiş" gibi ifadeleri şu cümleyle değiştir: "Kürekler tamamen içeri alınmış, hiç kürek görünmüyor; yalnız boş kürek kirişi (apostis) ve boş ıskarmozlar var; gemi yelken altında."
> Deneyim notu: Görüntü modelleri kadırgaya kendiliğinden kürek ekliyor. Bayrağa da yıldız ve haç ekliyor. Promptu kısa tutmak ve ana konsept (`KONSEPT_A_kadirga_kureksiz_v002a.png`) görselini referans olarak vermek en iyi sonucu verdi.

### A1. Baş omzu (sancak baş omzu, 3/4 önden)
> Fotogerçekçi tarihsel gemi referansı. 1572 yılına ait bir Osmanlı savaş kadırgası, sakin Akdeniz suyunda, sancak baş omzundan 3/4 açıyla, göz hizasından görülüyor. Uzun, dar, alçak gövde; fribord su seviyesine çok yakın. Omurgaya dik inen düz bir baş bodoslaması ve önünde demir uçlu uzun bir mahmuz var. Baş tarafta Batı tipi yüksek savaş platformu yok. Onun yerine halatla çevrili, alçak, küçük bir yarım güverte var. Burunda tam olarak ÜÇ top bulunuyor: merkez hatta büyük bir bronz top ve iki yanında birer küçük top. Her yanda 25 oturak ve her oturakta tek, uzun kürek var (a scaloccio); kürekler suya inmiş. İki direk var, direkler öne yatık. Latin serenlerde krem rengi keten yelkenler sarılı. Koyu, yıpranmış, katranlı meşe gövde. Küpeşte boyunca ince kırmızı-altın bordür şeridi var; mahmuz ucunda lale biçimli yaldızlı bir topuz. Ana direkte yıldızsız kırmızı ya da kırmızı-sarı yatay çizgili sancak dalgalanıyor. Öğle ışığı, net ayrıntı, müze maketi değil gerçek gemi.
> Kullanma: demir zırh plakası, ay-yıldızlı bayrak, yıldız motifi, logo, filigran, yazı, buhar bacası, 18. yy firkateyn arması, low-poly ya da çizgi film stili.

### A2. Borda (tam iskele profili)
> Fotogerçekçi tarihsel gemi referansı. 1572 yılına ait Osmanlı savaş kadırgasının tam iskele profili, ortografik yakın bir kamerayla, gövdenin tamamı kadrajda. Yaklaşık 41-42 metre boyunda, çok uzun ve dar bir gövde. Fribord çok alçak, neredeyse su seviyesinde. Kıç, baştan belirgin biçimde daha yüksek. Tek sıra halinde 25 kürek ağzı ve 25 uzun kürek görünüyor; kürekler bordadan dışarı taşan bir apostis (kürek kirişi) üzerine oturuyor. İki direk (ana direk ve öndeki trinketo), uzun ve eğik latin serenler, sarılı krem yelkenler. Önde demir uçlu mahmuz; baş tarafta halat korkuluklu alçak yarım güverte var, yüksek platform yok. Toplar yalnız burunda: bir merkez top ve iki yan top. Bordada ve kıçta top YOK. Kıçta alçak bir yarım güverte, üzerinde kırmızı-yeşil kumaş gölgelik ve tek bir pirinç fener. Koyu katranlı ahşap, ince kırmızı-altın bordür. Ana direkte yıldızsız kırmızı sancak. Sakin su, net yansımalar.
> Kullanma: demir zırh plakası, ay-yıldızlı bayrak, yıldız motifi, logo, filigran, yazı, buhar bacası, 18. yy firkateyn arması, low-poly ya da çizgi film stili.

### A3. Kıç omzu (iskele kıç omzu, 3/4 arkadan)
> Fotogerçekçi tarihsel gemi referansı. 1572 yılına ait Osmanlı savaş kadırgası, iskele kıç omzundan 3/4 açıyla görülüyor. Kıç, baştan daha yüksek ve arkaya doğru yükselen bir kıç güvertesi var; üzerinde kaptan ve dümenci duruyor. Kıç yarım güvertesinde kırmızı ve yeşil kumaştan yay biçimli bir gölgelik, kıç bodoslamasının tepesinde tek bir pirinç fener. Büyük dümen palası kıç bodoslamasına menteşeli. Gövdenin iki yanında dışa taşan kürek kirişleri (apostis) ve suya inen uzun kürekler; 25 oturaklı kürek düzeni tek sıra halinde uzanıyor. Kıç yüzeyinde sade yaldızlı çiçek kalem işi ve oymalı parmaklık var. Koyu yıpranmış katranlı ahşap. İki direkte latin serenler. Kıçta top yok. Yıldızsız kırmızı-sarı alaca sancak.
> Kullanma: demir zırh plakası, ay-yıldızlı bayrak, yıldız motifi, logo, filigran, yazı, buhar bacası, 18. yy firkateyn arması, low-poly ya da çizgi film stili.

### A4. Tam kıç (düz arkadan)
> Fotogerçekçi tarihsel gemi referansı. 1572 yılına ait Osmanlı savaş kadırgası, tam arkadan simetrik görünüm. Dar gövde kesiti; iki yanda gövdeden belirgin biçimde dışa taşan kürek kirişleri (apostis), gemiye silüette geniş ve alçak bir "T" görünümü veriyor. Kıç güvertesi arkaya doğru yükseliyor. Üzerinde kırmızı-yeşil kumaş gölgelik, tepede tek bir pirinç fener. Merkezde büyük dümen palası. Kıç kaplamasında yaldızlı lale-palmet kalem işi. Arkada iki direk ve latin serenler görünüyor. Su hattı çok alçak. Yıldızsız kırmızı sancak.
> Kullanma: demir zırh plakası, ay-yıldızlı bayrak, yıldız motifi, logo, filigran, yazı, buhar bacası, 18. yy firkateyn arması, low-poly ya da çizgi film stili.

**A kontrol listesi (render doğrulaması):**
- **S1:** Burunda tam 3 top.
- **S2:** Yüksek arrumbada yok.
- **S3:** Çok alçak fribord.
- **S4:** Dikey baş bodoslaması.
- **S5:** Mahmuz var.
- Bordada ve kıçta top yok.
- Bayrakta yıldız yok.

---

## Seçenek B: Osmanlı barçası, yaklaşık 1570 (yelkenli)

**Not:** Barçanın ölçü ve arma ayrıntıları kaynaksızdır. Kaynaklı olanlar yalnız şunlar: 2-3 direk, düz taban, kalyondan küçük. Bu promptlardaki arma planı **tahmin**dir ve kullanıcı konseptinden uyarlanmıştır.

### B1. Baş omzu
> Fotogerçekçi tarihsel gemi referansı. Yaklaşık 1570 yılına ait, orta boy bir Osmanlı barçası: düz tabanlı, üç direkli, silahlı bir yelkenli nakliye ve eskort gemisi. Sancak baş omzundan 3/4 açıyla görülüyor. Dolgun, geniş gövde; alçak bir baş kasarası. Ön ve ana direkte kare yelkenler, arka direkte latin yelken. Koyu, yıpranmış, katranlı meşe kaplama; kalafat izleri görünüyor. Küpeşte boyunca kırmızı-altın boyalı bordür şeritleri var. Baş bodoslamasının tepesinde yaldızlı lale-palmet oyması. Az sayıda top lumbarı, kapakları kapalı. Direklerde yıldızsız kırmızı, beyaz ve sarı-kırmızı alaca sancaklar. Sakin Akdeniz, öğle ışığı.
> Kullanma: demir zırh plakası, ay-yıldızlı bayrak, yıldız motifi, logo, filigran, yazı, buhar bacası, 18. yy firkateyn arması, low-poly ya da çizgi film stili.

### B2. Borda (tam iskele profili)
> Fotogerçekçi tarihsel gemi referansı. Yaklaşık 1570 yılına ait Osmanlı barçasının tam iskele profili. Üç direk: ön ve ana direkte kare yelkenler, mizana direğinde latin yelken. Düz tabanlı, dolgun gövde; alçak baş kasarası ve baştan belirgin biçimde yüksek, oymalı bir kıç kasarası. Tek sıra halinde az sayıda top lumbarı var; 18. yy firkateyni gibi çift sıra top lumbarı yok. Koyu katranlı ahşap, küpeşte boyunca kırmızı-altın bordür, kıçta tek bir pirinç fener. Yıldızsız kırmızı sancaklar. Kürek yok.
> Kullanma: demir zırh plakası, ay-yıldızlı bayrak, yıldız motifi, logo, filigran, yazı, buhar bacası, 18. yy firkateyn arması, low-poly ya da çizgi film stili.

### B3. Kıç omzu
> Fotogerçekçi tarihsel gemi referansı. Yaklaşık 1570 yılına ait Osmanlı barçası, iskele kıç omzundan 3/4 açıyla görülüyor. Yüksek, oymalı kıç kasarasında yaldızlı Osmanlı rumî-palmet oymaları ve kafesli pencereler var. Kıç aynasında tek bir büyük pirinç fener. Arkada latin yelkenli mizana direği, önde kare yelkenli direkler. Koyu, yıpranmış ahşap; kırmızı-altın bordür şeritleri. Yıldızsız kırmızı sancak.
> Kullanma: demir zırh plakası, ay-yıldızlı bayrak, yıldız motifi, logo, filigran, yazı, buhar bacası, 18. yy firkateyn arması, low-poly ya da çizgi film stili.

### B4. Tam kıç
> Fotogerçekçi tarihsel gemi referansı. Yaklaşık 1570 yılına ait Osmanlı barçası, tam arkadan simetrik görünüm. Dolgun gövde kesiti, düz taban. Yüksek kıç aynası kırmızı-altın oymalı pano ve kafesli pencerelerle süslü; ortada tek bir büyük pirinç fener. Altta dümen palası. Arkasında üç direğin silüeti: kare yelkenler ve latin mizana. Yıldızsız kırmızı sancak. Koyu katranlı ahşap.
> Kullanma: demir zırh plakası, ay-yıldızlı bayrak, yıldız motifi, logo, filigran, yazı, buhar bacası, 18. yy firkateyn arması, low-poly ya da çizgi film stili.

**B kontrol listesi:**
- Kürek yok.
- Tek sıra ve az sayıda top lumbarı.
- Zırh yok.
- Bayrakta yıldız yok.
- Konseptten alınan kırmızı-altın bordür, lale-palmet baş süsü ve kıç feneri korunmuş.
