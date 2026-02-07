package lib

// Project Moonlight: Verification Suite
// "Trust, but Verify."

test "Matrix_Float64::add" {
  let m1 = Matrix_Float64::new(2, 2)
  let m2 = Matrix_Float64::new(2, 2)
  
  // Set values
  m1.set(0, 0, 1.0); m1.set(0, 1, 2.0)
  m2.set(0, 0, 3.0); m2.set(0, 1, 4.0)
  
  let res = m1.add(m2)
  
  // Assertions (Primitive)
  if res.get(0, 0) != 4.0 { abort("Add Failed: 1+3 != 4") }
  if res.get(0, 1) != 6.0 { abort("Add Failed: 2+4 != 6") }
}

test "Vec3::dot" {
  let v1 = Vec3::new(1.0, 0.0, 0.0) // X-axis
  let v2 = Vec3::new(0.0, 1.0, 0.0) // Y-axis
  
  let dot = v1.dot(v2)
  
  if dot != 0.0 { abort("Dot Failed: Orthogonal vectors must be 0") }
  
  let v3 = Vec3::new(2.0, 0.0, 0.0)
  let dot2 = v1.dot(v3)
  
  if dot2 != 2.0 { abort("Dot Failed: Parallel vectors") }
}

test "Mat4x4::identity" {
  let id = Mat4x4::identity()
  
  // Check diagonal
  if id.m00 != 1.0 { abort("Identity Failed: m00") }
  if id.m11 != 1.0 { abort("Identity Failed: m11") }
  if id.m22 != 1.0 { abort("Identity Failed: m22") }
  if id.m33 != 1.0 { abort("Identity Failed: m33") }
  
  // Check off-diagonal
  if id.m01 != 0.0 { abort("Identity Failed: m01") }
}
