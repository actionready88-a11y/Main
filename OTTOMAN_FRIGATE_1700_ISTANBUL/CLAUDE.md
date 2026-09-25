# Osmanlı Gemisi Projesi — Claude Code Talimatı

Bu depo, Murat'ın "Ships" projesindeki tek bir geminin klasörüdür
(yerelde: `Desktop\Ships\OTTOMAN_FRIGATE_1700_ISTANBUL`). Bu Claude Code
oturumunu kullanıcı açıkça istedi (Claude Opus 5.5 denemesi). Tüm çıktılar
Türkçe olacak.

## Başlangıç

1. `reports/ARASTIRMA_GOREVI.md` dosyasını oku ve oradaki görevi uygula.
2. `_context/` altındaki dosyalar ana projenin kurallarından salt okunur
   kopyalardır. Okuyabilirsin, DEĞİŞTİRME.

## Bu oturumda uygulanmayan kurallar

`_context/AGENTS.md`, Hermes'in yerel iş akışı için yazıldı. Aşağıdaki
maddeler bu oturumda uygulanmaz:

- "Harici Codex / Claude Code / OpenCode ajanı kullanma": kullanıcı bu
  oturum için açıkça istisna tanıdı.
- Kanban kartları, `delegate_task`, `computer_use`, yerel Blender 5.2 ve
  `C:\` yolları.

Diğer bütün kurallar geçerli:

- Gate A insan onayı gerektirir; otomatik onay yok.
- Low-poly yasağı.
- Kaynaksız sayı yazılmaz.

## Git

- Çalışmanı kendi branch'inde tut. main'e merge etme, force push yapma.
- İş bitince çıktıları tek commit'te topla ve push et.
