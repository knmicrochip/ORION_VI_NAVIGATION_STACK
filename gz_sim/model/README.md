URDF generate:
```
xacro rover_model.xacro -o rover_model.urdf
```
Gazebo simulation run:
```
cd ~/orion-vi-navigation-stack/gz_sim/model/
gz sim mars_yard.world 
```
or:
```
gz sim rover_model.urdf
```