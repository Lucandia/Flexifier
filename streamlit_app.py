import subprocess
import plotly
import numpy as np
from stl import mesh  # pip install numpy-stl
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
import os
import time
import base64 # to download from html link

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

def build_hinges(hinges, template):
    union = str()
    difference = str()
    for ind, h in hinges.items():
        union = union + f"""
color("{color[ind-1]}")
translate([{h['h_tran'][0]},{h['h_tran'][1]},0])
rotate([0,0,{h['h_rot']}])
uni_hinge({height}, hinge_h_thick={h['h_thick']}, break={h['h_break']});"""
        difference = difference + f"""
translate([{h['h_tran'][0]},{h['h_tran'][1]},0])
rotate([0,0,{h['h_rot']}])
diff_hinge({height}, hinge_h_thick={h['h_thick']}, break={h['h_break']}, break_len={h['h_break_len']});"""
    return template + difference + '};\n' + union


openscad_template = """
$fn=50;

module uni_hinge(height, hinge_h_thick=5, vert_tolerance=0.8, break=4, hor_tolerance=0.4, chamfer_multi=6){{
chamfer = break/10*chamfer_multi;
hinge_pin_diam = (height-vert_tolerance)/3;
// external hinge
translate([0,0,height/2]) rotate([90,0,0])
linear_extrude(hinge_h_thick)
difference(){{
// external circle
union(){{
circle(d=height);
// squared cornern hing
translate([0,-height/2,0])
square([(hinge_pin_diam+vert_tolerance)/2+chamfer*sqrt(2), height]);}};
// internal hole + tolerance
circle(d=hinge_pin_diam+vert_tolerance);}};
// internal pin
translate([0,hor_tolerance, height/2]) rotate([90,0,0])
cylinder(h=hinge_h_thick+hor_tolerance*2, d=hinge_pin_diam);
}};

module diff_hinge(height, hinge_h_thick=5, hor_tolerance=0.4, vert_tolerance=0.8, break=4, chamfer_multi=6, break_len=200){{
chamfer = break/10*chamfer_multi;
hinge_pin_diam = (height-vert_tolerance)/3;
hinge_v_thick = (height-hinge_pin_diam-vert_tolerance)/2;
// line break
linear_extrude(height)
translate([(hinge_pin_diam+vert_tolerance)/2,-break_len/2-hinge_h_thick/2,0])
square([break/2, break_len]);
//chamfer bottom and top
for (i=[0, height]){{
translate([(hinge_pin_diam+vert_tolerance)/2+break/4,-break_len/2-hinge_h_thick/2,i])
translate([-chamfer*sqrt(2)/2,0,0])
rotate([0, 45, 0])
linear_extrude(chamfer)
square([chamfer, break_len]);}};
// square for difference
translate([-hor_tolerance/2-hinge_v_thick/2,+hor_tolerance,height/2]) rotate([90,0,0])
linear_extrude(hinge_h_thick+hor_tolerance*2)
square([height+hor_tolerance-hinge_v_thick, height], center=true);
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
    if 'hinges' not in st.session_state:
        st.session_state['hinges'] = dict()
    hinges = st.session_state['hinges']
    if hinges and max(list(hinges)) > len(color)-2:
        n_colors = len(hinges)//len(color)
        color = color * (n_colors+2)
    if not hinges: #always start with at least one hinge
        ind = 1
        hinges[ind] = dict()
        hinges[ind]['h_tran'] = [0.0, 0.0]
        hinges[ind]['h_rot'] = 0.0
        hinges[ind]['h_thick'] = 5.0
        hinges[ind]['h_break'] = 3.0
        hinges[ind]['h_break_len'] = 100.0
        st.session_state['hinges'].update(hinges)
        st.experimental_rerun()

    st.title('Flexifier: make it flexi')
    st.write('Generate flexi 3D models from images! You can find more information here [Printables](https://www.printables.com/it/model/505713-flexifier-make-it-flexi).')

    col1, col2, = st.columns(2)
    # Input type 
    with col1:
        filetype = st.selectbox('Choose the file type', ['png', 'jpg', 'svg', 'jpeg'])
    with col2:
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
                scales[0] = scales[0] * st.number_input('X scale %', min_value=0.0, value=100.0) / 100
            with col2:
                scales[1] = scales[1] * st.number_input('Y scale %', min_value=0.0, value=100.0) / 100

        # TRANSLATE
        tran = [0.0, 0.0]
        if translate:
            col1, col2, col3 = st.columns(3)
            with col1:
                tran[0] = st.number_input('Move X', value=0.0)
            with col2:
                tran[1] = st.number_input('Move Y', value=0.0)

        # ROTATE
        rot = 0
        if rotate:
            col1, col2, col3 = st.columns(3)
            with col1:
                rot = st.number_input(' Rotation Angle', value=0.0)

        if numb: height = st.number_input('Model height (mm)', 0.0, 100.0 , 10.0)
        else: height = st.slider('Model height (mm)', 0.0, 100.0 , 10.0)


        def_values = [[0.0, 0.0], 0.0, 5.0, 3.0, 100.0]
        col1, col2, col3 = st.columns(3)
        with col1:
            ref = st.selectbox('Select Hinge', sorted(list(hinges), reverse=True))
        with col2:
            st.write('Add a new hinge')
            if st.button('Add'):
                ind = max(list(hinges)) + 1
                hinges[ind] = dict()
                hinges[ind].update(hinges[ref])
                st.session_state['hinges'].update(hinges)
                #st.experimental_rerun()
        with col3:
            st.write('Remove the selected hinge')
            if st.button('Remove'):
                if ref not in hinges:
                    st.warning(f'Hinge {ref} not found. No hinge removed.', icon="⚠️")
                else:
                    st.session_state['hinges'].pop(ref)
                    if st.session_state['hinges']:
                        ref = sorted(list(st.session_state['hinges']), reverse=True)[0]
                    else:
                        st.experimental_rerun()
        col1, col2, col3 = st.columns(3)
        h_tran = [0.0, 0.0]
        with col1:
            if numb: h_tran[0] = st.number_input('Move X', value=def_values[0][0])
            else: h_tran[0] = st.slider('Move X', -100.0, 100.0, value=def_values[0][0])
        with col2:
            if numb: h_tran[1] = st.number_input('Move Y', value=def_values[0][1])
            else: h_tran[1] = st.slider('Move Y', -100.0, 100.0, value=def_values[0][1])
        with col3:
            if numb: h_rot = st.number_input('Rotate', value=def_values[1])
            else: h_rot = st.slider('Rotate', 0.0, 360.0, value=def_values[1])

        col1, col2, col3 = st.columns(3)
        with col1:
            if numb: h_thick = st.number_input('Hinge thickness', value=def_values[2])
            else: h_thick = st.slider('Hinge thickness', 0.1, 10.0, value=def_values[2])
        with col2:
            if numb: h_break = st.number_input('Image cut thickness', value=def_values[3])
            else: h_break = st.slider('Image cut thickness',  0.1, 10.0, value=def_values[3])
        with col3:
            if numb: h_break_len = st.number_input('Image cut length', value=def_values[4])
            else: h_break_len = st.slider('Image cut length', h_thick, 200.0, value=def_values[4])

        hinges[ref]['h_tran'] = h_tran
        hinges[ref]['h_rot'] = h_rot
        hinges[ref]['h_thick'] = h_thick
        hinges[ref]['h_break'] = h_break
        hinges[ref]['h_break_len'] = h_break_len
        st.session_state['hinges'].update(hinges)
        #PREPARE FILES

        # resize the scale of the svg
        templ = openscad_template.format(HEIGHT=height, X_TRAN=tran[0], Y_TRAN=tran[1], X_SCALE=scales[0], Y_SCALE=scales[1], Z_DEG=rot)
        if st.session_state['hinges']:
            run = build_hinges(st.session_state['hinges'], templ)
        else:
            st.stop
        with open('run.scad', 'w') as f:
            f.write(run)
        preview = False
        if not st.button('Render'):
            preview = True
        if preview:
            subprocess.run('xvfb-run -a openscad -o preview.png --camera 0,0,0,0,0,0,0 --autocenter --viewall --view axes,scales  --projection=ortho run.scad', shell = True)
        else:
            start = time.time()
            # run openscad
            with st.spinner('Rendering in progress...'):
                subprocess.run(f'openscad run.scad -o file.stl', shell = True)
            end = time.time()
            st.success(f'Rendered in {int(end-start)} seconds', icon="✅")

        if preview:
            if 'preview.png' not in os.listdir():
                st.error('OpenScad was not able to generate the preview', icon="🚨")
                st.stop()
            colors_text = 'Preview image:'
            for index in st.session_state['hinges']:
                colors_text += f' <span style="color:{color[index-1]}">Hinge {index},</span>'
            st.markdown(colors_text, unsafe_allow_html=True)
            image = Image.open('preview.png')
            st.image(image, caption='Openscad preview')
            image.close()
        else:
            if 'file.stl' not in os.listdir():
                st.error('OpenScad was not able to generate the mesh', icon="🚨")
                st.stop()
            with open(f"file.stl", "rb") as file:
                html = create_download_link(file.read(), "model")
                st.markdown("Please, put a like [on Printables](https://www.printables.com/it/model/505713-flexifier-make-it-flexi) to support the project!", unsafe_allow_html=True)
                st.markdown("I am a student who enjoys 3D printing and programming. If you want to support me with a coffee, just [click here!](https://www.paypal.com/donate/?hosted_button_id=V4LJ3Z3B3KXRY)", unsafe_allow_html=True)
                st.markdown(html, unsafe_allow_html=True)
            st.write('Interactive mesh preview:')
            st.plotly_chart(figure_mesh(f'file.stl'), use_container_width=True)

