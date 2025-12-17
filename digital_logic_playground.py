import tkinter as tk
from tkinter import ttk, messagebox
import uuid
import math

# -------------------------
# Data Model
# -------------------------

class Wire:
    """Represents a connection from a source element to a target element's pin."""
    def __init__(self, source_id, target_id, target_pin_index):
        self.id = str(uuid.uuid4())
        self.source_id = source_id  # ID of InputNode or Gate
        self.target_id = target_id  # ID of Gate or OutputNode
        self.target_pin_index = target_pin_index # 0 or 1 for gates, 0 for outputs
        self.value = False

class Gate:
    """Represents a logic gate (AND, OR, NOT, XOR)."""
    def __init__(self, gtype, x, y):
        self.id = str(uuid.uuid4())
        self.type = gtype  # "AND", "OR", "NOT", "XOR"
        self.x = x
        self.y = y
        self.num_inputs = 1 if gtype == "NOT" else 2
        self.inputs = [False] * self.num_inputs # Input values, default to False
        self.output = False
        self.width = 80
        self.height = 40
        self.pin_radius = 5

    def get_pin_coords(self, index):
        """Get (x, y) coordinates for a specific input pin."""
        if self.type == "NOT":
            py = self.y + self.height / 2
        else:
            py = self.y + (index + 1) * self.height / (self.num_inputs + 1)
        return (self.x, py)

    def get_output_coords(self):
        """Get (x, y) coordinates for the output pin."""
        return (self.x + self.width, self.y + self.height / 2)

class InputNode:
    """Represents a toggleable input source."""
    def __init__(self, x, y):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.value = False # This is its output value
        self.radius = 12

    def get_output_coords(self):
        """Get (x, y) coordinates for its output."""
        return (self.x, self.y)

class OutputNode:
    """Represents an output probe to display a value."""
    def __init__(self, x, y):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.value = False # This is its input value
        self.radius = 12

    def get_pin_coords(self, index=0):
        """Get (x, y) coordinates for its input."""
        return (self.x, self.y)

# -------------------------
# Main Application
# -------------------------

