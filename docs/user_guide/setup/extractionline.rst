Extraction Line
===================

1. Edit ``Pychron/setupfiles/extractionline/valves.xml``. This file defines the valves used in the
extraction line. The name and location of the valves file is configurable via Preferences/Extraction Line.
Both .xml and .yaml file formats are supported
2. Edit ``Pychron/setupfiles/canvas2D/canvas.xml``. This file defines the positions of various extraction line elements, namely valves
3. Edit ``Pychron/setupfiles/canvas2D/canvas_config.xml``. Defines some global aspects of the main canvas

Example Valves.yaml
=====================

.. code-block:: yaml

    - name: A
      address: Ftkh
      state_device:
        name: foo
        address: bar
        inverted: True
      description: Furnace Turbo
    - name: H
      address: Blep
      interlock:
        - I
      description: Outer pipette
    - name: I
      address: Blop
      interlock: H
      description: Inner pipette
    - name: Air
      kind: pipette
      inner: G
      outer: F
    - name: Cocktail
      kind: pipette
      inner: I
      outer: H


Example Valves.xml
=====================

.. code-block:: xml

    <?xml version='1.0' encoding='ASCII'?>
    <root>
        #Furnace
        <valve>A
            <address>FTkh</address>
            <state_device>foo
                <address>bar</address>
            </state_device>
            <description>Furnace Turbo</description>
        </valve>

      #Ref (Ar)
      <valve>H
          <address>Pipet Ref. Out Set</address>
          <description>Ar Outer</description>
          <interlock>I</interlock>
      </valve>
      <valve>I
          <track>True</track>
          <address>Pipet Ref. In Set</address>
          <description>Ar Inner</description>
          <interlock>H</interlock>
      </valve>

      <switch>J<address>Getter manual 1 Degas Set</address><description>Getter manual 1 Degas</description></switch>


      <manual_valve>T<description>CO2 Inlet</description></manual_valve>
      <manual_valve>U<description>Excimer Inlet</description></manual_valve>
      <manual_valve>ADiode</manual_valve>
      <manual_valve>RDiode</manual_valve>

      <pipette>Air
       <inner>G</inner>
       <outer>F</outer>
      </pipette>
      <pipette>Ar
       <inner>I</inner>
       <outer>H</outer>
      </pipette>
    </root>

