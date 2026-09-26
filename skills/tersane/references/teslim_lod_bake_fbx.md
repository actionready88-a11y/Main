# Tersane — LOD, bake, FBX teslimi

> SKILL.md'nin ayrıntı dosyası. Bölüm numaraları SKILL.md ile aynıdır.

## 15. LOD, bake, export

- LOD (`pass_v026_lods.build_lods`): ≥ 2000 üçgenli benzersiz mesh'ler; modifier yığını uygulanmış kopya → Decimate
  %50/%20 (gövde +%8); `50_LODS`, gizli, `<Kaynak>_LOD<n>`. Paylaşılan mesh bir kez. Geometri değişince yeniden üret.
- Tile bake (`bake_tile_textures.py`): UV'ler metre ölçekli → her prosedürel malzeme 4×4 m düzleme; iki UV
  (`UVMap` metre = active_render, `BakeUV` 0–1 = active); DIFFUSE(COLOR) / ROUGHNESS / NORMAL; ORM paket R=AO G=R B=M;
  normal G ters (DirectX). UE'de UV×0,25. Dünya-Z'ye bağlı ton (su hattı altı) UE'de world position ile.
- FBX: `apply_unit_scale`, `FBX_SCALE_UNITS`, `add_leaf_bones=False`, `use_triangles=True`, `mesh_smooth_type=FACE`;
  her modül ayrı dosya, orijin sokette; export sonrası **temiz sahneye geri yükle** ve ölçek/soket/UCX kontrol et;
  manifestte sha256 + boyut. UE re-import kullanıcı ortamında.
