import re
import os

def extract_physical_limits(lean_file_path):
    """
    Parses a Lean 4 file to extract physical limits defined as axioms/constants
    and generates a LaTeX table.
    """
    limits = {
        "Mach Threshold": "N/A",
        "Max Enstrophy (Water)": "N/A",
        "Mean Free Path (Water)": "N/A",
        "Knudsen Threshold": "N/A"
    }

    if not os.path.exists(lean_file_path):
        print(f"Error: {lean_file_path} not found.")
        return ""

    with open(lean_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Simple regex to extract defined constant values
    mach_match = re.search(r"def PhysLibMachThreshold\s*:\s*ℝ\s*:=\s*([\d\.]+)", content)
    enstrophy_match = re.search(r"def PhysLibMaxEnstrophyWater\s*:\s*ℝ\s*:=\s*([\d\.e]+)", content)
    mfp_match = re.search(r"def PhysLibMeanFreePathWater\s*:\s*ℝ\s*:=\s*([\d\.e\-]+)", content)
    kn_match = re.search(r"def PhysLibKnudsenThreshold\s*:\s*ℝ\s*:=\s*([\d\.]+)", content)

    if mach_match: limits["Mach Threshold"] = mach_match.group(1)
    if enstrophy_match: limits["Max Enstrophy (Water)"] = enstrophy_match.group(1)
    if mfp_match: limits["Mean Free Path (Water)"] = mfp_match.group(1) + " m"
    if kn_match: limits["Knudsen Threshold"] = kn_match.group(1)

    latex_table = f"""\\begin{{table}}[h]
\\centering
\\begin{{tabular}}{{|l|c|}}
\\hline
\\textbf{{Physical Parameter}} & \\textbf{{Censorship Limit}} \\\\
\\hline
Mach Threshold ($Ma$) & {limits['Mach Threshold']} \\\\
Max Enstrophy ($\\Omega_{{max}}$) & {limits['Max Enstrophy (Water)']} \\\\
Mean Free Path ($\\lambda$) & {limits['Mean Free Path (Water)']} \\\\
Knudsen Threshold ($Kn$) & {limits['Knudsen Threshold']} \\\\
\\hline
\\end{{tabular}}
\\caption{{Automated extraction of physical censorship boundaries from Lean 4 kernel.}}
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
