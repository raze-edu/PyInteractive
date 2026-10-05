import sys
import os
import random
import pygame

# Ensure project root is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from pyinteractive_objects import FATTable, dir_entry, dir_cluster, BitLayoutMode


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 800))
    pygame.display.set_caption("FAT System, Directory Cluster & Entry Visualizer Demo")
    clock = pygame.time.Clock()

    active_view = 0  # 0: FAT Table, 1: dir_cluster, 2: dir_entry

    # View 0: FAT Cluster Allocation Table
    fat16_entries = [
        0xFFF8, 0xFFFF, 4, 7, 5, 9, 0, 8,
        0xFFFF, 10, 0xFFFF, 0, 0, 0, 0, 0
    ]
    fat_table = FATTable(
        pos=(60, 110),
        size=(1160, 640),
        data=fat16_entries,
        entry_size=16,
        mode=BitLayoutMode.BIT_CHAR,
        chars=("0", "1"),
        colors_off_on=((30, 41, 59), (16, 185, 129)),
        col2_width=110,
        arrow_margin=180,
        zoom=1.0,
        interactive=True
    )
    fat_table.assign_info(2 * 16, 3 * 16, {
        "name": "Cluster #2 (FileA.txt Start)",
        "description": "Root entry for FileA.txt",
        "color": (59, 130, 246),
        "metadata": {"File": "FileA.txt", "Next Cluster": "4"}
    })
    fat_table.assign_info(3 * 16, 4 * 16, {
        "name": "Cluster #3 (FileB.bin Start)",
        "description": "Root entry for FileB.bin",
        "color": (236, 72, 153),
        "metadata": {"File": "FileB.bin", "Next Cluster": "7"}
    })

    # View 1: Directory Cluster (dir_cluster)
    cluster_widget = dir_cluster(
        pos=(60, 110),
        size=(1160, 640),
        cluster_index=2,
        zoom=1.0
    )

    # View 2: Standalone 32-Byte Directory Entry (dir_entry)
    single_dir_widget = dir_entry(
        pos=(60, 110),
        size=(1160, 640),
        filename="DOCUMENT.PDF",
        attributes=0x20,
        first_cluster=0x00020004,
        filesize=2048576,
        show_annotations=True,
        annotation_margin=300,
        zoom=0.9,
        interactive=True
    )

    font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
    font_help = pygame.font.SysFont("Segoe UI", 14)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        if active_view == 0:
            active_widget = fat_table
        elif active_view == 1:
            active_widget = cluster_widget
        else:
            active_widget = single_dir_widget

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    active_view = (active_view + 1) % 3
                elif event.key == pygame.K_1:
                    if hasattr(active_widget, "set_mode"):
                        active_widget.set_mode(BitLayoutMode.BIT_CHAR)
                elif event.key == pygame.K_2:
                    if hasattr(active_widget, "set_mode"):
                        active_widget.set_mode(BitLayoutMode.BIT_COLOR)
                elif event.key == pygame.K_3:
                    if hasattr(active_widget, "set_mode"):
                        active_widget.set_mode(BitLayoutMode.HEX)
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    active_widget.zoom_in(0.1)
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    active_widget.zoom_out(0.1)
                elif event.key == pygame.K_r and active_view == 0:
                    rand_entries = [random.randint(0, 15) if random.random() > 0.3 else 0xFFFF for _ in range(16)]
                    fat_table.set_fat_entries(rand_entries)

            active_widget.handle_event(event)

        screen.fill((15, 23, 42))

        # Title & Help text
        if active_view == 0:
            title_str = f"1. FAT Cluster Table Visualizer (Zoom: {fat_table.zoom:.2f}x)"
            help_str = "[TAB] Cycle Views (FAT Table -> dir_cluster -> dir_entry) || Hover Cluster #2/#3 for Pointer Arrows"
        elif active_view == 1:
            title_str = f"2. Directory Cluster Visualizer (dir_cluster) (Zoom: {cluster_widget.zoom:.2f}x)"
            help_str = "[TAB] Cycle Views || Click any Name.Ext Entry Block Card to open detailed 32-byte Specs!"
        else:
            title_str = f"3. Detailed 32-Byte Directory Entry (dir_entry) (Zoom: {single_dir_widget.zoom:.2f}x)"
            help_str = "[TAB] Cycle Views || Renders Bit Letters (h,m,s,y,d,Flags) & Side Callout Cards"

        title_surf = font_title.render(title_str, True, (241, 245, 249))
        screen.blit(title_surf, (60, 20))

        help_surf = font_help.render(help_str, True, (148, 163, 184))
        screen.blit(help_surf, (60, 56))

        # Render Active Widget
        active_widget.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
