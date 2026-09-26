"""Gemi ölçeği: v007'den itibaren dünya koordinatları = SHIP_SCALE × tasarım uzayı.

build_hull_v001.py ve v002-v006 pass'leri tasarım uzayında (HMS Lyme ölçüsü) çalışır.
v007 pass'i sahneyi bir kez SHIP_SCALE ile ölçekledi (kullanıcı izni 2026-09-26:
"hafiften gemiyi büyütebilirsin"; gerekçe: kasara/kamara altı tavanları 1,88-1,90 m).
Sonraki pass'ler tasarım fonksiyonlarını bu sarmalayıcılarla kullanır: uzunluk çıktıları × K,
uzunluk girdileri ÷ K. Su hattı Z=0 korunur (ölçek orijine göre).
"""

SHIP_SCALE = 1.10


def wrap(H, k=SHIP_SCALE):
    """Tasarım modülü H'nin fonksiyonlarını dünya ölçeğinde döndüren küçük bir ad alanı."""

    class W:
        K = k

        @staticmethod
        def deck_z(s):
            return k * H.deck_z(s)

        @staticmethod
        def top_z(s):
            return k * H.top_z(s)

        @staticmethod
        def stern_x(z):
            return k * H.stern_x(z / k)

        @staticmethod
        def bow_x(z):
            return k * H.bow_x(z / k)

        @staticmethod
        def half_breadth(s, z):
            return k * H.half_breadth(s, z / k)

        @staticmethod
        def hull_point(s, z):
            x, y = H.hull_point(s, z / k)
            return k * x, k * y

    return W
