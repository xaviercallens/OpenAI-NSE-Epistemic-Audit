import re
import os

def extract_physical_limits(lean_file_path):
    """
    Parses a Lean 4 file to extract physical limits defined as axioms/constants
    and generates a LaTeX table.
    """
    limits = {
        "Mach Threshold": "N/A",
        "Max Local Vorticity (Water)": "N/A",
        "Mean Free Path (Water)": "N/A",
        "Knudsen Threshold": "N/A"
    }

    if not os.path.exists(lean_file_path):
        print(f"Error: {lean_file_path} not found.")
        return ""

    with open(lean_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex-read the `def` constants of the draft file. This is a text scan of
    # hand-chosen constants, not an extraction from the Lean kernel.
    mach_match = re.search(r"def PhysLibMachThreshold\s*:\s*ℝ\s*:=\s*([\d\.]+)", content)
    cs_match = re.search(r"def PhysLibSoundSpeedWater\s*:\s*ℝ\s*:=\s*([\d\.e]+)", content)
    mfp_match = re.search(r"def PhysLibMeanFreePathWater\s*:\s*ℝ\s*:=\s*([\d\.e\-]+)", content)
    kn_match = re.search(r"def PhysLibKnudsenThreshold\s*:\s*ℝ\s*:=\s*([\d\.]+)", content)

    # The legacy `PhysLibMaxEnstrophyWater = 1.13e13` constant has no derivation
    # and is a global (volume-dependent) quantity; it is deliberately no longer
    # tabulated. The physically motivated bound is local: |omega|_max = c_s^2/nu
    # (Ma < 1 and Kn < 1 together). The Lean draft defines no viscosity constant,
    # so nu for water is taken from the project's physics_constants (1e-6 m^2/s).
    nu_water = 1.0e-6
    if mach_match: limits["Mach Threshold"] = mach_match.group(1)
    if cs_match:
        omega_max = float(cs_match.group(1)) ** 2 / nu_water
        limits["Max Local Vorticity (Water)"] = f"{omega_max:.1e} s$^{{-1}}$"
    if mfp_match: limits["Mean Free Path (Water)"] = mfp_match.group(1) + " m"
    if kn_match: limits["Knudsen Threshold"] = kn_match.group(1)

    latex_table = f"""\\begin{{table}}[h]
\\centering
\\begin{{tabular}}{{|l|c|}}
\\hline
\\textbf{{Physical Parameter}} & \\textbf{{Validity Threshold}} \\\\
\\hline
Mach Threshold ($Ma$) & {limits['Mach Threshold']} \\\\
Max local vorticity ($|\\omega|_{{\\max}} = c_s^2/\\nu$, water) & {limits['Max Local Vorticity (Water)']} \\\\
Molecular length ($\\lambda$, water: intermolecular spacing) & {limits['Mean Free Path (Water)']} \\\\
Knudsen Threshold ($Kn$) & {limits['Knudsen Threshold']} \\\\
\\hline
\\end{{tabular}}
\\caption{{Reference validity thresholds used in this project. Values are hand-chosen constants read by a text scan of the draft Lean file (not extracted from the Lean kernel); the vorticity bound is computed as $c_s^2/\\nu$ and is equivalent to $Ma \\lesssim 1$ and $Kn \\lesssim 1$ together. The former ``Max Enstrophy $\\Omega_{{max}} = 1.13\\times10^{{13}}$'' row had no derivation and is no longer tabulated.}}
\\label{{tab:physlib_limits}}
\\end{{table}}
"""
    return latex_table

if __name__ == "__main__":
    primary_path = os.path.join(
        os.path.dirname(__file__),
        "../03_Lean4_Topological_Censorship/src/PhysLibThermodynamicCensorship.lean"
    )
    draft_path = os.path.join(
        os.path.dirname(__file__),
        "../03_Lean4_Topological_Censorship/src/drafts/PhysLibThermodynamicCensorship.lean"
    )
    lean_path = primary_path if os.path.exists(primary_path) else draft_path
    latex_out = extract_physical_limits(lean_path)
    
    out_path = os.path.join(os.path.dirname(__file__), "../04_Thermodynamic_Censorship_Paper/physlib_limits_table.tex")
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(latex_out)
    
    print(f"Successfully extracted physical limits to {out_path}")
