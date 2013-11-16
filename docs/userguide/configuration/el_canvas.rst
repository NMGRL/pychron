Extraction Line Canvas
=========================

This section describes how to construct and modify an extraction line canvas.

Two files are required to define an extraction line canvas. 

1. ``setupfiles/canvas2D/canvas.xml`` Defines the canvas elements
2. ``setupfiles/canvas2D/canvas_config.xml`` Defines globals parameters e.i origin, bgcolor
3. Optional. ``setupfiles/canvas2D/alt_canvas.xml`` Defines globals for the secondary canvas 
   (Canvas displayed as a pane within a window). Useful for defining a smaller font when
   canvas displayed with Experiment or Spectrometer tasks.
   
Lets construct an example canvas.xml file to see how it works.  

The file starts with the standard ``<root>`` xml tag. All other elements will be children
of ``root``. Various graphical elements can be easily added to the canvas. 
Lets start with a ``stage`` element. ``Stages`` are generic areas that connect multiple 
valves.

.. code-block:: xml

    <root>
        <stage>Bone
           <translation>10,5</translation>
           <dimension>5,2</dimension>
           <color>255,0,0</color>
        </stage>
    </root> 

The above snippet defines a ``stage`` named **"Bone"** that is 5 units wide, 2 units tall and 
positioned 10 units to the right and 5 units above the center of the canvas. The color
of the stage is defined using the color tag and is red in this case- 255,0,0 (R,G,B). By default
the name of the stage is rendered by can be disabled using ``display_name="false"``

.. code-block:: xml

    ...
    <stage display_name="false">Bone
    ...
    
Before we can see what our canvas looks like, we need to make a ``canvas_config.xml`` file.
This file contains X important elements. 

1. origin. Shift the center of the canvas X,Y
2. xview. Left bounds, Right bounds
3. yview. Bottom bounds, Top bounds
4. color tags. default colors for canvas elements

.. code-block:: xml

    <root>
        <origin>0,2.5</origin>
        <xview>-25,25</xview>
        <yview>-22,22</yview>
        <color tag="bgcolor">lightblue</color>
        <color tag="getter">green</color>
        <!-- optional-->
        <font>arial 12</font>
    </root>

The above snippet shifts the canvas up 2.5 units and sets the background color to ``lightblue``.
The default color for ``"getter"`` elements is "green". 
The left bounds of the canvas is -25 and the right 25 (width=50 units). The upper and lower bounds
are -22 and 22 respectively (height=44 units). Optionally the font used for labels can be set using 
a ``font`` tag. 
    

(Note. Defining the canvas is independent of defining hardware connections. Elements 
defined here need not have physical representations)