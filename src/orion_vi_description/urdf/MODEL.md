# Generowanie modelu
Plik `orion_VI.blend` należy otworzyć w programie Blender z zainstalowanym dodatkiem [LinkForge](https://extensions.blender.org/add-ons/linkforge/?utm_source=blender-5.2.0-lts). Pliki modeli 3D należy wyeksportować do katalogu `meshes`. W wygenerowanym pliku należy do ścieżek modeli 3D dodać `package://orion_vi_description/urdf/`. Ważne jest również zachowanie takich samych nazw członów ( links ) i połączeń ( joints ).

**Uwaga:** Obecnie LinkForge eksportuje pliki glTF z osią Y jako górną, co wymaga ręcznej edycji plików. Dlatego pliki OBJ są obecnie preferowane.
#
Dla laptopów Nvidii trzeba ustawić zmienne przed komendą `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia`