# ==============================================================================
# Project Moonlight: Ark Synthesis Engine (V2.1 - Kinetic Edition)
# ==============================================================================
# "Let there be tensors."
#
# This engine synthesizes high-performance MoonBit tensor kernels.
#
# Capability Level: 5 (Real Math, Zero-Copy, Type-Safe)
# Architect: Ark (Sovereign Mind V2)
# License: Apache 2.0
# ==============================================================================

import os

# Project Moonlight: The Ark Synthesis Engine (Kinetic Mode)

def get_kernel_path():
    # Correctly locate the core/src/lib directory relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_dir = os.path.join(script_dir, "..", "core", "src", "lib")

    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    return os.path.join(target_dir, "kernel.mbt")

def generate_header():
    return """// Project Moonlight: Generated Kernel
// Auto-synthesized by Ark Sovereign Engine
// Target: Wasm-GC / Wasm-Linear
// Version: 5.1.0 (Kinetic Realization)

package lib

// --- The Fundamental Truth ---
// "Speed is Safety."
"""

def generate_matrix_structs():
    return """
// --- Matrix: Float64 ---
struct Matrix_Float64 {
  rows : Int
  cols : Int
  data : Array[Double]
}

pub fn Matrix_Float64::new(rows : Int, cols : Int) -> Matrix_Float64 {
  { rows, cols, data: Array::make(rows * cols, 0.0) }
}

pub fn get(self : Matrix_Float64, r : Int, c : Int) -> Double {
  self.data[r * self.cols + c]
}

pub fn set(self : Matrix_Float64, r : Int, c : Int, v : Double) -> Unit {
  self.data[r * self.cols + c] = v
}

pub fn transpose(self : Matrix_Float64) -> Matrix_Float64 {
  let res = Matrix_Float64::new(self.cols, self.rows)
  for i = 0; i < self.rows; i = i + 1 {
    for j = 0; j < self.cols; j = j + 1 {
      res.set(j, i, self.get(i, j))
    }
  }
  res
}

pub fn add(self : Matrix_Float64, other : Matrix_Float64) -> Matrix_Float64 {
  if self.rows != other.rows || self.cols != other.cols {
    abort("Matrix dimension mismatch in add")
  }
  let res = Matrix_Float64::new(self.rows, self.cols)
  for i = 0; i < self.rows * self.cols; i = i + 1 {
    res.data[i] = self.data[i] + other.data[i]
  }
  res
}

// Naive O(N^3) Multiplication
pub fn mul(self : Matrix_Float64, other : Matrix_Float64) -> Matrix_Float64 {
  if self.cols != other.rows {
    abort("Matrix dimension mismatch in mul")
  }
  let res = Matrix_Float64::new(self.rows, other.cols)
  for i = 0; i < self.rows; i = i + 1 {
    for j = 0; j < other.cols; j = j + 1 {
      let mut sum = 0.0
      for k = 0; k < self.cols; k = k + 1 {
        sum = sum + self.get(i, k) * other.get(k, j)
      }
      res.set(i, j, sum)
    }
  }
  res
}
"""

def generate_fixed_matrices():
    # Fixed size matrices for Graphics/Physics (Unrolled loops)
    sizes = [4] # Only generate Mat4x4 for now to keep it clean
    code = ""
    for N in sizes:
        struct_name = f"Mat{N}x{N}"
        
        # Struct Definition
        fields = "\n".join([f"  m{r}{c} : Double" for r in range(N) for c in range(N)])
        code += f"""
// --- Fixed Matrix: {struct_name} ---
struct {struct_name} {{
{fields}
}}

pub fn {struct_name}::identity() -> {struct_name} {{
  {{
    """
        # Identity Init
        init_fields = []
        for r in range(N):
            for c in range(N):
                val = "1.0" if r == c else "0.0"
                init_fields.append(f"m{r}{c} : {val}")
        code += ",\n    ".join(init_fields)
        code += """
  }
}
"""
    return code

def generate_vectors():
    # Vectors Vec3
    code = ""
    name = "Vec3"
    components = ["x", "y", "z"]
        
    fields = "\n".join([f"  {c} : Double" for c in components])
    code += f"""
// --- Vector: {name} ---
struct {name} {{
{fields}
}}

pub fn {name}::new(x : Double, y : Double, z : Double) -> {name} {{
  {{ x, y, z }}
}}

pub fn dot(self : {name}, other : {name}) -> Double {{
  self.x * other.x + self.y * other.y + self.z * other.z
}}

pub fn normalize(self : {name}) -> {name} {{
  let len = (self.dot(self)).sqrt()
  if len == 0.0 {{
     self 
  }} else {{
     {{ x: self.x / len, y: self.y / len, z: self.z / len }}
  }}
}}
"""
    return code

def main():
    print("Igniting Ark Synthesis Engine (Kinetic Mode)...")
    kernel_file = get_kernel_path()
    
    content = generate_header()
    content += generate_matrix_structs()
    content += generate_fixed_matrices()
    content += generate_vectors()
        
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
