import math

# Test parameters (you should replace with actual values from your dataset)
pipe_diameter_m = 0.225  # 225mm
roughness_m = 0.0015  # 1.5mm
gradient = 0.01  # 1%
g = 9.807

depth_ratio = 0.5  # Test at 50% fill

print(f"Testing CBW calculation at {depth_ratio*100}% fill")
print(f"Pipe diameter: {pipe_diameter_m*1000}mm")
print(f"Roughness: {roughness_m*1000}mm")
print(f"Gradient: {gradient*100}%")
print()

# Calculate theta
theta = 2 * math.acos(1 - 2 * depth_ratio)
print(f"Theta: {theta} rad ({math.degrees(theta)} deg)")

# LEGACY formulas
print("\n=== LEGACY FORMULAS ===")
flow_area_legacy = (theta - math.sin(theta)) / 8 * math.pi * pipe_diameter_m**2
wetted_perimeter_legacy = pipe_diameter_m * theta / (2 * math.pi)
print(f"Flow area: {flow_area_legacy} m²")
print(f"Wetted perimeter: {wetted_perimeter_legacy} m")
hydraulic_radius_legacy = flow_area_legacy / wetted_perimeter_legacy
print(f"Hydraulic radius: {hydraulic_radius_legacy} m")

reynolds_number_legacy = (4 * flow_area_legacy * math.sqrt(gradient * hydraulic_radius_legacy * g)) / (1.002e-3)
print(f"Reynolds number: {reynolds_number_legacy}")

if reynolds_number_legacy > 4000:
    friction_factor_legacy = 0.25 / (math.log10((roughness_m / (3.7 * pipe_diameter_m)) + (5.74 / reynolds_number_legacy**0.9)))**2
else:
    friction_factor_legacy = 64 / reynolds_number_legacy if reynolds_number_legacy > 0 else 0
print(f"Friction factor: {friction_factor_legacy}")

velocity_legacy = math.sqrt(gradient * hydraulic_radius_legacy * g / friction_factor_legacy)
flow_legacy = flow_area_legacy * velocity_legacy
print(f"Velocity: {velocity_legacy} m/s")
print(f"Flow: {flow_legacy * 1000} L/s")

# CURRENT formulas (from my backend)
print("\n=== CURRENT FORMULAS ===")
area = (theta - math.sin(theta)) / 8 * math.pi * pipe_diameter_m**2
perimeter = pipe_diameter_m * theta / (2 * math.pi)
print(f"Flow area: {area} m²")
print(f"Wetted perimeter: {perimeter} m")
hydraulic_radius = area / perimeter
print(f"Hydraulic radius: {hydraulic_radius} m")

viscosity = 1.002e-3
re_numerator = 4 * area * math.sqrt(gradient * hydraulic_radius * g)
re = re_numerator / viscosity
print(f"Reynolds number: {re}")

if re > 4000:
    term1 = roughness_m / (3.7 * pipe_diameter_m)
    term2 = 5.74 / (re**0.9)
    friction_factor = 0.25 / (math.log10(term1 + term2))**2
else:
    friction_factor = 64 / re
print(f"Friction factor: {friction_factor}")

velocity = math.sqrt(gradient * hydraulic_radius * g / friction_factor)
flow = area * velocity
print(f"Velocity: {velocity} m/s")
print(f"Flow: {flow * 1000} L/s")

print("\n=== DIFFERENCES ===")
print(f"Flow area difference: {abs(area - flow_area_legacy)}")
print(f"Wetted perimeter difference: {abs(perimeter - wetted_perimeter_legacy)}")
print(f"RE difference: {abs(re - reynolds_number_legacy)}")
print(f"Velocity difference: {abs(velocity - velocity_legacy)} m/s")
print(f"Velocity % difference: {abs(velocity - velocity_legacy) / velocity_legacy * 100 if velocity_legacy > 0 else 0}%")
