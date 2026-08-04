import sys
import pygame
from pyinteractive import PygameApp
from pyinteractive_objects import MultiWheelCounter, StringInput, Slider

def main():
    # Initialize the Pygame app using the default config.json
    try:
        app = PygameApp(config_path="config.json", title="Number System Playground")
    except Exception as e:
        print(f"Error loading configuration or initializing app: {e}")
        sys.exit(1)

    # Active screen state: 0 is Menu screen, 1 is Counter screen
    active_screen = 0
    counter = None

    # --- Screen 0: Menu Widgets Setup ---
    # String input for space-separated wheel options
    text_input = StringInput(
        pos=(460, 400),
        size=(1000, 60),
        max_length=60,
        placeholder="e.g. 0 1 2 3 4"
    )
    # Pre-populate string input with default options for convenience
    text_input.text = "0 1 2 3 4"

    # Slider for choosing number of wheels (range from 2 to 15)
    slider = Slider(
        pos=(460, 560),
        size=(1000, 60),
        values=list(range(2, 16)),
        default_index=1  # Default is 3 wheels (values[1] = 3)
    )

    # --- Navigation Elements Rectangles ---
    btn_toggle = pygame.Rect(20, 20, 150, 40)      # Top-left switch button
    btn_build = pygame.Rect(810, 750, 300, 60)     # "BUILD COUNTER" bottom button

    def switch_to_screen(new_screen: int) -> None:
        """Transitions to the specified screen. Re-creates the counter if moving to screen 1."""
        nonlocal active_screen, counter
        
        if new_screen == 1:
            # Recreate the counter dynamically based on menu inputs
            raw_text = text_input.text.strip()
            if raw_text == "":
                options = ["0", "1", "2", "3", "4"]
            else:
                options = raw_text.split()
                if len(options) == 0:
                    options = ["0", "1", "2", "3", "4"]
            
            num_wheels = int(slider.get_value())
            
            # Position counter: width 1400, height 500, centered in 1920x1080 display
            # (1920 - 1400) / 2 = 260
            # (1080 - 500) / 2 = 290
            counter = MultiWheelCounter(
                pos=(260, 290),
                size=(1400, 500),
                items=options,
                num_wheels=num_wheels
            )
            
        active_screen = new_screen

    # --- Event Handling Overrides ---
    original_handle_event = app.handle_event
    def custom_handle_event(event: pygame.event.Event) -> None:
        nonlocal active_screen
        
        # 1. Global Keyboard Shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                app.is_running = False
                return
            elif event.key == pygame.K_F1:
                switch_to_screen(1 - active_screen)
                return

        # 2. Mouse Clicks (Button 1: Left Click)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.display.get_init():
                mouse_pos = pygame.mouse.get_pos()
            else:
                mouse_pos = getattr(event, "pos", (0, 0))

            # Click top-left navigation toggle button
            if btn_toggle.collidepoint(mouse_pos):
                switch_to_screen(1 - active_screen)
                return

            # Click bottom Build Button on Menu screen
            if active_screen == 0 and btn_build.collidepoint(mouse_pos):
                switch_to_screen(1)
                return

        # 3. Route Events to Active Screen Widgets
        if active_screen == 0:
            text_input.handle_event(event)
            slider.handle_event(event)
        else:
            if counter:
                counter.handle_event(event)

        original_handle_event(event)
        
    app.handle_event = custom_handle_event

    # --- Update Loop Overrides ---
    original_update = app.update
    def custom_update(dt: float) -> None:
        if active_screen == 0:
            text_input.update(dt)
            slider.update(dt)
        else:
            if counter:
                counter.update(dt)
        original_update(dt)
        
    app.update = custom_update

    # --- Drawing Loop Overrides ---
    def custom_draw() -> None:
        # Fetch configurations
        primary_color = app.get_color("primary", (0, 150, 255, 255))
        secondary_color = app.get_color("secondary", (240, 240, 240, 255))
        accent_color = app.get_color("accent", (255, 65, 54, 255))
        panel_color = app.get_color("wheel_bg", (25, 25, 30, 255))

        # Fonts setup
        try:
            title_font = pygame.font.Font(None, 60)
            label_font = pygame.font.Font(None, 32)
            btn_font = pygame.font.Font(None, 26)
        except Exception:
            title_font = pygame.font.SysFont("arial", 60)
            label_font = pygame.font.SysFont("arial", 32)
            btn_font = pygame.font.SysFont("arial", 26)

        # Draw Top-Left Button (shared across both screens)
        pygame.draw.rect(app.screen, panel_color, btn_toggle)
        pygame.draw.rect(app.screen, primary_color, btn_toggle, 2)
        
        btn_text = "PLAY [F1]" if active_screen == 0 else "MENU [F1]"
        btn_surf = btn_font.render(btn_text, True, secondary_color)
        bx = btn_toggle.x + (btn_toggle.width - btn_surf.get_width()) / 2
        by = btn_toggle.y + (btn_toggle.height - btn_surf.get_height()) / 2
        app.screen.blit(btn_surf, (int(bx), int(by)))

        if active_screen == 0:
            # --- SCREEN 0: MENU DRAWING ---
            
            # Header Title & Subtitle
            title_surf = title_font.render("Number System Playground", True, primary_color)
            sub_surf = label_font.render("Configure your custom odometer with a base and number of wheels", True, secondary_color)
            app.screen.blit(title_surf, (int((app.screen.get_width() - title_surf.get_width()) / 2), 130))
            app.screen.blit(sub_surf, (int((app.screen.get_width() - sub_surf.get_width()) / 2), 200))

            # String list input widget
            text_lbl = label_font.render("String symbols (space separated, max 60 chars):", True, secondary_color)
            app.screen.blit(text_lbl, (460, 360))
            text_input.draw(app.screen, app)

            # Wheels count slider widget
            slider_lbl = label_font.render(f"Number of wheels: {slider.get_value()}", True, secondary_color)
            app.screen.blit(slider_lbl, (460, 520))
            slider.draw(app.screen, app)

            # Bottom Build/Play Button
            pygame.draw.rect(app.screen, panel_color, btn_build)
            pygame.draw.rect(app.screen, primary_color, btn_build, 2)
            build_surf = btn_font.render("BUILD COUNTER", True, accent_color)
            bdx = btn_build.x + (btn_build.width - build_surf.get_width()) / 2
            bdy = btn_build.y + (btn_build.height - build_surf.get_height()) / 2
            app.screen.blit(build_surf, (int(bdx), int(bdy)))

        else:
            # --- SCREEN 1: ODOMETER COUNTER DRAWING ---
            if counter:
                # Odometer title with active base length
                base_len = len(counter.items)
                title_surf = title_font.render(f"Connected Odometer (Base-{base_len})", True, primary_color)
                app.screen.blit(title_surf, (int((app.screen.get_width() - title_surf.get_width()) / 2), 80))

                # Display active decimal total
                sum_surf = label_font.render(f"Decimal (Base-10) Total: {counter.get_total_sum()}", True, secondary_color)
                app.screen.blit(sum_surf, (int((app.screen.get_width() - sum_surf.get_width()) / 2), 150))

                # Display scroll guidelines at bottom
                inst_surf = label_font.render(
                    "Scroll, drag, or use Up/Down arrow keys on the hovered wheel. Carry propagates left, Borrow right.",
                    True,
                    secondary_color
                )
                app.screen.blit(inst_surf, (int((app.screen.get_width() - inst_surf.get_width()) / 2), 820))

                # Render odometer
                counter.draw(app.screen, app)

    app.draw = custom_draw

    # Start Pygame loop
    app.run()
    print("App closed successfully.")

if __name__ == "__main__":
    main()
