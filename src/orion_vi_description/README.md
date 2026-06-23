URDF generate:
```
xacro rover_model.xacro -o rover_model.urdf
```
Gazebo simulation run:
```
cd ~/orion-vi-navigation-stack/gz_sim/model/
gz sim mars_yard.world 
```
Dla laptopów Nvidii trzeba ustawić zmienne przed komendą `__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia`

or:
```
gz sim rover_model.urdf
```

Aby zobaczyć topiki stworzone w symulacji:
```
gz topic -l
```gz