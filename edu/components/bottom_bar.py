"""Bottom action bar and check/continue feedback banner component."""
from typing import Optional, Tuple
import pygame
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_bevel_button,
    draw_lightbulb,
    draw_calculator_icon,
    draw_check_badge,
    draw_cross_badge,
    DIVIDER_COLOR,
    BG_COLOR,
    BANNER_CORRECT_BG,
    BANNER_INCORRECT_BG,
    GREEN_CORRECT,
    GREEN_DARK,
    RED_INCORRECT,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class BottomBar:
    """Bottom navigation and check bar with animated result banner."""
    
    def __init__(self):
        self.state: str = "question"  # "question", "correct", "incorrect"
        self.feedback_message: str = "Good job!"
        self.solution_hint: str = ""
        self.is_ready_to_check: bool = False
        
        # Animations
        self.banner_offset: float = 140.0  # Slide-in animation offset
        self.target_offset: float = 0.0
        
        # Interaction rects
        self.check_rect = pygame.Rect(0, 0, 160, 52)
        self.continue_rect = pygame.Rect(0, 0, 170, 52)
        self.help_rect = pygame.Rect(0, 0, 110, 44)
        self.calc_rect = pygame.Rect(0, 0, 48, 44)
        
        self.hovered_btn: Optional[str] = None
        self.pressed_btn: Optional[str] = None
        
    def set_state(self, state: str, message: str = "Good job!", solution_hint: str = "") -> None:
        self.state = state
        self.feedback_message = message
        self.solution_hint = solution_hint
        if state in ("correct", "incorrect"):
            self.banner_offset = 120.0
            self.target_offset = 0.0
        else:
            self.banner_offset = 0.0
            self.target_offset = 0.0

    def update(self, dt: float) -> None:
        # Smooth slide-in lerp
        self.banner_offset += (self.target_offset - self.banner_offset) * min(1.0, dt * 14.0)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handles mouse interactions and returns action strings: 'check', 'continue', 'help', 'toolkit'."""
        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            if self.state == "question":
                if self.check_rect.collidepoint(pos):
                    self.hovered_btn = "check"
                elif self.help_rect.collidepoint(pos):
                    self.hovered_btn = "help"
                elif self.calc_rect.collidepoint(pos):
                    self.hovered_btn = "calc"
                else:
                    self.hovered_btn = None
            else:
                if self.continue_rect.collidepoint(pos):
                    self.hovered_btn = "continue"
                else:
                    self.hovered_btn = None

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.state == "question":
                if self.check_rect.collidepoint(pos) and self.is_ready_to_check:
                    self.pressed_btn = "check"
                    sound_manager.play_click()
                    return "check"
                elif self.help_rect.collidepoint(pos):
                    self.pressed_btn = "help"
                    sound_manager.play_click()
                    return "help"
                elif self.calc_rect.collidepoint(pos):
                    self.pressed_btn = "calc"
                    sound_manager.play_click()
                    return "toolkit"
            else:
                if self.continue_rect.collidepoint(pos):
                    self.pressed_btn = "continue"
                    sound_manager.play_click()
                    return "continue"

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.pressed_btn = None

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if self.state == "question" and self.is_ready_to_check:
                    sound_manager.play_click()
                    return "check"
                elif self.state in ("correct", "incorrect"):
                    sound_manager.play_click()
                    return "continue"

        return None

    def draw(self, screen: pygame.Surface, rect: pygame.Rect) -> None:
        """Renders bottom bar or the full-width result banner."""
        btn_font = get_font(20, bold=True)
        small_font = get_font(15, bold=True)

        # 1. In standard question state:
        if self.state == "question":
            # Top border line
            pygame.draw.line(screen, DIVIDER_COLOR, (rect.left, rect.top), (rect.right, rect.top), 2)
            
            # Left toolkit / calc icon button
            self.calc_rect = pygame.Rect(rect.x + 30, rect.y + (rect.height - 46) // 2, 46, 46)
            calc_hover = self.hovered_btn == "calc"
            calc_bg = (32, 47, 54) if calc_hover else (24, 39, 46)
            draw_rounded_rect(screen, self.calc_rect, calc_bg, radius=12, border_color=(43, 61, 71), border_width=2)
            draw_calculator_icon(screen, self.calc_rect.center, 22, (28, 176, 246) if calc_hover else (119, 142, 155))

            # Left HELP button with lightbulb
            self.help_rect = pygame.Rect(rect.x + 90, rect.y + (rect.height - 46) // 2, 110, 46)
            help_hover = self.hovered_btn == "help"
            help_bg = (32, 47, 54) if help_hover else (24, 39, 46)
            draw_rounded_rect(screen, self.help_rect, help_bg, radius=12, border_color=(43, 61, 71), border_width=2)
            
            # Draw bulb & text
            bulb_col = (28, 176, 246) if help_hover else (119, 142, 155)
            draw_lightbulb(screen, (self.help_rect.x + 22, self.help_rect.centery), 18, bulb_col)
            help_surf = small_font.render("HELP", True, bulb_col)
            screen.blit(help_surf, (self.help_rect.x + 40, self.help_rect.centery - help_surf.get_height() // 2))

            # Right CHECK button
            btn_w, btn_h = 160, 52
            self.check_rect = pygame.Rect(rect.right - btn_w - 30, rect.y + (rect.height - btn_h) // 2, btn_w, btn_h)
            
            if self.is_ready_to_check:
                draw_bevel_button(
                    screen, self.check_rect, "CHECK",
                    bg_color=GREEN_CORRECT,
                    bevel_color=GREEN_DARK,
                    text_color=TEXT_WHITE,
                    font=btn_font,
                    is_hovered=(self.hovered_btn == "check"),
                    is_pressed=(self.pressed_btn == "check"),
                    border_radius=14
                )
            else:
                draw_bevel_button(
                    screen, self.check_rect, "CHECK",
                    bg_color=(43, 56, 63),
                    bevel_color=(43, 56, 63),
                    text_color=(82, 101, 109),
                    font=btn_font,
                    is_disabled=True,
                    border_radius=14
                )

        # 2. In result state (Correct / Incorrect banner)
        else:
            banner_y = int(rect.y + self.banner_offset)
            banner_rect = pygame.Rect(rect.x, banner_y, rect.width, rect.height + 40)
            
            is_correct = (self.state == "correct")
            banner_bg = BANNER_CORRECT_BG if is_correct else BANNER_INCORRECT_BG
            pygame.draw.rect(screen, banner_bg, banner_rect)
            
            # Top border of banner
            border_col = (30, 70, 50) if is_correct else (80, 30, 35)
            pygame.draw.line(screen, border_col, (banner_rect.left, banner_rect.top), (banner_rect.right, banner_rect.top), 3)

            # Check/Cross badge icon on left
            badge_x = rect.x + 60
            badge_y = banner_y + rect.height // 2
            if is_correct:
                draw_check_badge(screen, (badge_x, badge_y), 22)
            else:
                draw_cross_badge(screen, (badge_x, badge_y), 22)

            # Message texts
            msg_font = get_font(24, bold=True)
            msg_color = GREEN_CORRECT if is_correct else RED_INCORRECT
            msg_surf = msg_font.render(self.feedback_message, True, msg_color)
            
            if is_correct:
                screen.blit(msg_surf, (badge_x + 36, badge_y - 20))
                # Report flag link
                rep_surf = small_font.render("⚐ REPORT", True, (119, 142, 155))
                screen.blit(rep_surf, (badge_x + 36, badge_y + 8))
            else:
                screen.blit(msg_surf, (badge_x + 36, badge_y - 22))
                if self.solution_hint:
                    hint_surf = small_font.render(f"Correct: {self.solution_hint}", True, TEXT_WHITE)
                    screen.blit(hint_surf, (badge_x + 36, badge_y + 8))

            # Right CONTINUE button
            btn_w, btn_h = 175, 52
            self.continue_rect = pygame.Rect(rect.right - btn_w - 30, banner_y + (rect.height - btn_h) // 2, btn_w, btn_h)
            draw_bevel_button(
                screen, self.continue_rect, "CONTINUE",
                bg_color=GREEN_CORRECT if is_correct else RED_INCORRECT,
                bevel_color=GREEN_DARK if is_correct else (180, 40, 40),
                text_color=TEXT_WHITE,
                font=btn_font,
                is_hovered=(self.hovered_btn == "continue"),
                is_pressed=(self.pressed_btn == "continue"),
                border_radius=14
            )
