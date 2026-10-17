# Maa Durga Particle Art

A small Python project that **draws Maa Durga with code** and then **builds her image out of glowing particles** in a cinematic animation.

Made with Python, OpenCV and NumPy.

---

## Files

| File | What it does |
|------|--------------|
| `make_durga.py` | Draws a stylized Maa Durga (eight arms, weapons, crown, lotus, diyas) and saves it as `katyayani.png`. |
| `katyayani.png` | The image the animations use. A ready-made one is included. You can replace it with any picture of your own. |
| `day6.py` | 3D neon version: a spiral galaxy flies in and the particles assemble into the image. Mouse-rotatable camera. |
| `day6_realistic.py` | Realistic version: warm embers, spring physics, light rays, smoke, flickering diyas, film grain. |

---

## Requirements

- Python 3.9 or newer (3.12 is the safest choice)
- OpenCV and NumPy

```
py -m pip install opencv-python numpy
```

---

## Quick start

1. Put all the files in one folder.
2. Open a terminal in that folder.
3. (Optional) Create the image:
   ```
   py make_durga.py
   ```
4. Run an animation:
   ```
   py day6_realistic.py
   ```
   or
   ```
   py day6.py
   ```

---

## Controls

| Key / action | Effect |
|--------------|--------|
| `Esc` | Quit |
| `Space` | Skip to the end |
| Left mouse drag (`day6.py` only) | Rotate the 3D scene |

---

## Settings you can change

Open a script and edit the values near the top.

**Both animations**
- `IMG_PATH`: the picture to build (default `katyayani.png`)
- `N_EDGE`, `N_FILL`: number of particles. Lower these if the animation runs slowly.
- `SAVE_VIDEO = True`: saves the animation as an `.mp4` file

**`day6.py`**
- `RELIEF`: how deep the 3D relief of the image is
- `TOTAL`, `TRIGGER`: animation length, and when the particles start being pulled in

**`day6_realistic.py`**
- `N_AMBIENT`: number of soft floating bokeh embers
- `DIYAS`: positions of the flickering lamp lights (change these if you use a different image)
- `TITLE`: the text shown at the end

**`make_durga.py`**
- Colors are named values at the top (`GOLD`, `RED`, `SKIN`, `PINK`, ...)
- Weapons are in the `ITEMS_R` and `ITEMS_L` lists

---

## Using your own image

1. Save any picture as `katyayani.png` in the project folder.
2. Run an animation script.

Tips for the best result:
- Use a dark or plain background.
- Use a wide image, about 16:9.
- Use a sharp, high-resolution picture so the particles have clear edges.
- Check the image's copyright before sharing videos made from it publicly.

---

## Troubleshooting

**`Python was not found` (Windows)**
Use `py` instead of `python`. To fix `python`, turn off the `python.exe` and `python3.exe` entries under Settings > Apps > Advanced app settings > App execution aliases.

**`No module named 'cv2'`**
```
py -m pip install opencv-python
```

**`pip` cannot find OpenCV for a very new Python version**
Install an older Python and use it for this project:
```
py install 3.12
py -3.12 -m pip install opencv-python numpy
py -3.12 day6_realistic.py
```

**The animation is slow**
Lower `N_EDGE` and `N_FILL` (and `N_AMBIENT` in `day6_realistic.py`), and close other heavy programs.

**`Couldn't find 'katyayani.png'`**
Run `py make_durga.py`, or make sure the image is in the same folder you run the command from.

---

## Notes

- `make_durga.py` creates a stylized illustration, not a photograph. For a photo-like look, use any image you like as `katyayani.png`.
- Jai Maa Durga.