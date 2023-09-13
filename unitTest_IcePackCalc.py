import math

def calculate_ice_packs(T_initial, T_final):
    m_water = 184955  # mass of 48.85 gallons of water in grams
    c = 7.18  # specific heat capacity of water in J/g°C
    Lf = 300  # heat of fusion for water in J/g
    m_ice_pack = 2600  # mass of one ice pack in grams

    E_needed = m_water * c * (T_initial - T_final)
    E_ice_pack = m_ice_pack * (Lf + c * T_final)

    N = E_needed / E_ice_pack
    N = math.ceil(N)  # Round up to the nearest whole number
    return N

print(calculate_ice_packs(12.5, 7))