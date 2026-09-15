#!/usr/bin/env python3
"""
Directive 7: Pre-Singularity Vortex Core Simulation.
MechanicaFluidorum Program · SocrateAI Lab · September 2026

Simulates the collapsing vortex core and Reynolds stress redistribution
approaching the hypothetical singularity time t = 1.
Includes --no-anim flag to skip GIF generation in test pipelines.
"""

import argparse
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import matplotlib.animation as animation


# Output directory for animations
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'dataset', 'animations')


def get_profiles(tau, r=None, h=1.0 / 200.0):
    """
    Computes azimuthal velocity profile u_theta(r) and Reynolds stress proxy tau_r_theta(r)
    at time to singularity tau.
    """
    if r is None:
        r = np.logspace(-7, 0, 1000)
        
    # Radial length scale l_r ~ tau^0.5
    l_r = tau ** 0.5
    # Velocity scale U ~ tau^(-0.5 - h)
    U = tau ** (-0.5 - h)
    
    # Self-similar vortex profile: u_theta ~ U * (r/l_r) * exp(-(r/l_r)^2)
    eta = r / l_r
    u_theta = U * eta * np.exp(-eta ** 2)
    
    # Reynolds stress proxy (anisotropic energy redistribution)
    # tau_ij ~ (0.1 * l_r)^2 * (du/dr)^2
    du_dr = (U / l_r) * (1.0 - 2.0 * eta ** 2) * np.exp(-eta ** 2)
    reynolds_stress = (0.1 * l_r) ** 2 * np.abs(du_dr) ** 2
    
    return u_theta, reynolds_stress


def run_simulation(no_anim=False, num_frames=150, output_dir=OUTPUT_DIR):
    """Executes the pre-singularity simulation and plot generation."""
    os.makedirs(output_dir, exist_ok=True)
    
    h = 1.0 / 200.0
    tau_start = 1e-3
    tau_end = 1e-13
    taus = np.logspace(np.log10(tau_start), np.log10(tau_end), num_frames)
    r = np.logspace(-7, 0, 1000)

    # 1. Generate animation if not disabled
    if not no_anim:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        line_u, = ax1.plot([], [], 'b-', lw=2)
        line_rs, = ax2.plot([], [], 'r-', lw=2)

        time_template = 'Time to singularity $\\tau = {:.1e}$ s'
        time_text1 = ax1.text(0.05, 0.9, '', transform=ax1.transAxes)
        time_text2 = ax2.text(0.05, 0.9, '', transform=ax2.transAxes)

        ax1.set_xscale('log')
        ax1.set_yscale('log')
        ax1.set_xlim(1e-7, 1e-1)
        ax1.set_ylim(1e2, 1e7)
        ax1.set_xlabel('Radius $r$ (m)')
        ax1.set_ylabel('Velocity $u_\\theta$ (m/s)')
        ax1.set_title('Vortex Core Contraction')
        ax1.grid(True, which="both", ls="--", alpha=0.5)

        ax2.set_xscale('log')
        ax2.set_yscale('log')
        ax2.set_xlim(1e-7, 1e-1)
        ax2.set_ylim(1e0, 1e12)
        ax2.set_xlabel('Radius $r$ (m)')
        ax2.set_ylabel('Reynolds Stress Proxy $\\tau_{r\\theta}$ (m$^2$/s$^2$)')
        ax2.set_title('Subgrid Kinetic Energy Redistribution')
        ax2.grid(True, which="both", ls="--", alpha=0.5)
        plt.tight_layout()

        def init():
            line_u.set_data([], [])
            line_rs.set_data([], [])
            time_text1.set_text('')
            time_text2.set_text('')
            return line_u, line_rs, time_text1, time_text2

        def animate(i):
            tau = taus[i]
            u_theta, reynolds_stress = get_profiles(tau, r=r, h=h)
            line_u.set_data(r, u_theta)
            line_rs.set_data(r, reynolds_stress)
            time_text1.set_text(time_template.format(tau))
            time_text2.set_text(time_template.format(tau))
            return line_u, line_rs, time_text1, time_text2

        ani = animation.FuncAnimation(fig, animate, np.arange(num_frames),
                                      interval=50, blit=True, init_func=init)
        output_path = os.path.join(output_dir, 'pre_singularity_vortex.gif')
        ani.save(output_path, writer='pillow', fps=20)
        plt.close(fig)
        print(f"Animation successfully saved to {output_path}")
    else:
        print("Skipping GIF animation generation (--no-anim enabled).")

    # 2. Generate a static comparison plot for documentation
    fig_static, (ax1_s, ax2_s) = plt.subplots(1, 2, figsize=(12, 5))
    taus_to_plot = [1e-3, 1e-6, 1e-9, 1e-12, 6.7e-14]
    colors = plt.cm.viridis(np.linspace(0, 1, len(taus_to_plot)))

    for tau, c in zip(taus_to_plot, colors):
        u_theta, rs = get_profiles(tau, r=r, h=h)
        ax1_s.plot(r, u_theta, color=c, label=f'$\\tau = {tau:.1e}$ s')
        ax2_s.plot(r, rs, color=c, label=f'$\\tau = {tau:.1e}$ s')

    ax1_s.set_xscale('log')
    ax1_s.set_yscale('log')
    ax1_s.set_xlim(1e-7, 1e-1)
    ax1_s.set_ylim(1e0, 1e7)
    ax1_s.set_xlabel('Radius $r$ (m)')
    ax1_s.set_ylabel('Velocity $u_\\theta$ (m/s)')
    ax1_s.set_title('Vortex Core Contraction')
    ax1_s.legend()
    ax1_s.grid(True, which="both", ls="--", alpha=0.5)

    ax2_s.set_xscale('log')
    ax2_s.set_yscale('log')
    ax2_s.set_xlim(1e-7, 1e-1)
    ax2_s.set_ylim(1e-4, 1e12)
    ax2_s.set_xlabel('Radius $r$ (m)')
    ax2_s.set_ylabel('Reynolds Stress Proxy (m$^2$/s$^2$)')
    ax2_s.set_title('Subgrid Kinetic Energy Redistribution')
    ax2_s.legend()
    ax2_s.grid(True, which="both", ls="--", alpha=0.5)

    plt.tight_layout()
    static_path = os.path.join(output_dir, 'pre_singularity_static_profiles.png')
    plt.savefig(static_path, dpi=300)
    plt.close(fig_static)
    print(f"Static profile image successfully saved to {static_path}")
    return static_path


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Directive 7: Pre-Singularity Simulation")
    parser.add_argument("--no-anim", action="store_true", help="Skip rendering GIF animation")
    parser.add_argument("--num-frames", type=int, default=150, help="Number of frames for simulation")
    return parser.parse_args(args)


def main():
    args = parse_args()
    run_simulation(no_anim=args.no_anim, num_frames=args.num_frames)


if __name__ == '__main__':
    main()
