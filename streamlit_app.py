import subprocess
import plotly
try:
    import cadquery as cq
except: 
    print('Not able to import cadquery')
import numpy as np
from stl import mesh  # pip install numpy-stl
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
import os
import time
import base64 # to download from html link
from math import sqrt
hor_tolerance= 0.4
vert_tolerance= 0.8
chamfer_multi = 1

def create_download_link(val, filename):
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.stl">Download mesh</a>'

def stl2mesh3d(stl_mesh):
    # stl_mesh is read by nympy-stl from an stl file; it is  an array of faces/triangles (i.e. three 3d points)
    # This function extracts the unique vertices and the lists I, J, K to define a Plotly mesh3d
    p, q, r = stl_mesh.vectors.shape #(p, 3, 3)
    # the array stl_mesh.vectors.reshape(p*q, r) can contain multiple copies of the same vertex;
    # extract unique vertices from all mesh triangles
    vertices, ixr = np.unique(stl_mesh.vectors.reshape(p*q, r), return_inverse=True, axis=0)
    I = np.take(ixr, [3*k for k in range(p)])
    J = np.take(ixr, [3*k+1 for k in range(p)])
    K = np.take(ixr, [3*k+2 for k in range(p)])
    return vertices, I, J, K

def figure_mesh(filename):
  my_mesh = mesh.Mesh.from_file(filename)
  vertices, I, J, K = stl2mesh3d(my_mesh)
  x, y, z = vertices.T
  colorscale= [[0, '#e5dee5'], [1, '#e5dee5']]
  mesh3D = go.Mesh3d(
              x=x,
              y=y,
              z=z,
              i=I,
              j=J,
              k=K,
              name='mesh',
              showscale=False,
              colorscale=colorscale, 
              intensity=z,
              flatshading=True,)
  title = "mesh"
  layout = go.Layout(
              paper_bgcolor='rgb(1,1,1)',
              title_text=None,# title_x=0.5, font_color='white',
              width=800,
              height=800,
              scene_camera=dict(eye=dict(x=1.25, y=-1.25, z=1)),
              scene_xaxis_visible=True,
              scene_yaxis_visible=True,
              scene_zaxis_visible=False)
  fig = go.Figure(data=[mesh3D], layout=layout)

  fig.data[0].update(lighting=dict(ambient= 0.18,
                                   diffuse= 1,
                                   fresnel=  .1,
                                   specular= 1,
                                   roughness= .1,
                                   facenormalsepsilon=0))
  fig.data[0].update(lightposition=dict(x=3000,
                                        y=3000,
                                        z=10000));
  fig.update_scenes(aspectmode='data')
  fig.write_html("file_stl.html")
  return fig

def cut_image(h, res):
    chamfer = h['h_break']*chamfer_multi
    # cut image
    cut_im =  cq.Workplane('XY').box(h['h_break'], h['h_break_len'],height,centered=(1,1,0)).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    # chamfer
    chamfer_top = cq.Workplane('XY').box(chamfer, h['h_break_len'],chamfer).rotate([0,0,0], [0,1,0], 45).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    chamfer_bot = cq.Workplane('XY').box(chamfer, h['h_break_len'],chamfer).rotate([0,0,0], [0,1,0], 45).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],height])
    res -= cut_im + chamfer_top + chamfer_bot
    return res

