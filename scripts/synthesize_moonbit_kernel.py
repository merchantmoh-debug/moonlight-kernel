# ==============================================================================
# Project Moonlight: Ark Synthesis Engine (V3.1 - Kinetic Realization)
# ==============================================================================
# "Let there be tensors."
#
# This engine synthesizes high-performance MoonBit tensor kernels.
#
# Capability Level: 7 (Real Math, Safe Interface, Ring Buffer, Type-Safe)
# Architect: Ark (Sovereign Mind V2)
# License: Apache 2.0
# ==============================================================================

import os

def get_kernel_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(script_dir, "..", "core", "src", "lib")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
    return os.path.join(target_dir, "kernel.mbt")

def generate_header():
    return """// Project Moonlight: Generated Kernel (V3.1)
// Auto-synthesized by Ark Sovereign Engine
// Target: Wasm-GC / Wasm-Linear

package lib

// --- The Fundamental Truth ---
// "Speed is Safety."

let buffer_size : Int = 65536
let input_buffer : FixedArray[Byte] = FixedArray::make(buffer_size, b'\\x00')
let output_buffer : FixedArray[Byte] = FixedArray::make(buffer_size, b'\\x00')
let canary : Byte = b'\\xAA'

var read_head : Int = 0
var write_head : Int = 0

// --- Exports for Rust Host ---

pub fn get_buffer_size() -> Int {
  buffer_size
}

// NOTE: Zero-Copy exports removed for V3.1 safety.
// Direct memory access requires unsafe FFI or predictable layout.
// We default to the 'Legacy' Function Call interface for guaranteed stability.

pub fn set_write_head(pos : Int) -> Unit {
  if pos >= 0 {
    write_head = pos % buffer_size
  }
}

pub fn get_read_head() -> Int {
  read_head
}

pub fn set_input_byte(index : Int, val : Int) -> Unit {
  if index >= 0 {
    input_buffer[index % buffer_size] = val.to_byte()
  }
}

pub fn set_input_3_bytes(index : Int, x : Int, y : Int, z : Int) -> Unit {
  if index >= 0 {
    let idx = index % buffer_size
    input_buffer[idx] = x.to_byte()
    input_buffer[(idx + 1) % buffer_size] = y.to_byte()
    input_buffer[(idx + 2) % buffer_size] = z.to_byte()
  }
}

pub fn get_output_byte(index : Int) -> Int {
  if index >= 0 {
    output_buffer[index % buffer_size].to_int()
  } else {
    0
  }
}
"""

def generate_math_structs():
    return """
// --- Vector Math ---

struct Vec3 {
  x : Double
  y : Double
  z : Double
}

fn Vec3::new(x : Double, y : Double, z : Double) -> Vec3 {
  { x, y, z }
}

fn normalize(self : Vec3) -> Vec3 {
  let len = (self.x * self.x + self.y * self.y + self.z * self.z).sqrt()
  if len == 0.0 {
    self
  } else {
    { x: self.x / len, y: self.y / len, z: self.z / len }
  }
}
"""

def generate_processing_logic():
    return """
// --- Kinetic Processing ---

fn diff(read : Int, write : Int, cap : Int) -> Int {
  if write >= read {
    write - read
  } else {
    (cap - read) + write
  }
}

pub fn process_tensor_stream() -> Int {
  let mut processed = 0

  // Kinetic Loop: Process chunks of 3 bytes (Vec3)
  while diff(read_head, write_head, buffer_size) >= 3 {
    let idx = read_head

    // 1. Read Raw Bytes (Function Call Interface)
    let x = input_buffer[idx].to_int().to_double()
    let y = input_buffer[(idx + 1) % buffer_size].to_int().to_double()
    let z = input_buffer[(idx + 2) % buffer_size].to_int().to_double()

    // 2. Compute (Neuronal Activation)
    let v = Vec3::new(x, y, z)
    let vn = v.normalize()

    // 3. Quantize Output (0-255 range mapping [-1, 1] -> [0, 200])
    // Matches Mock Kernel Logic: (nx * 100.0 + 100.0)
    let ox = (vn.x * 100.0 + 100.0).to_int()
    let oy = (vn.y * 100.0 + 100.0).to_int()
    let oz = (vn.z * 100.0 + 100.0).to_int()

    // 4. Write Output
    output_buffer[idx] = ox.to_byte()
    output_buffer[(idx + 1) % buffer_size] = oy.to_byte()
    output_buffer[(idx + 2) % buffer_size] = oz.to_byte()

    read_head = (read_head + 3) % buffer_size
    processed = processed + 3
  }

  processed
}
"""

def main():
    print("Igniting Ark Synthesis Engine (Kinetic Mode V3.1)...")
    kernel_file = get_kernel_path()
    
    content = generate_header()
    content += generate_math_structs()
    content += generate_processing_logic()
        
    print(f"Synthesizing MoonBit Logic...")
    
    with open(kernel_file, "w") as f:
        f.write(content)
    
    # Count lines
    with open(kernel_file, "r") as f:
        lines = len(f.readlines())
        
    print(f"Write Complete: {kernel_file}")
    print(f"Total Lines Synthesized: {lines}")

if __name__ == "__main__":
    main()
