# Flexifier: make it flexi
A simple interface to generate flexi 3D models from images for 3D printing
Visit the original [Printables page](https://www.printables.com/it/model/505713-flexifier-make-it-flexi)!

## Try the web app:

[Flexifier web app](https://lmonari5-flexifier.streamlit.app/) powered by streamlit

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://lmonari5-flexifier.streamlit.app/)

## Convert png to svg

To convert a png to a svg I suggest using 'vectorize bitmap' on Inkscape. On Linux, you can install the packages imagemagick and potrace, and use the terminal commands:
```
convert YOUR_FILE.png YOUR_FILE.pnm
potrace -s -o YOUR_FILE.svg YOUR_FILE.pnm
rm YOUR_FILE.pnm
```
### Try the OpenScad module:

The generate a hinge in a model from your svg try:
```
difference(){
  linear_extrude(height = HEIGHT) // extrude the svg
    translate(v=[X_TRAN,Y_TRAN,0]) // translate the svg image
      rotate(a=[0,0,Z_DEG]) // rotate the svg image
        scale([X_SCALE,Y_SCALE,1]) // scale the X and Y axis of the svg
            import(file = "YOUR_PATH/YOUR_FILE.svg", center = true);

translate([X_TRAN_HINGE,Y_TRAN_HINGE,0])
rotate([0,0,ROTATE_HINGE])
diff_hinge(HEIGHT_HING, hinge_h_thick=HINGE_THICKNESS, break=CUT_THICKNESS break_len=CUT_LENGTH);
};

translate([X_TRAN_HINGE, Y_TRAN_HINGE,0])
rotate([0,0,ROTATE_HINGE])
uni_hinge(HEIGHT_HING, hinge_h_thick=HINGE_THICKNESS, break=CUT_THICKNESS);
```
Replacing the capital variables with your values

## Donate

I enjoy working on this project in my free time, if you want to support me with a coffee just [click here!](https://www.paypal.com/donate/?hosted_button_id=V4LJ3Z3B3KXRY)

## License

Code is licensed under the GNU General Public License v3.0 ([GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.en.html))

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%20v3-lightgrey.svg)](https://www.gnu.org/licenses/gpl-3.0.en.html)

Models are licensed under the Creative Commons Non Commercial Share Alike License 4.0 ([CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/))

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-sa/4.0/)
