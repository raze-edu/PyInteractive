"""Help dialog modal with friendly character avatar, speech bubble, and tips."""
from typing import List, Optional, Tuple
import pygame
from ..theme import (
    get_font,
    draw_rounded_rect,
    draw_bevel_button,
    CARD_BG,
    CARD_BORDER,
    ACCENT_BLUE,
    TEXT_WHITE,
    TEXT_MUTED
)
from ..sound import sound_manager

class HelpModal:
    """Friendly character tip modal dialog matching Duolingo style."""
    
    def __init__(self):
        self.is_open: bool = False
        self.title: str = "Need a hand?"
        self.tips: List[str] = []
        self.active_tab: int = 0
        self.done_rect = pygame.Rect(0, 0, 200, 50)
        self.done_hovered: bool = False
        self.done_pressed: bool = False
        self.faq_buttons: List[Tuple[pygame.Rect, str, str]] = []  # (rect, question, answer)
        self.selected_answer: str = ""

    def show(self, title: str, main_tip: str, faqs: Optional[List[Tuple[str, str]]] = None) -> None:
        self.title = title
        self.is_open = True
        self.selected_answer = main_tip
        self.faq_data = faqs or []
        self.faq_buttons = []

    def close(self) -> None:
        self.is_open = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if modal swallowed the event."""
        if not self.is_open:
            return False

        if event.type == pygame.MOUSEMOTION:
            pos = event.pos
            self.done_hovered = self.done_rect.collidepoint(pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.done_rect.collidepoint(pos):
                self.done_pressed = True
                sound_manager.play_click()
                self.close()
                return True
                
            # Check FAQ question pill clicks
            for rect, q, a in self.faq_buttons:
                if rect.collidepoint(pos):
                    sound_manager.play_click()
                    self.selected_answer = a
                    return True
            return True  # Consume click outside modal

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.done_pressed = False
            return True

        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.close()
                return True
            return True

        return True

    def _draw_character(self, surface: pygame.Surface, x: int, y: int, size: int = 60) -> None:
        """Draws a cute stylized Duolingo avatar head with crown/hijab."""
        cx = x + size // 2
        cy = y + size // 2
        
        # Body / shoulders
        body_rect = pygame.Rect(cx - 24, cy + 14, 48, 30)
        pygame.draw.rect(surface, (235, 120, 150), body_rect, border_radius=12)
        
        # Face
        pygame.draw.circle(surface, (255, 205, 175), (cx, cy), 22)
        # Hair / cap
        pygame.draw.arc(surface, (230, 80, 120), (cx - 24, cy - 25, 48, 44), 0, 3.1415, 8)
        # Crown / ornament
        crown_rect = pygame.Rect(cx - 18, cy - 30, 36, 12)
        pygame.draw.rect(surface, (255, 200, 0), crown_rect, border_radius=4)
        
        # Cute cartoon eyes
        pygame.draw.circle(surface, (40, 40, 50), (cx - 8, cy - 2), 4)
        pygame.draw.circle(surface, (40, 40, 50), (cx + 8, cy - 2), 4)
        pygame.draw.circle(surface, (255, 255, 255), (cx - 7, cy - 4), 1)
        pygame.draw.circle(surface, (255, 255, 255), (cx + 9, cy - 4), 1)
        # Smile
        pygame.draw.arc(surface, (180, 50, 50), (cx - 6, cy + 2, 12, 8), 3.1415, 0, 2)

    def draw(self, screen: pygame.Surface, screen_rect: pygame.Rect) -> None:
        if not self.is_open:
            return

        # Dim background
        dim_surf = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 160))
        screen.blit(dim_surf, (0, 0))

        # Modal window container
        mw, mh = min(720, screen_rect.width - 60), min(420, screen_rect.height - 80)
        mx = (screen_rect.width - mw) // 2
        my = (screen_rect.height - mh) // 2
        modal_rect = pygame.Rect(mx, my, mw, mh)

        draw_rounded_rect(screen, modal_rect, (24, 39, 46), radius=20, border_color=(43, 61, 71), border_width=2)

        # Character avatar on left
        char_x = mx + 36
        char_y = my + 44
        self._draw_character(screen, char_x, char_y, 70)

        # Speech bubble
        bubble_x = char_x + 95
        bubble_y = my + 36
        bubble_w = mw - 160
        bubble_h = 130
        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
        draw_rounded_rect(screen, bubble_rect, (32, 47, 54), radius=16, border_color=(53, 72, 81), border_width=2)

        # Bubble pointer triangle towards character
        triangle_pts = [
            (bubble_x, bubble_y + 35),
            (bubble_x - 14, bubble_y + 45),
            (bubble_x, bubble_y + 55)
        ]
        pygame.draw.polygon(screen, (32, 47, 54), triangle_pts)
        pygame.draw.line(screen, (53, 72, 81), (bubble_x - 14, bubble_y + 45), (bubble_x, bubble_y + 35), 2)
        pygame.draw.line(screen, (53, 72, 81), (bubble_x - 14, bubble_y + 45), (bubble_x, bubble_y + 55), 2)

        # Text inside bubble (multi-line wrapping)
        font = get_font(19)
        words = self.selected_answer.split()
        lines = []
        cur_line = []
        max_line_w = bubble_w - 40
        for w in words:
            test_line = " ".join(cur_line + [w])
            if font.size(test_line)[0] > max_line_w and cur_line:
                lines.append(" ".join(cur_line))
                cur_line = [w]
            else:
                cur_line.append(w)
        if cur_line:
            lines.append(" ".join(cur_line))

        ty = bubble_y + 24
        for line in lines:
            line_surf = font.render(line, True, TEXT_WHITE)
            screen.blit(line_surf, (bubble_x + 20, ty))
            ty += font.get_linesize() + 4

        # FAQ Question Pills
        self.faq_buttons = []
        pill_font = get_font(15, bold=True)
        py_start = bubble_rect.bottom + 20
        px = mx + 40
        for q, a in self.faq_data:
            q_surf = pill_font.render(q, True, (28, 176, 246))
            pw = q_surf.get_width() + 32
            ph = 40
            prect = pygame.Rect(px, py_start, pw, ph)
            is_active = (self.selected_answer == a)
            p_bg = (28, 60, 75) if is_active else (32, 47, 54)
            p_border = (28, 176, 246) if is_active else (53, 72, 81)
            draw_rounded_rect(screen, prect, p_bg, radius=12, border_color=p_border, border_width=2)
            screen.blit(q_surf, q_surf.get_rect(center=prect.center))
            self.faq_buttons.append((prect, q, a))
            px += pw + 14

        # Bottom "DONE" button
        self.done_rect = pygame.Rect(mx + 40, my + mh - 70, mw - 80, 50)
        draw_bevel_button(
            screen, self.done_rect, "DONE",
            bg_color=ACCENT_BLUE,
            bevel_color=(20, 140, 200),
            text_color=TEXT_WHITE,
            font=get_font(20, bold=True),
            is_hovered=self.done_hovered,
            is_pressed=self.done_pressed,
            border_radius=14
        )