class LogicPlayground(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digital Logic Playground")
        self.geometry("1100x680")

        # --- Data Model ---
        self.gates = {}
        self.inputs = {}
        self.outputs = {}
        self.wires = {}
        
        # --- UI State ---
        self.elements = {} # Master dict for quick lookup by ID

        # --- Interaction State ---
        self.connect_source_obj = None  # The element (InputNode/Gate) we are connecting FROM
        self.temp_line_id = None      # Canvas ID for the rubber-band wire preview
        
        # Dragging state
        self.drag_target = None       # The Gate object being dragged
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Click vs. Drag detection
        self.click_start_pos = None   # (x, y) tuple on Button-1 press
        self.CLICK_DRAG_THRESHOLD = 3 # Pixels to move before it's a "drag"

        self._build_ui()
        self.redraw() # Initial draw

    def _build_ui(self):
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True)

        # --- Left Panel (Toolbox) ---
        left = ttk.Frame(container, width=220)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        left.pack_propagate(False) # Prevent frame from shrinking

        ttk.Label(left, text="Components", font=("Arial", 12, "bold")).pack(pady=6)
        for label in ["Input", "Output", "AND", "OR", "NOT", "XOR", "NAND", "NOR", "XNOR"]:
            cmd = lambda l=label: self.add_component(l)
            ttk.Button(left, text=f"Add {label}", command=cmd).pack(fill=tk.X, pady=3)

        ttk.Separator(left).pack(fill=tk.X, pady=8)
        ttk.Button(left, text="Evaluate", command=self.evaluate_circuit).pack(fill=tk.X, pady=3)
        ttk.Button(left, text="Clear", command=self.clear_all).pack(fill=tk.X, pady=3)

        ttk.Separator(left).pack(fill=tk.X, pady=8)
        ttk.Label(left, text="How-To Guide:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        tips = [
            "• Click 'Add' buttons to place components.",
            "• Click an Input or Gate to start a wire.",
            "• Click a Gate pin or Output to finish a wire.",
            "• Click an Input (when not wiring) to toggle 0/1.",
            "• Click and drag a Gate's body to move it.",
            "• Click empty space to cancel wiring.",
        ]
        for t in tips:
            ttk.Label(left, text=t, wraplength=200, justify=tk.LEFT).pack(anchor=tk.W, pady=2)

        # --- Canvas ---
        self.canvas = tk.Canvas(container, bg="#FAFAFA", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=8)

        # --- Bindings ---
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_motion)

    # -------------------------
    # Component Management
    # -------------------------

    def add_component(self, kind):
        """Adds a new component to the canvas and data models."""
        x, y = 100, 100 # Default spawn
        if kind == "Input":
            y = 80 + len(self.inputs) * 70
            node = InputNode(x, y)
            self.inputs[node.id] = node
            self.elements[node.id] = node
        elif kind == "Output":
            x = 800
            y = 80 + len(self.outputs) * 70
            node = OutputNode(x, y)
            self.outputs[node.id] = node
            self.elements[node.id] = node
        else: # Gates
            x, y = 350, 100 + len(self.gates) * 80
            g = Gate(kind, x, y)
            self.gates[g.id] = g
            self.elements[g.id] = g
        
        self.evaluate_circuit() # Recalculate and redraw

    def clear_all(self):
        if not messagebox.askyesno("Clear Canvas", "Are you sure you want to clear everything?"):
            return
        
        self.gates.clear()
        self.inputs.clear()
        self.outputs.clear()
        self.wires.clear()
        self.elements.clear()
        
        self.cancel_connection()
        self.drag_target = None
        
        self.redraw()

    # -------------------------
    # Drawing
    # -------------------------

    def redraw(self):
        self.canvas.delete("all")

        # Draw Wires First (Bottom layer)
        for w in self.wires.values():
            self.draw_wire(w)

        # Draw Gates and Nodes
        for g in self.gates.values():
            self.draw_gate(g)
        for n in self.inputs.values():
            self.draw_input(n)
        for o in self.outputs.values():
            self.draw_output(o)

        # Draw Connection Highlight
        if self.connect_source_obj:
            sx, sy = self.connect_source_obj.get_output_coords()
            r = 10
            self.canvas.create_oval(sx - r, sy - r, sx + r, sy + r, 
                                    outline="#FF8800", width=2, dash=(6, 4))

    def draw_gate(self, g):
        x, y = g.x, g.y
        color_lit = "#2ecc71" # Green
        color_dim = "#333333" # Dark Gray
        
        # Body
        self.canvas.create_rectangle(x, y, x + g.width, y + g.height, 
                                     fill="#D9EEFC", outline="#2A7FB8", width=2, 
                                     tags=("gate", g.id, "body"))
        self.canvas.create_text(x + g.width / 2, y + g.height / 2, 
                                text=g.type, font=("Arial", 10, "bold"), 
                                tags=("gate", g.id, "label"))
        
        # Input Pins
        for idx in range(g.num_inputs):
            px, py = g.get_pin_coords(idx)
            r = g.pin_radius
            pin_val = g.inputs[idx]
            self.canvas.create_oval(px - r, py - r, px + r, py + r, 
                                    fill=color_lit if pin_val else "white", 
                                    outline=color_lit if pin_val else color_dim, 
                                    width=2, tags=("gate", g.id, f"pin_in_{idx}"))
        
        # Output Pin
        ox, oy = g.get_output_coords()
        r = g.pin_radius
        self.canvas.create_oval(ox - r, oy - r, ox + r, oy + r, 
                                fill=color_lit if g.output else "white", 
                                outline=color_lit if g.output else color_dim, 
                                width=2, tags=("gate", g.id, "pin_out"))

    def draw_input(self, n):
        x, y, r = n.x, n.y, n.radius
        color = "#2ecc71" if n.value else "#e74c3c" # Green / Red
        self.canvas.create_oval(x - r, y - r, x + r, y + r, 
                                fill=color, outline="#333", width=2, 
                                tags=("input", n.id, "body")) # Added "body" tag
        self.canvas.create_text(x, y, text=str(int(n.value)), 
                                font=("Arial", 10, "bold"), fill="white", 
                                tags=("input", n.id, "label"))

    def draw_output(self, o):
        x, y, r = o.x, o.y, o.radius
        color = "#2ecc71" if o.value else "#95a5a6" # Green / Gray
        self.canvas.create_oval(x - r, y - r, x + r, y + r, 
                                fill=color, outline="#333", width=2, 
                                tags=("output", o.id, "body")) # Added "body" tag
        self.canvas.create_text(x, y, text=str(int(o.value)), 
                                font=("Arial", 10, "bold"), fill="black", 
                                tags=("output", o.id, "label"))

    def draw_wire(self, w):
        src = self.elements.get(w.source_id)
        tgt = self.elements.get(w.target_id)
        if not src or not tgt:
            return # Don't draw if element is missing

        sx, sy = src.get_output_coords()
        tx, ty = tgt.get_pin_coords(w.target_pin_index)
        
        color = "#2ecc71" if w.value else "#333333"
        self.canvas.create_line(sx, sy, tx, ty, fill=color, width=3, 
                                tags=("wire", w.id))
    
    # -------------------------
    # Mouse Event Handlers
    # -------------------------

    def on_press(self, event):
        self.click_start_pos = (event.x, event.y)
        
        # Check for gate drag
        obj, part = self.find_clicked_object(event.x, event.y)
        if isinstance(obj, Gate) and part == "body":
            self.drag_target = obj
            self.drag_start_x = event.x - obj.x
            self.drag_start_y = event.y - obj.y
            return # Don't process clicks if dragging

    def on_drag(self, event):
        # --- Handle Dragging ---
        if self.drag_target:
            # Clear click state
            self.click_start_pos = None 
            
            # Move gate
            self.drag_target.x = event.x - self.drag_start_x
            self.drag_target.y = event.y - self.drag_start_y
            self.redraw()
            return

        if self.click_start_pos: # Check if a click has started
            dist = math.hypot(event.x - self.click_start_pos[0], 
                              event.y - self.click_start_pos[1])
            
            if dist > self.CLICK_DRAG_THRESHOLD:
                # It's a drag! Find out what we're dragging.
                # Find object at the START of the click
                obj, part = self.find_clicked_object(self.click_start_pos[0], self.click_start_pos[1]) 
                
                if part == "body" and isinstance(obj, (InputNode, OutputNode)):
                    # Start dragging this Input/Output node
                    self.drag_target = obj
                    self.drag_start_x = event.x - obj.x
                    self.drag_start_y = event.y - obj.y
                    self.click_start_pos = None # Consume the click
                    self.cancel_connection()    # Cancel any wiring
                    self.redraw()
                    return

        # --- Handle Wiring Preview ---
        if self.connect_source_obj:
            # Clear click state
            self.click_start_pos = None
            
            sx, sy = self.connect_source_obj.get_output_coords()
            if not self.temp_line_id:
                self.temp_line_id = self.canvas.create_line(
                    sx, sy, event.x, event.y, 
                    fill="#FF8800", width=2, dash=(6, 3))
            else:
                self.canvas.coords(self.temp_line_id, sx, sy, event.x, event.y)
            return

    def on_release(self, event):
        # --- End Drag Operation ---
        if self.drag_target:
            self.drag_target = None
            self.evaluate_circuit() # Redraw with final positions
            return

        # --- Handle Click (vs. Drag) ---
        if self.click_start_pos:
            # Check if it was a "click" (mouse didn't move far)
            dist = math.hypot(event.x - self.click_start_pos[0], 
                              event.y - self.click_start_pos[1])
            if dist > self.CLICK_DRAG_THRESHOLD:
                # It was a drag, but not on a target. Cancel.
                self.cancel_connection()
                return
            
            # --- It was a valid CLICK ---
            obj, part = self.find_clicked_object(event.x, event.y)

            # 1. Handle second click (completing a connection)
            if self.connect_source_obj:
                if (isinstance(obj, Gate) and "pin_in" in part) or (isinstance(obj, OutputNode) and part == "body"):
                    # Valid target!
                    pin_index = int(part.split('_')[-1]) if isinstance(obj, Gate) else 0
                    self.add_wire(self.connect_source_obj, obj, pin_index)
                
                # Whether it was valid or not, cancel connection mode
                self.cancel_connection()
                self.evaluate_circuit()
                return

            # 2. Handle toggling an Input
            if isinstance(obj, InputNode) and part == "body":
                obj.value = not obj.value
                self.evaluate_circuit()
                
                # ALSO start a connection from it
                self.connect_source_obj = obj
                self.redraw() # To show highlight
                return

            # 3. Handle starting a new connection from a Gate output
            if isinstance(obj, Gate) and part == "pin_out":
                self.connect_source_obj = obj
                self.redraw() # To show highlight
                return
            
            if obj is None: # Only check for wires if we didn't click a component
                clicked_wire = self.find_clicked_wire(event.x, event.y)
                if clicked_wire:
                    # Confirm deletion
                    if messagebox.askyesno("Delete Wire", "Are you sure you want to delete this wire?"):
                        del self.wires[clicked_wire.id]
                        self.evaluate_circuit()
                    self.cancel_connection() # Always cancel any pending wire
                    return

            # 4. Handle clicking empty space
            if obj is None:
                self.cancel_connection()
                return

    def on_motion(self, event):
        """Handle mouse motion for wire preview when not dragging."""
        if self.connect_source_obj and not self.drag_target:
            sx, sy = self.connect_source_obj.get_output_coords()
            if not self.temp_line_id:
                self.temp_line_id = self.canvas.create_line(
                    sx, sy, event.x, event.y, 
                    fill="#FF8800", width=2, dash=(6, 3))
            else:
                self.canvas.coords(self.temp_line_id, sx, sy, event.x, event.y)

    def cancel_connection(self):
        """Clears any in-progress connection."""
        self.connect_source_obj = None
        if self.temp_line_id:
            self.canvas.delete(self.temp_line_id)
            self.temp_line_id = None
        self.redraw() # Remove highlight

    # -------------------------
    # Helper Functions
    # -------------------------


        
      #  Finds the object (and part) under the cursor.
      #  Returns (object, "part_name") or (None, None).
        
        
        # Check Gates (and their pins)
        for g in self.gates.values():
            # Check body
            if g.x <= x <= g.x + g.width and g.y <= y <= g.y + g.height:
                return (g, "body")
            # Check input pins
            for idx in range(g.num_inputs):
                px, py = g.get_pin_coords(idx)
                if math.hypot(x - px, y - py) <= g.pin_radius + 2:
                    return (g, f"pin_in_{idx}")
            # Check output pin
            ox, oy = g.get_output_coords()
            if math.hypot(x - ox, y - oy) <= g.pin_radius + 2:
                return (g, "pin_out")

        # Check Inputs
        for n in self.inputs.values():
            if math.hypot(x - n.x, y - n.y) <= n.radius + 2:
                return (n, "body")
                
        # Check Outputs
        for o in self.outputs.values():
            if math.hypot(x - o.x, y - o.y) <= o.radius + 2:
                return (o, "body")

        return (None, None)

    def find_clicked_wire(self, x, y):
        """Checks if a click (x, y) is on an existing wire."""
        CLICK_RADIUS = 6 # How close the click must be
        for w in self.wires.values():
            src = self.elements.get(w.source_id)
            tgt = self.elements.get(w.target_id)
            if not src or not tgt:
                continue

            sx, sy = src.get_output_coords()
            tx, ty = tgt.get_pin_coords(w.target_pin_index)

            # Calculate distance from point (x,y) to line segment (sx,sy) -> (tx,ty)
            L_sq = (tx - sx)**2 + (ty - sy)**2 # Squared length of the wire
            if L_sq == 0:
                # Wire is a zero-length "point"
                dist = math.hypot(x - sx, y - sy)
            else:
                # Project point (x,y) onto the infinite line
                # t is the projection factor (0=start, 1=end)
                t = ((x - sx) * (tx - sx) + (y - sy) * (ty - sy)) / L_sq
                
                if t < 0:
                    # Closest point is the start (sx, sy)
                    dist = math.hypot(x - sx, y - sy)
                elif t > 1:
                    # Closest point is the end (tx, ty)
                    dist = math.hypot(x - tx, y - ty)
                else:
                    # Closest point is on the segment
                    proj_x = sx + t * (tx - sx)
                    proj_y = sy + t * (ty - sy)
                    dist = math.hypot(x - proj_x, y - proj_y)
            
            if dist <= CLICK_RADIUS:
                return w # Found a wire

        return None

    # -------------------------
    # Wiring & Evaluation
    # -------------------------

    def add_wire(self, source_obj, target_obj, target_pin_index):
        """Creates and registers a new wire."""
        # Prevent duplicate connections to the *same pin*
        for w in self.wires.values():
            if w.target_id == target_obj.id and \
               w.target_pin_index == target_pin_index:
                print(f"Pin {target_pin_index} on {target_obj.id} is already connected.")
                return 

        w = Wire(source_obj.id, target_obj.id, target_pin_index)
        self.wires[w.id] = w

    def get_element_output_value(self, element_id):
        """Gets the output value (bool) of an element by its ID."""
        if element_id in self.inputs:
            return self.inputs[element_id].value
        if element_id in self.gates:
            return self.gates[element_id].output
        return False

    def evaluate_circuit(self):
        """
        Evaluates the entire circuit logic.
        Uses iteration to allow signals to propagate through layers.
        """
        
        # Iterative evaluation to handle propagation (e.g., A -> NOT -> AND)
        # 10 iterations is more than enough for complex but non-cyclic graphs
        for _ in range(10):
            # Reset all gate inputs to default (False)
            for g in self.gates.values():
                g.inputs = [False] * g.num_inputs
            
            # Reset all output nodes
            for o in self.outputs.values():
                o.value = False

            # --- Pass 1: Set wire values and populate inputs ---
            for w in self.wires.values():
                # Get value from the source element
                src_val = self.get_element_output_value(w.source_id)
                w.value = src_val
                
                # Find the target and set its input value
                target_element = self.elements.get(w.target_id)
                if isinstance(target_element, Gate):
                    # Ensure pin index is valid before assigning
                    if 0 <= w.target_pin_index < len(target_element.inputs):
                        target_element.inputs[w.target_pin_index] = src_val
                elif isinstance(target_element, OutputNode):
                    target_element.value = src_val # Outputs just take the value

            # --- Pass 2: Evaluate all gates ---
            for g in self.gates.values():
                inputs = g.inputs
                if g.type == "AND":
                    g.output = all(inputs)
                elif g.type == "OR":
                    g.output = any(inputs)
                elif g.type == "NOT":
                    g.output = not inputs[0]
                elif g.type == "XOR":
                    g.output = bool(inputs[0]) ^ bool(inputs[1])
                elif g.type == "NAND":
                    g.output = not all(inputs)
                elif g.type == "NOR":
                    g.output = not any(inputs)
                elif g.type == "XNOR":
                    # XNOR is true if inputs are equal
                    g.output = bool(inputs[0]) == bool(inputs[1])
        

        # Wires and Outputs may have changed, so do a final value update
        for w in self.wires.values():
            w.value = self.get_element_output_value(w.source_id)
        for o in self.outputs.values():
            # Check if an output is wired
            is_connected = False
            for w in self.wires.values():
                if w.target_id == o.id:
                    o.value = w.value
                    is_connected = True
                    break
            if not is_connected:
                o.value = False # Default if no wire

        self.redraw()

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    app = LogicPlayground()
    
    # --- Create a pre-wired demo circuit (AND gate) ---
    try:
        # Add components
        app.add_component("Input")
        app.add_component("Input")
        app.add_component("AND")
        app.add_component("Output")
        
        # Get the objects (note: this relies on insertion order)
        in1 = list(app.inputs.values())[0]
        in2 = list(app.inputs.values())[1]
        gate = list(app.gates.values())[0]
        out1 = list(app.outputs.values())[0]
        
        # Manually add wires
        app.add_wire(in1, gate, 0) # Input 1 -> Gate Pin 0
        app.add_wire(in2, gate, 1) # Input 2 -> Gate Pin 1
        app.add_wire(gate, out1, 0) # Gate -> Output
        
        app.evaluate_circuit()
    except Exception as e:
        print(f"Could not build demo circuit: {e}")
        app.clear_all() # Clear partial circuit on error

    app.mainloop()







