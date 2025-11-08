# Digital Logic Playground

Digital Logic Playground is an interactive desktop app that simulates basic logic circuits.
Users can place logic gates (AND, OR, NOT, XOR), connect them with virtual wires, toggle inputs, and instantly see output updates in real-time.

The project demonstrates understanding of:
* Logic gate fundamentals
* Event-driven simulation
* GUI programming in Python (Tkinter)
* Object-oriented modeling of digital circuits

---

## Features

| Feature | Description |
| :--- | :--- |
| Add Input | Adds a toggleable input source (0 / 1). Click to flip its value. |
| Add Gates | Add AND, OR, XOR, or NOT gates to the canvas. |
| Add Output | Adds an output probe to display the final logic state (0 or 1). |
| Connect Wires | Click a source (input or gate) → click a target (gate or output) to connect them with a wire. |
| Real-Time Evaluation | Circuit automatically re-evaluates whenever an input changes. |
| Clear Canvas | Resets the workspace — remove all components and connections. |
| Evaluate (optional) | Manual “refresh” button (useful for debugging). |
| Drag-and-Drop | Move gates and nodes freely around the canvas. |

---

## Components Overview

| Component | Description |
| :--- | :--- |
| Input Node | Provides binary values (0/1). Click to toggle. |
| AND Gate | Outputs 1 if **both** inputs are 1. |
| OR Gate | Outputs 1 if **any** input is 1. |
| XOR Gate | Outputs 1 if inputs differ. |
| NOT Gate | Outputs the inverse of its single input. |
| Output Probe | Displays final result (color or label). |
| Wire | Connects outputs to inputs; color represents signal. |

---

## Example Circuit
Here is an example of a full adder circuit built usin this tool using only NAND gates. A full adder circuit adds 2 binary digits together, with a potential carry over from a previous addition stage. Full adders play a crucial role in modern computing, as the ALU (Arithmetic Logic Unit) uses full adder circuits to create addresses in memory and help the Program Counter move to the next instruction.
![Demo of the logic simulator](./example.png)

## How to Run

### Requirements
* Python 3.8+
* No external dependencies (Tkinter is built-in).

### Steps
```bash
# 1. Clone the repository
git clone [https://github.com/yourusername/digital-logic-playground.git](https://github.com/yourusername/digital-logic-playground.git)
cd digital-logic-playground

# 2. Run the app
python digital_logic_playground.py