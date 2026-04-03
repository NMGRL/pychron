# canvas

2D scientific visualization and diagramming system for Pychron. Renders
interactive schematic diagrams of extraction line hardware, sample positions,
and laser ablation targets using the Enthought Tool Suite (Enable/Chaco).

## What This Package Owns

- **Extraction line diagrams** -- Interactive schematic diagrams showing valves,
  switches, pumps, lasers, spectrometers, stages, gauges, getters, and the
  tubing (connections) between them
- **Scene system** -- Layered component model with YAML/XML persistence
- **Primitives** -- Drawable items: points, circles, rectangles, lines, labels,
  polygons, images, valves, switches, and connection/tubing shapes
- **Markup canvases** -- Annotating sample positions on irradiation trays,
  UV masks, laser ablation targets, and furnace stages
- **Calibration canvases** -- Geometric calibration of laser ablation systems
- **Data canvases** -- Chaco-based plot canvases for line plots and colormap images

## Entry Points

The `__init__.py` is empty. Consumers import directly from submodules.

| Import Path | Class | Role |
|---|---|---|
| `canvas2D.scene.scene_canvas.SceneCanvas` | `SceneCanvas` | Main canvas widget that renders scenes |
| `canvas2D.scene.scene.Scene` | `Scene` | Container for layers and overlays |
| `canvas2D.scene.extraction_line_scene.ExtractionLineScene` | `ExtractionLineScene` | Specialized scene for extraction line diagrams |
| `canvas2D.extraction_line_canvas2D.ExtractionLineCanvas2D` | `ExtractionLineCanvas2D` | Interactive extraction line canvas with mouse handling |
| `canvas2D.base_data_canvas.BaseDataCanvas` | `BaseDataCanvas` | Chaco DataView with zoom, pan, axes, coordinate mapping |
| `canvas2D.scene.primitives.base.Primitive` | `Primitive`, `QPrimitive`, `Connectable` | Base classes for all drawable items |
| `canvas2D.scene.layer.Layer` | `Layer` | Z-ordering container with visibility toggle |
| `canvas2D.scene.yaml_scene_loader.YAMLLoader` | `YAMLLoader` | YAML scene file loader |
| `canvas_editor.CanvasEditor` | `CanvasEditor` | Interactive editor for adjusting canvas items |

## Critical Files

```
canvas/
├── canvas_editor.py                    # Interactive reposition/resize editor
├── scene_viewer.py                     # TraitsUI viewer wrappers
├── utils.py                            # Helper functions for holder geometry
├── canvas2D/
│   ├── base_canvas.py                  # Minimal base (Enable Component)
│   ├── base_data_canvas.py             # Chaco DataView (zoom, pan, axes, mapping)
│   ├── scene/
│   │   ├── scene.py                    # Scene: layers, overlays, rendering dispatch
│   │   ├── scene_canvas.py             # Bridges BaseDataCanvas with Scene
│   │   ├── layer.py                    # Named component list with visibility
│   │   ├── extraction_line_scene.py    # Specialized scene with load() and hit-testing
│   │   ├── yaml_scene_loader.py        # YAML file parser → primitives
│   │   ├── xml_scene_loader.py         # Legacy XML loader (deprecated)
│   │   ├── canvas_parser.py            # XML/YAML parser wrapper
│   │   └── primitives/
│   │       ├── base.py                 # Primitive, QPrimitive, Connectable
│   │       ├── primitives.py           # Point, Rectangle, Circle, Line, Label, etc.
│   │       ├── valves.py               # Switch, Valve, RoughValve, ManualSwitch
│   │       ├── connections.py          # Connection, Elbow, Tee, Fork, Cross
│   │       ├── rounded.py              # RoundedRectangle, CircleStage, Spectrometer
│   │       ├── lasers.py               # Laser, CircleLaser
│   │       └── pumps.py                # Turbo, IonPump
│   ├── overlays/
│   │   └── extraction_line_overlay.py  # Info overlay for extraction line
│   └── markup/
│       ├── markup_canvas.py            # Sample position annotation
│       └── markup_items.py             # Markup drawing items
└── canvas2D/tests/
    └── calibration_item.py             # Single test file (rotation math)
```

## Runtime Lifecycle

### Creation and Loading Flow

1. **Canvas creation** -- Application creates a specialized canvas
   (e.g., `ExtractionLineCanvas2D`), which chains through
   `SceneCanvas` → `BaseDataCanvas` → Chaco `DataView`. A default
   `Scene` is created with two layers (`Layer("0")`, `Layer("1")`).

2. **Scene loading** -- `ExtractionLineScene.load()` reads a YAML file:
   - `_load_config()` reads view ranges, valve dimensions, colors, origin
   - `YAMLLoader` instantiates primitives: valves, stages, lasers, pumps
   - Connections are loaded last (they reference components by name)
   - `scene.set_canvas(canvas)` wires the canvas reference to all primitives

3. **Rendering** -- Triggered by `request_redraw()`:
   - `_draw_underlay(gc)` → `scene.render_components(gc, canvas)`
     - Culls off-screen items via `is_in_region(bounds)`
     - Calls `ci.render(gc)` → `Primitive._render(gc)`
   - `_draw_overlay(gc)` → `scene.render_overlays(gc, canvas)`

### Trait Event Chains

```
Primitive property change (x, y, color, state, visible)
  → _refresh_canvas() → request_redraw() → canvas redraw

Scene.layout_needed event
  → SceneCanvas observes → request_redraw()

Connectable x/y change
  → _update_xy() → updates Connection endpoints → request_layout() → request_redraw()
```

### Caching

Primitives cache screen-space position (`_cached_xy`), size (`_cached_wh`),
bounds (`_cached_bounds`), colors (`_cached_colors`), and text extents
(`_cached_text_extent`). The `_layout_needed` flag invalidates caches.

## Test Strategy

**Extremely minimal.** One test file exists:

| Test File | Coverage |
|-----------|----------|
| `canvas2D/tests/calibration_item.py` | `CalibrationObject.calculate_rotation()` (8 tests) |

**Not tested**: canvas creation, scene loading, primitive rendering, YAML/XML
parsing, extraction line interaction, connection wiring, caching invalidation.

## Common Failure Modes

| Failure | Symptom | Where |
|---------|---------|-------|
| `canvas` is `None` | Primitives fail silently or return wrong coordinates | `base.py` |
| Malformed YAML | Incomplete scene (no error raised) | `yaml_scene_loader.py` |
| Connection load order | Broken connections if loaded before components | `extraction_line_scene.py` |
| Stale color cache | Wrong colors if color object mutated after conversion | `base.py` |
| Overflow in coordinate mapping | Caught and ignored | `rounded.py:54` |
| Unknown colormap depth | `RuntimeError` raised | `primitives.py:866` |

**Known fragility points:**
- XML format is deprecated but both loaders still coexist
- No validation on YAML structure -- malformed files silently produce incomplete scenes
- Connection wiring is order-dependent: connectables must be loaded before connections
- Caching invalidation relies on `_layout_needed` propagation; edge cases exist on
  canvas resize/zoom
- `_convert_color()` caches by `id()` -- if a color object is mutated after
  conversion, the cache becomes stale
