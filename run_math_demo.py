import sys
import pygame
from pyinteractive import PygameApp
from pyinteractive_objects import StringInput, MathEquationWidget

def main():
    print("Initializing Pygame App for MathEquationWidget Demo...")
    
    try:
        app = PygameApp(config_path="config.json", title="Interactive Math Equation Demo")
    except Exception as e:
        print(f"Error loading configuration or initializing app: {e}")
        sys.exit(1)

    # 1. Create a StringInput for typing math equations
    # Position: (260, 200), Size: (1400, 60), Max Length: 80
    equation_input = StringInput(
        pos=(260, 200),
        size=(1400, 60),
        max_length=80,
        placeholder="Type equation, e.g. 3 + !frac{20 + 1}{100}"
    )
    equation_input.text = "3 + !frac{20 + 1}{100}"
    app.add_object(equation_input)

    # 2. Create the MathEquationWidget to display the equation
    # Position: (260, 350), Font Size: 48, using default theme secondary color
    math_widget = MathEquationWidget(
        pos=(260, 380),
        expression=equation_input.text,
        font_size=48
    )
    app.add_object(math_widget)

    print("\nInstructions:")
    print("  - Click on the text box to type.")
    print("  - Supported markup:")
    print("      - !frac{num}{den}  : Creates a fraction layout block.")
    print("      - \\!, \\{, \\}, \\\\    : Escapes special characters.")
    print("  - Nested functions are fully supported, e.g., !frac{!frac{1}{2}}{3}.")
    print("  - Press ESC to exit.")

    # Custom event handling
    original_handle_event = app.handle_event
    def custom_handle_event(event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                app.is_running = False
                return
            
        # Forward events to StringInput
        equation_input.handle_event(event)
        original_handle_event(event)

    app.handle_event = custom_handle_event

    # Custom update to synchronize input text with equation widget expression
    original_update = app.update
    def custom_update(dt):
        original_update(dt)
        # Update widget expression if input changed
        if math_widget.expression != equation_input.text:
            math_widget.expression = equation_input.text

    app.update = custom_update

    # Custom drawing to add title and helper labels
    original_draw = app.draw
    def custom_draw():
        # Setup fonts
        try:
            title_font = pygame.font.Font(None, 48)
            label_font = pygame.font.Font(None, 24)
        except Exception:
            title_font = pygame.font.SysFont("arial", 48)
            label_font = pygame.font.SysFont("arial", 24)

        primary_color = app.get_color("primary")
        secondary_color = app.get_color("secondary")

        # Draw header title
        title_surf = title_font.render("Interactive Math Equation Demo", True, primary_color)
        app.screen.blit(title_surf, (int((app.screen.get_width() - title_surf.get_width()) / 2), 40))

        # Draw input box label
        input_label = label_font.render("Equation Input String:", True, secondary_color)
        app.screen.blit(input_label, (260, 170))

        # Draw rendering output label
        render_label = label_font.render("Rendered Math Equation:", True, secondary_color)
        app.screen.blit(render_label, (260, 330))

        # Draw instructions/examples at the bottom
        inst_1 = label_font.render("Examples to copy & paste:", True, primary_color)
        inst_2 = label_font.render("-  x!expo{2} + y!expo{2} = z!expo{2}", True, secondary_color)
        inst_3 = label_font.render("-  !sqrt{x!expo{2} + y!expo{2}}", True, secondary_color)
        inst_4 = label_font.render("-  !frac{-b +- !sqrt{b!expo{2} - 4ac}}{2a}", True, secondary_color)
        
        app.screen.blit(inst_1, (260, 720))
        app.screen.blit(inst_2, (260, 760))
        app.screen.blit(inst_3, (260, 790))
        app.screen.blit(inst_4, (260, 820))

        # Draw standard widgets
        original_draw()

    app.draw = custom_draw

    # Run the Pygame loop
    app.run()
    print("Demo closed successfully.")

if __name__ == "__main__":
    main()
