import sys
import os
import random
import pygame

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pyinteractive import PygameApp
from pyinteractive_objects import BitLayout, BitInfoObject, SectionLabel, BitLayoutMode
import bitarray


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 768))
    pygame.display.set_caption("Modular & Zoomable BitLayout Visualizer Demo")
    clock = pygame.time.Clock()

    # Create 128-bit sample data (e.g., Network Packet Header + Payload)
    sample_bits = bitarray.bitarray('1' * 16 + '0' * 16 + '1010' * 8 + '0110' * 8 + '1100' * 8)

    # Initialize BitLayout Widget
    bit_layout = BitLayout(
        pos=(60, 100),
        size=(1160, 580),
        data=sample_bits,
        row_size=16,                           # 16 bits per row
        mode=BitLayoutMode.BIT_CHAR,           # Default bit character mode
        chars=("0", "1"),
        colors_off_on=((30, 41, 59), (16, 185, 129)),  # Dark Slate (0) / Emerald Green (1)
        col1_width=130,                        # 1st Left Col: Multi-row section labels
        col2_width=90,                         # 2nd Left Col: Row offsets
        show_header=True,
        interactive=True,
        zoom=1.0                               # Scalable geometry factor
    )

    # Add Multi-Row Section Labels (Col 1)
    bit_layout.add_section_label(0, 1, "HEADER (32b)", (59, 130, 246))       # Rows 0-1
    bit_layout.add_section_label(2, 4, "PAYLOAD (48b)", (16, 185, 129))      # Rows 2-4
    bit_layout.add_section_label(5, 7, "CHECKSUM (48b)", (245, 158, 11))     # Rows 5-7

    # Assign Info Objects to Bit Slices
    bit_layout.assign_info(0, 4, BitInfoObject(
        name="Version",
        description="Protocol version identifier",
        color=(99, 102, 241),
        metadata={"Protocol": "PyInteractive v2.0", "Type": "Control"}
    ))

    bit_layout.assign_info(4, 8, BitInfoObject(
        name="IHL",
        description="Internet Header Length",
        color=(236, 72, 153),
        metadata={"Unit": "32-bit Words"}
    ))

    bit_layout.assign_info(8, 16, BitInfoObject(
        name="Type of Service",
        description="Differentiated Services Field / QoS Flags",
        color=(14, 165, 233),
        metadata={"DSCP": "CS0", "ECN": "Non-ECT"}
    ))

    bit_layout.assign_info(16, 32, BitInfoObject(
        name="Total Length",
        description="Total packet length in bytes",
        color=(168, 85, 247),
        metadata={"Max Length": "65535 Bytes"}
    ))

    bit_layout.assign_info(32, 64, BitInfoObject(
        name="Source Address",
        description="32-bit Originating Host Address",
        color=(34, 197, 94),
        metadata={"IP Format": "IPv4 Standard"}
    ))

    bit_layout.assign_info(64, 96, BitInfoObject(
        name="Destination Address",
        description="32-bit Target Host Address",
        color=(234, 179, 8),
        metadata={"IP Format": "IPv4 Standard"}
    ))

    bit_layout.assign_info(96, 128, BitInfoObject(
        name="Frame Check Sequence",
        description="CRC-32 Error Detection Checksum",
        color=(239, 68, 68),
        metadata={"Algorithm": "IEEE 802.3 CRC32"}
    ))

    font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
    font_help = pygame.font.SysFont("Segoe UI", 14)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    bit_layout.set_mode(BitLayoutMode.BIT_CHAR)
                elif event.key == pygame.K_2:
                    bit_layout.set_mode(BitLayoutMode.BIT_COLOR)
                elif event.key == pygame.K_3:
                    bit_layout.set_mode(BitLayoutMode.HEX)
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    bit_layout.zoom_in(0.1)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    bit_layout.zoom_out(0.1)
                elif event.key == pygame.K_r:
                    # Randomize bits
                    rand_str = "".join(random.choice("01") for _ in range(128))
                    bit_layout.set_data(rand_str)

            # Pass events to BitLayout widget
            bit_layout.handle_event(event)

        # Render UI
        screen.fill((15, 23, 42))  # Dark navy slate background

        # Header Title & Controls Bar
        title_str = f"Modular & Zoomable BitLayout Visualizer (Zoom: {bit_layout.zoom:.2f}x)"
        title_surf = font_title.render(title_str, True, (241, 245, 249))
        screen.blit(title_surf, (60, 20))

        help_str = "Modes: [1] Bit Char | [2] Bit Color | [3] Hex || Zoom: [+/-] or [CTRL + Wheel] || [R] Randomize || Click: Toggle Bit"
        help_surf = font_help.render(help_str, True, (148, 163, 184))
        screen.blit(help_surf, (60, 56))

        # Render BitLayout widget
        bit_layout.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