def normal_hinge(h, res):
    ### Diff part
    chamfer = h['h_break']*chamfer_multi
    pin_diam = (h['h_diam']-vert_tolerance)/3
    x_hinge = -h['h_break']/2-pin_diam/2
    res = cut_image(h, res)
    # hinge hole
    hole_h_im_x = (h['h_diam'] + pin_diam)/2 + hor_tolerance
    hole_im = cq.Workplane('XY').box(hole_h_im_x, h['h_thick']+hor_tolerance*2,height,centered=(1,1,0)).translate([-hole_h_im_x/2-h['h_break']/2,0,0]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    res -= hole_im
    ### Uni part
    hole_diam = pin_diam + vert_tolerance
    # hinge corner
    # hinge_corn = cq.Workplane('XZ').box(cq.Workplane('XY').box(hole_h_im_x, h['h_thick']+hor_tolerance*2,height,centered=(1,1,0)).translate([-hole_h_im_x/2-h['h_break']/2,0,0]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])/2 + pin_diam/2+chamfer*sqrt(2),h['h_diam'], h['h_thick'], centered=(0,0,1)).translate([-h['h_break']/2 -pin_diam/2,0,height/2-h['h_diam']/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    hinge_corn = cq.Workplane('XZ').box(hole_h_im_x/2+chamfer*sqrt(2),h['h_diam'], h['h_thick'], centered=(0,0,1)).translate([-h['h_break']/2 -pin_diam/2,0,height/2-h['h_diam']/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    # External hinge
    hinge_ext =  cq.Workplane('XZ').cylinder(h['h_thick'], h['h_diam']/2, centered=(1,0,1)).translate([x_hinge,0,height/2-h['h_diam']/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    hinge_hole =  cq.Workplane('XZ').cylinder(h['h_thick'], hole_diam/2, centered=(1,0,1)).translate([x_hinge,0,height/2-hole_diam/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    hinge_pin =  cq.Workplane('XZ').cylinder(h['h_thick']+hor_tolerance*2, pin_diam/2, centered=(1,0,1)).translate([x_hinge,0,height/2-pin_diam/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    res += hinge_corn + hinge_ext - hinge_hole + hinge_pin
    return res

def ball_joint(h, res):
    res = cut_image(h, res)
    hole_diam = h['h_diam']+vert_tolerance
    ### Diff part
    hole_im1 = cq.Workplane('XY').sphere(hole_diam/2).translate([-h['h_break']/2-hole_diam/2,0,height/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    hole_im2 = cq.Workplane('XY').sphere(hole_diam/2).translate([+h['h_break']/2+hole_diam/2,0,height/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    if h['h_expose']:
        hole_join = cq.Workplane('XY').box(h['h_break']+(h['h_diam']/2+hor_tolerance)*2, h['h_diam']/2+hor_tolerance,height,centered=(1,1,0)).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    else:
        hole_join = cq.Workplane('YZ').cylinder(h['h_break']+h['h_diam'], h['h_diam']/4+hor_tolerance).translate([0,0,height/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    res -= hole_im1 + hole_im2 + hole_join
    ### Uni part
    ball1 = cq.Workplane('XY').sphere(h['h_diam']/2).translate([-h['h_break']/2-hole_diam/2,0,height/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    ball2 = cq.Workplane('XY').sphere(h['h_diam']/2).translate([+h['h_break']/2+hole_diam/2,0,height/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    join = cq.Workplane('YZ').cylinder(h['h_break']+h['h_diam'], h['h_diam']/4).translate([0,0,height/2]).rotate([0,0,0], [0,0,1], h['h_rot']).translate([h['h_tran'][0],h['h_tran'][1],0])
    res += ball1 + ball2 + join
    return res


def build_preview(hinges, template):
    union = str()
    difference = str()
    for ind, h in hinges.items():
        if h['type'] == 'normal':
            union = union + f"""
    color("{color[ind-1]}")
    translate([{h['h_tran'][0]},{h['h_tran'][1]},0])
    rotate([0,0,{h['h_rot']}])
    uni_hinge({height}, hinge_diam={h['h_diam']}, hinge_h_thick={h['h_thick']}, break={h['h_break']});"""
        elif h['type'] == 'ball':
            union = union + f"""
color("{color[ind-1]}")
translate([{h['h_tran'][0]},{h['h_tran'][1]},0])
rotate([0,0,{h['h_rot']}])
uni_ball({height}, ball_diam={h['h_diam']}, break={h['h_break']});"""
        difference = difference + f"""
translate([{h['h_tran'][0]},{h['h_tran'][1]},0])
rotate([0,0,{h['h_rot']}])
diff({height}, break={h['h_break']}, break_len={h['h_break_len']});"""
    return template + difference + '};\n' + union

svg_to_dxf = """
translate(v=[{X_TRAN},{Y_TRAN},0])
  rotate(a=[0,0,{Z_DEG}])
    scale([{X_SCALE},{Y_SCALE},1])
      import(file = "file.svg", center = true);
"""

preview_template = """
$fn=10;

module diff(height, break=4, break_len=200){{
// line break
linear_extrude(height)
square([break, break_len], center=true);
}};

module uni_hinge(height, hinge_diam=5, hinge_h_thick=5, vert_tolerance=0.8, break=4, chamfer_multi=1){{
chamfer = break*chamfer_multi;
pin_diam = (hinge_diam-vert_tolerance)/3;
// external hinge
translate([-break/2-pin_diam/2,hinge_h_thick/2,height/2])
rotate([90,0,0])
linear_extrude(hinge_h_thick)
// external circle
circle(d=hinge_diam);
// squared cornern hing
linear_extrude(hinge_diam)
translate([-(chamfer*sqrt(2)/2-break/2)/2,0,0])
square([break/2+chamfer*sqrt(2)/2, hinge_h_thick], center=true);
}};

module uni_ball(height, ball_diam=5, tolerance=0.4, break=3){{
// internal ball left
translate([-ball_diam/2-break/2, 0, height/2]) sphere(r=ball_diam/2);
// internal ball right
translate([ball_diam/2+break/2, 0, height/2]) sphere(r=ball_diam/2);
// connection cylinder
translate([0, 0,height/2])
rotate([90, 0, 90])
cylinder(h=ball_diam+break,r=ball_diam/4, center=true);
}};

difference(){{
  linear_extrude(height = {HEIGHT})
    translate(v=[{X_TRAN},{Y_TRAN},0])
      rotate(a=[0,0,{Z_DEG}])
        scale([{X_SCALE},{Y_SCALE},1])
          import(file = "file.svg", center = true);
"""

color = ['red', 'navy', 'green', 'purple', 'silver', 'orange', 'indigo', 'teal', 'darkslategray',
    'yellowgreen', 'cyan', 'cornflowerblue', 'magenta', 'tan', 'darkred', 'deeppink', 'olive', 'lightsalmon', 'mocassin', 'rosybrown']

if __name__ == "__main__":
    for key in ('xlen', 'ylen', 'xmin', 'xmax', 'ymin', 'ymax'):
        if key not in st.session_state:
            st.session_state[key] = 0
    if 'hinges' not in st.session_state:
        st.session_state['hinges'] = dict()
    hinges = st.session_state['hinges']
    if 'image_value' not in st.session_state:
        st.session_state['image_value'] = [0]
    if hinges and max(list(hinges)) > len(color)-2:
        n_colors = len(hinges)//len(color)
        color = color * (n_colors+2)

    # clean memory
    for file in ['file.stl', 'preview.png']:
        if file in os.listdir():
            os.remove(file)

    st.title('Flexifier: make it flexi')
    st.write("Generate flexi 3D models from images! If you like the project put a like on [Printables](https://www.printables.com/it/model/505713-flexifier-make-it-flexi) or [support me with a coffee](https://www.paypal.com/donate/?hosted_button_id=V4LJ3Z3B3KXRY)! On Printables you can find more info about the project.", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    # Input type 
    with col1:
        filetype = st.selectbox('Input file type', ['png', 'jpg', 'svg', 'jpeg'])
    with col2:
        out = st.selectbox('Output file type', ['stl', 'step'])
    with col3:
        interface = st.selectbox('Interface', ['slider', 'number'])
    numb = False
    if interface == 'number':
        numb = True
    # Input file
    uploaded_file = st.file_uploader("Upload the file:", type=[filetype])
    if uploaded_file is not None:
        # To read file as bytes:
        bytes_data = uploaded_file.getvalue()
        with open(f'file.{filetype}', 'wb') as f:
            f.write(bytes_data)
        image_value = [bytes_data]

        # calculate the svg if the imgage is different from the previous one
        if image_value[0] != st.session_state['image_value'][0]:
            # avoid transparency in PNG, replace it with white
            if filetype == 'png':
                subprocess.run(f'convert file.{filetype} -background white -alpha remove -alpha off file.{filetype}', shell = True)
            # convert the img to svg
            if filetype != 'svg':
                subprocess.run(f'convert file.{filetype} file.pnm', shell=True)
                subprocess.run(f'potrace -s -o file.svg file.pnm', shell=True)
    
        # MODIFY IMAGE
        col1, col2, col3 = st.columns(3)
        with col1:
            scale = st.checkbox('Rescale image size')
        with col2:
            translate = st.checkbox('Translate the image')
        with col3:
            rotate = st.checkbox('Rotate the image')

        # SCALE
        scales = [0.4, 0.4]
        if scale:
            col1, col2, col3 = st.columns(3)
            with col1:
                if numb: scales[0] = scales[0] * st.number_input('X scale %', min_value=0.0, value=100.0) / 100
                else: scales[0] = scales[0] * st.slider('X scale %', 0.0, 500.0, step=0.1, value=100.0) / 100
            with col2:
                if numb: scales[1] = scales[1] * st.number_input('Y scale %', min_value=0.0, value=100.0) / 100
                else: scales[1] = scales[1] * st.slider('Y scale %', 0.0, 500.0, step=0.1, value=100.0) / 100
        image_value.append(scale)

        # TRANSLATE
        tran = [0.0, 0.0]
        if translate:
            col1, col2, col3 = st.columns(3)
            with col1:
                if numb: tran[0] = st.number_input('Move X', value=0.0)
                else: tran[0] = st.slider('Move X', 0.0, 200.0, step=0.1, value=0.0)
            with col2:
                if numb: tran[1] = st.number_input('Move Y', value=0.0)
                else: tran[1] = st.slider('Move Y', 0.0, 200.0, step=0.1, value=0.0)
        image_value.append(tran)

        # ROTATE
        rot = 0
        if rotate:
            col1, col2, col3 = st.columns(3)
            with col1:
                if numb: rot = st.number_input('Rotation Angle', value=0.0)
                else: rot = st.slider('Rotation Angle', 0.0, 360.0, step=0.1, value=0.0)
        image_value.append(rot)


        if numb: height = st.number_input('Model height (mm)', 0.0, 100.0 , 10.0)
        else: height = st.slider('Model height (mm)', 0.0, 100.0 , 10.0)

        # calculate bounding box only if it's a different image
        if image_value != st.session_state['image_value']:
            try:
                print('CALCOLO DXF')
                # CREATE DXF AND CALCULATE THE BOUNDING BOX
                with open("svg_to_dxf.scad", 'w') as f:
                    f.write(svg_to_dxf.format(X_TRAN=tran[0], Y_TRAN=tran[1], X_SCALE=scales[0], Y_SCALE=scales[1], Z_DEG=rot))
                subprocess.run(f'openscad svg_to_dxf.scad -o file.dxf', shell = True)
                result = (cq.importers.importDXF("file.dxf").wires().toPending().extrude(height))
                b_box = result.combine().objects[0].BoundingBox()
                st.session_state['xlen'] = b_box.xlen
                st.session_state['ylen'] = b_box.ylen
                st.session_state['xmin'] = b_box.xmin
                st.session_state['xmax'] = b_box.xmax
                st.session_state['ymin'] = b_box.ymin
                st.session_state['ymax'] = b_box.ymax
            except:
                st.warning('Not able to calculate the bounding box', icon="⚠️")
                st.session_state['xlen'] = 200.0
                st.session_state['ylen'] = 200.0
                st.session_state['xmin'] = -100.0
                st.session_state['xmax'] = 100.0
                st.session_state['ymin'] = -100.0
                st.session_state['ymax'] = 100.0
        st.session_state['image_value'] = image_value
        xlen = st.session_state['xlen']
        ylen = st.session_state['ylen']
        xmin = st.session_state['xmin']
        xmax = st.session_state['xmax']
        ymin = st.session_state['ymin']
        ymax = st.session_state['ymax']


        def_values = {'h_tran': [0.0, 0.0], 'h_rot': 0.0, 'h_break': 3.0, 'h_break_len': ylen*2,
                      'h_diam': height, 'h_thick': 5.0, 'h_expose': True}

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            ref = st.selectbox('Select Hinge', sorted(list(hinges), reverse=True))
        with col2:
            hinge_type = st.selectbox('Add hinge type:', ['normal', 'ball'])
        with col3:
            st.write('Add hinge')
            if st.button('Add'):
                if not hinges: #always start with at least one hinge
                    ind = 1
                    hinges[ind] = dict()
                    hinges[ind]['type'] = hinge_type
                    hinges[ind]['h_tran'] = [0.0, 0.0]
                    hinges[ind]['h_rot'] = 0.0
                    hinges[ind]['h_break'] = 3.0
                    hinges[ind]['h_break_len'] = 100.0
                    hinges[ind]['h_diam'] = height
                    hinges[ind]['h_thick'] = 5.0
                    hinges[ind]['h_expose'] = True
                    st.session_state['hinges'].update(hinges)
                    st.experimental_rerun()
                else:
                    ind = max(list(hinges)) + 1
                    hinges[ind] = dict()
                    hinges[ind].update(hinges[ref])
                    if hinges[ref]['type'] == 'normal' and hinge_type == 'ball':
                        hinges[ind]['type'] = hinge_type
                    if hinges[ref]['type'] == 'ball' and hinge_type == 'normal':
                        hinges[ind]['type'] = hinge_type
                        hinges[ind]['h_thick'] = 5.0
                    st.session_state['hinges'].update(hinges)
                    #st.experimental_rerun()
        with col4:
            st.write('Remove hinge')
            if st.button('Remove'):
                if ref not in hinges:
                    st.warning(f'Hinge {ref} not found. No hinge removed.', icon="⚠️")
                else:
                    st.session_state['hinges'].pop(ref)
                    if st.session_state['hinges']:
                        ref = sorted(list(st.session_state['hinges']), reverse=True)[0]
                    else:
                        st.experimental_rerun()

        if hinges:
            col1, col2, col3 = st.columns(3)
            h_tran = [0.0, 0.0]
            with col1:
                if numb: h_tran[0] = st.number_input('Move X', value=def_values['h_tran'][0])
                else: h_tran[0] = st.slider('Move X', xmin, xmax, step=0.1, value=def_values['h_tran'][0])
            with col2:
                if numb: h_tran[1] = st.number_input('Move Y', value=def_values['h_tran'][1])
                else: h_tran[1] = st.slider('Move Y', ymin, ymax, step=0.1, value=def_values['h_tran'][1])
            with col3:
                if numb: h_rot = st.number_input('Rotate', value=def_values['h_rot'])
                else: h_rot = st.slider('Rotate', 0.0, 360.0, step=0.1, value=def_values['h_rot'])


            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if hinges[ref]['type'] == 'normal':
                    h_expose = False
                    if numb: h_thick = st.number_input('Hinge thickness', value=def_values['h_thick'])
                    else: h_thick = st.slider('Hinge thickness', 0.1, 20.0, step=0.1, value=def_values['h_thick'])
                else:
                    h_thick = def_values['h_thick']
                    h_expose = st.checkbox('Expose ball joint', value=True)
            with col2:
                if numb: h_diam = st.number_input('Joint external diameter', value=def_values['h_diam'])
                else: h_diam = st.slider('Joint external diameter', 0.1, height, step=0.1, value=def_values['h_diam'])
            with col3:
                if numb: h_break = st.number_input('Image cut thickness', value=def_values['h_break'])
                else: h_break = st.slider('Image cut thickness',  0.1, max([ylen, xlen]), step=0.1, value=def_values['h_break'])
            with col4:
                if numb: h_break_len = st.number_input('Image cut length', value=def_values['h_break_len'])
                else: h_break_len = st.slider('Image cut length', h_thick, sqrt(ylen**2+xlen**2)*2, step=0.1, value=def_values['h_break_len'])

            hinges[ref]['h_tran'] = h_tran
            hinges[ref]['h_rot'] = h_rot
            hinges[ref]['h_thick'] = h_thick
            hinges[ref]['h_expose'] = h_expose
            hinges[ref]['h_diam'] = h_diam
            hinges[ref]['h_break'] = h_break
            hinges[ref]['h_break_len'] = h_break_len
            st.session_state['hinges'].update(hinges)
        #PREPARE FILES
        preview = False
        if not st.button('Render'):
            preview = True
        if preview:
            height_model = height/2
            openscad_template = preview_template
            # resize the scale of the svg
            templ = openscad_template.format(HEIGHT=height_model, X_TRAN=tran[0], Y_TRAN=tran[1], X_SCALE=scales[0], Y_SCALE=scales[1], Z_DEG=rot)
            run = build_preview(st.session_state['hinges'], templ)
            with open('run.scad', 'w') as f:
                f.write(run)
            if preview:
                subprocess.run('xvfb-run -a openscad -o preview.png --camera 0,0,0,0,0,0,0 --autocenter --viewall --view axes,scales  --projection=ortho run.scad', shell = True)
        else:
            start = time.time()
            # run openscad
            with st.spinner('Rendering in progress...'):
                res = cq.importers.importDXF("file.dxf").wires().toPending().extrude(height)
                for h in hinges.values():
                    if h['type'] == 'normal':
                        res = normal_hinge(h, res)
                    else:
                        res = ball_joint(h, res)
                cq.exporters.export(res, f'file.{out}')
            end = time.time()
            st.success(f'Rendered in {int(end-start)} seconds', icon="✅")

        if preview:
            if 'preview.png' not in os.listdir():
                st.error('OpenScad was not able to generate the preview', icon="🚨")
                st.stop()
            colors_text = 'Quick preview:'
            for index in st.session_state['hinges']:
                colors_text = colors_text + f' <span style="color:{color[index-1]}">Hinge {index},</span>'
            st.markdown(colors_text, unsafe_allow_html=True)
            image = Image.open('preview.png')
            st.image(image, caption='Openscad preview')
            image.close()
        else:
            if f'file.{out}' not in os.listdir():
                st.error('The program was not ot able to generate the mesh', icon="🚨")
                st.stop()
            with open(f'file.{out}', "rb") as file:
                btn = st.download_button(
                        label=f"Download {out}",
                        data=file,
                        file_name=f'flexi.{out}',
                        mime=f"model/{out}"
                    )
            #html = create_download_link(file.read(), "model")
            #st.markdown(html, unsafe_allow_html=True)
            #if out=='stl':
                #st.write('Interactive mesh preview:')
                #st.plotly_chart(figure_mesh(f'file.stl'), use_container_width=True)
        st.markdown("Please, put a like [on Printables](https://www.printables.com/it/model/505713-flexifier-make-it-flexi) to support the project!", unsafe_allow_html=True)
        st.markdown("I am a student who enjoys 3D printing and programming. If you want to support me with a coffee, just [click here!](https://www.paypal.com/donate/?hosted_button_id=V4LJ3Z3B3KXRY)", unsafe_allow_html=True)

