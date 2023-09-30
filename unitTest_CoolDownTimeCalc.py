def time_to_reach_setpoint(initial_temp_water_c, setpoint_temp_c, volume_water_liters, mass_ice_pack_g, c_gel, number_of_ice_packs):
    # Constants
    c_water = 4.18  # J/g°C
    liters_to_ml = 1000  # mL/L
    density_water_g_ml = 1  # g/mL
    
    # Calculate the mass of water in grams
    mass_water_grams = volume_water_liters * liters_to_ml * density_water_g_ml
    
    # Calculate the total energy change required to reach the setpoint temperature
    delta_Q_required = mass_water_grams * c_water * (initial_temp_water_c - setpoint_temp_c)
    
    # Calculate the total energy that can be absorbed by the ice packs
    total_energy_ice_packs = number_of_ice_packs * mass_ice_pack_g * c_gel * (0 - (-5))
    
    # Check if the ice packs have enough capacity to cool the water to the setpoint temperature
    if total_energy_ice_packs < delta_Q_required:
        return None  # The given number of ice packs is not sufficient to reach the setpoint temperature
    
    # Calculate the time required to reach the setpoint temperature
    time_seconds = delta_Q_required / (number_of_ice_packs * mass_ice_pack_g * c_gel * (0 - (-5)) / mass_ice_pack_g)
    return time_seconds / 60  # Convert time to minutes


# Given data
initial_temp_water_c = 12.05  # Initial temperature of water in °C
setpoint_temp_c = 8  # Desired setpoint temperature in °C
volume_water_liters = 48  # Volume of water in liters
mass_ice_pack_g = 2600  # Mass of each ice pack in grams
c_gel = 7.18  # Specific heat capacity of the gel in J/g°C
number_of_ice_packs = 10

# Calculate the time required to reach the setpoint temperature
time_minutes = time_to_reach_setpoint(initial_temp_water_c, setpoint_temp_c, volume_water_liters, mass_ice_pack_g, c_gel, number_of_ice_packs)

if time_minutes:
    print(f"Time required to reach the setpoint temperature: {time_minutes} minutes")
else:
    print("The given number of ice packs is not sufficient to reach the setpoint temperature.")

