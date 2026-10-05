"""EduMath Pygame Application: Gamified interactive math learning system.
Faithfully reproduces the Duolingo Math interface and mechanics from the example screenshots.
"""
from typing import List, Optional
import pygame
from .theme import (
    BG_COLOR,
    CARD_BG,
    CARD_BORDER,
    CARD_HOVER,
    CARD_SELECTED_BG,
    CARD_SELECTED_BORDER,
    GREEN_CORRECT,
    GREEN_DARK,
    ACCENT_BLUE,
    TEXT_WHITE,
    TEXT_MUTED,
    get_font,
    draw_rounded_rect,
    draw_bevel_button,
    draw_check_badge
)
from .components import (
    Header,
    BottomBar,
    HelpModal,
    CalculatorWidget,
    ConfettiSystem,
    GeneratorMenu
)
from .exercises import BaseExercise
from .lessons import create_default_curriculum
from .generator import MathGenerator
from .sound import sound_manager

class EduApp:
    """Main application manager for the EduMath educational experience."""

    def __init__(
        self,
        width: int = 1200,
        height: int = 850,
        exercises: Optional[List[BaseExercise]] = None,
        title: str = "EduMath - Interactive Math Learning"
    ):
        self.width = width
        self.height = height
        self.title = title
        
        # Display & timing
        self.screen: Optional[pygame.Surface] = None
        self.clock: Optional[pygame.time.Clock] = None
        self.is_running: bool = False
        
        # Curriculum & state
        self.exercises = exercises or create_default_curriculum()
        self.current_index: int = 0
        self.streak: int = 0
        self.max_streak: int = 0
        self.correct_count: int = 0
        self.is_lesson_finished: bool = False
        self.show_level_select: bool = False

        # Components
        self.header = Header()
        self.bottom_bar = BottomBar()
        self.help_modal = HelpModal()
        self.calculator = CalculatorWidget()
        self.confetti = ConfettiSystem()
        self.generator_menu = GeneratorMenu()

        # Update initial progress
        self._sync_progress()

    def set_curriculum(self, exercises: List[BaseExercise]) -> None:
        """Replaces current exercises with a new curriculum or generated set."""
        if not exercises:
            return
        self.exercises = exercises
        self.current_index = 0
        self.streak = 0
        self.max_streak = 0
        self.correct_count = 0
        self.is_lesson_finished = False
        self.show_level_select = False
        self.current_exercise.reset()
        self._sync_progress()

    @property
    def current_exercise(self) -> BaseExercise:
        return self.exercises[self.current_index]

    def _sync_progress(self) -> None:
        self.header.set_progress(
            current=self.current_index,
            total=len(self.exercises),
            streak=self.streak
        )
        self.bottom_bar.set_state("question")
        self.bottom_bar.is_ready_to_check = self.current_exercise.is_ready_to_check()

    def init_pygame(self) -> None:
        pygame.init()
        pygame.display.set_caption(self.title)
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()

    def run(self) -> None:
        if self.screen is None:
            self.init_pygame()

        self.is_running = True
        while self.is_running:
            dt = self.clock.tick(60) / 1000.0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                else:
                    self.handle_event(event)
                    
            self.update(dt)
            self.draw()
            pygame.display.flip()
            
        pygame.quit()

    def handle_event(self, event: pygame.event.Event) -> None:
        # 0. Generator Menu has priority when open
        if self.generator_menu.is_open:
            menu_res = self.generator_menu.handle_event(event)
            if menu_res is not None:
                op, diff, count = menu_res
                if op == "curriculum":
                    self.set_curriculum(create_default_curriculum())
                else:
                    self.set_curriculum(MathGenerator.generate_lesson(op, diff, count))
            return

        # Global Hotkeys
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.generator_menu.open()
                return
            elif event.key == pygame.K_l:
                self.show_level_select = not self.show_level_select
                return
            elif event.key == pygame.K_h:
                if self.help_modal.is_open:
                    self.help_modal.close()
                else:
                    self._open_help()
                return
            elif event.key in (pygame.K_c, pygame.K_t):
                self.calculator.toggle()
                return
            elif event.key == pygame.K_r:
                self.current_exercise.reset()
                self._sync_progress()
                return
            elif event.key == pygame.K_n and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self._next_exercise()
                return
            elif event.key == pygame.K_p and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self._prev_exercise()
                return

        # 1. Level select modal
        if self.show_level_select:
            self._handle_level_select_event(event)
            return

        # 2. Victory screen modal
        if self.is_lesson_finished:
            self._handle_victory_event(event)
            return

        # 3. Help modal has high priority
        if self.help_modal.is_open:
            if self.help_modal.handle_event(event):
                return

        # 4. Calculator panel
        calc_res = self.calculator.handle_event(event)
        if calc_res is not None:
            # If current exercise accepts typing, forward character
            if hasattr(self.current_exercise, "append_char"):
                self.current_exercise.append_char(calc_res)

        # 5. Header events (close / menu clicked)
        hdr_action = self.header.handle_event(event)
        if hdr_action == "close":
            self.generator_menu.open()
            return

        # 6. Bottom bar events (check / continue / help / toolkit)
        bar_action = self.bottom_bar.handle_event(event)
        if bar_action == "check":
            self._on_check_answer()
            return
        elif bar_action == "continue":
            self._on_continue()
            return
        elif bar_action == "help":
            self._open_help()
            return
        elif bar_action == "toolkit":
            self.calculator.toggle()
            return

        # 7. Exercise area events (if not already answered and banner open)
        if self.bottom_bar.state == "question":
            self.current_exercise.handle_event(event)
            # Recheck readiness
            self.bottom_bar.is_ready_to_check = self.current_exercise.is_ready_to_check()

    def _open_help(self) -> None:
        ex = self.current_exercise
        self.help_modal.show(
            title=ex.help_title,
            main_tip=ex.help_tip,
            faqs=ex.help_faqs
        )

    def _on_check_answer(self) -> None:
        ex = self.current_exercise
        is_correct = ex.check()
        msg, hint = ex.get_feedback()
        
        if is_correct:
            self.streak += 1
            self.max_streak = max(self.max_streak, self.streak)
            self.correct_count += 1
            sound_manager.play_correct()
            self.bottom_bar.set_state("correct", message=msg, solution_hint=hint)
            # Launch confetti burst from bottom check area!
            self.confetti.burst(self.width - 120, self.height - 80, count=45)
        else:
            self.streak = 0
            sound_manager.play_error()
            self.bottom_bar.set_state("incorrect", message=msg, solution_hint=hint)
            
        self.header.set_progress(self.current_index, len(self.exercises), self.streak)

    def _on_continue(self) -> None:
        self._next_exercise()

    def _next_exercise(self) -> None:
        if self.current_index < len(self.exercises) - 1:
            self.current_index += 1
            self._sync_progress()
        else:
            # Finished all exercises!
            self.is_lesson_finished = True
            sound_manager.play_correct()
            self.confetti.burst(self.width // 2, self.height // 2, count=90)

    def _prev_exercise(self) -> None:
        if self.current_index > 0:
            self.current_index -= 1
            self._sync_progress()

    def jump_to_level(self, index: int) -> None:
        if 0 <= index < len(self.exercises):
            self.current_index = index
            self.current_exercise.reset()
            self.is_lesson_finished = False
            self.show_level_select = False
            self._sync_progress()

    def update(self, dt: float) -> None:
        self.header.update(dt)
        self.bottom_bar.update(dt)
        self.calculator.update(dt)
        self.confetti.update(dt)
        if not self.is_lesson_finished and not self.show_level_select:
            self.current_exercise.update(dt)
            self.bottom_bar.is_ready_to_check = self.current_exercise.is_ready_to_check()

    def draw(self) -> None:
        if self.screen is None:
            return

        # 1. Background
        self.screen.fill(BG_COLOR)

        screen_rect = pygame.Rect(0, 0, self.width, self.height)
        header_rect = pygame.Rect(0, 0, self.width, 70)
        bottom_rect = pygame.Rect(0, self.height - 90, self.width, 90)
        exercise_rect = pygame.Rect(0, 70, self.width, self.height - 160)

        # 2. Main Exercise Area
        self.current_exercise.draw(self.screen, exercise_rect)

        # 3. Confetti particles
        self.confetti.draw(self.screen)

        # 4. Header Bar
        self.header.draw(self.screen, header_rect)

        # 5. Bottom Action & Feedback Bar
        self.bottom_bar.draw(self.screen, bottom_rect)

        # 6. Side Calculator Widget
        self.calculator.draw(self.screen, screen_rect)

        # 7. Help Modal Overlay
        self.help_modal.draw(self.screen, screen_rect)

        # 8. Level Select Overlay
        if self.show_level_select:
            self._draw_level_select(self.screen, screen_rect)

        # 9. Generator Menu Overlay
        if self.generator_menu.is_open:
            self.generator_menu.draw(self.screen, screen_rect)

        # 10. Lesson Finished Victory Screen
        if self.is_lesson_finished:
            self._draw_victory_screen(self.screen, screen_rect)

    def _draw_level_select(self, screen: pygame.Surface, screen_rect: pygame.Rect) -> None:
        dim = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        screen.blit(dim, (0, 0))

        mw, mh = min(880, screen_rect.width - 60), min(640, screen_rect.height - 60)
        mx = (screen_rect.width - mw) // 2
        my = (screen_rect.height - mh) // 2
        modal_rect = pygame.Rect(mx, my, mw, mh)
        draw_rounded_rect(screen, modal_rect, CARD_BG, radius=18, border_color=CARD_BORDER, border_width=2)

        # Title
        f_title = get_font(28, bold=True)
        t_surf = f_title.render("Jump to Exercise", True, TEXT_WHITE)
        screen.blit(t_surf, t_surf.get_rect(center=(mx + mw // 2, my + 38)))

        # Close X on top right
        close_font = get_font(22, bold=True)
        cx_surf = close_font.render("✕", True, TEXT_MUTED)
        self.level_select_close_rect = pygame.Rect(mx + mw - 46, my + 20, 30, 30)
        screen.blit(cx_surf, cx_surf.get_rect(center=self.level_select_close_rect.center))

        # Grid of levels (4 columns x 4 rows)
        self.level_buttons = []
        cols = 4
        rows = 4
        gw = (mw - 70 - (cols - 1) * 14) // cols
        gh = (mh - 160 - (rows - 1) * 14) // rows
        start_x = mx + 35
        start_y = my + 72
        f_btn = get_font(16, bold=True)

        for i, ex in enumerate(self.exercises):
            r = i // cols
            c = i % cols
            brect = pygame.Rect(start_x + c * (gw + 14), start_y + r * (gh + 14), gw, gh)
            is_cur = (i == self.current_index)
            bg = CARD_SELECTED_BG if is_cur else (32, 47, 54)
            border = CARD_SELECTED_BORDER if is_cur else CARD_BORDER
            draw_rounded_rect(screen, brect, bg, radius=12, border_color=border, border_width=2)

            num_surf = f_btn.render(f"#{i+1}", True, ACCENT_BLUE if is_cur else TEXT_WHITE)
            screen.blit(num_surf, (brect.x + 12, brect.y + 10))

            # Truncated title
            title_txt = ex.title
            if len(title_txt) > 16:
                title_txt = title_txt[:14] + ".."
            lbl_surf = get_font(13).render(title_txt, True, TEXT_MUTED)
            screen.blit(lbl_surf, (brect.x + 12, brect.y + 36))

            self.level_buttons.append((brect, i))

        # Bottom Switch to Generator Button
        self.level_switch_gen_rect = pygame.Rect(mx + mw // 2 - 130, my + mh - 58, 260, 44)
        draw_bevel_button(
            screen, self.level_switch_gen_rect, "⚙ GENERATOR MENU",
            bg_color=ACCENT_BLUE, bevel_color=(20, 140, 200),
            text_color=TEXT_WHITE, font=get_font(16, bold=True), border_radius=12
        )

    def _handle_level_select_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_l):
            self.show_level_select = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if hasattr(self, "level_select_close_rect") and self.level_select_close_rect.collidepoint(pos):
                self.show_level_select = False
                sound_manager.play_click()
                return
            if hasattr(self, "level_switch_gen_rect") and self.level_switch_gen_rect.collidepoint(pos):
                self.show_level_select = False
                self.generator_menu.open()
                sound_manager.play_click()
                return
            for brect, idx in getattr(self, "level_buttons", []):
                if brect.collidepoint(pos):
                    sound_manager.play_snap()
                    self.jump_to_level(idx)
                    return

    def _draw_victory_screen(self, screen: pygame.Surface, screen_rect: pygame.Rect) -> None:
        dim = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 190))
        screen.blit(dim, (0, 0))

        mw, mh = min(620, screen_rect.width - 40), 400
        mx = (screen_rect.width - mw) // 2
        my = (screen_rect.height - mh) // 2
        modal_rect = pygame.Rect(mx, my, mw, mh)
        draw_rounded_rect(screen, modal_rect, CARD_BG, radius=20, border_color=GREEN_CORRECT, border_width=3)

        # Big check badge
        draw_check_badge(screen, (mx + mw // 2, my + 60), 36)

        # Celebratory title
        t_font = get_font(32, bold=True)
        t_surf = t_font.render("Lesson Complete!", True, GREEN_CORRECT)
        screen.blit(t_surf, t_surf.get_rect(center=(mx + mw // 2, my + 130)))

        # Stats
        st_font = get_font(20, bold=True)
        total = len(self.exercises)
        acc_pct = int((self.correct_count / max(1, total)) * 100)
        stats_str = f"Score: {self.correct_count}/{total} ({acc_pct}%)  •  Max Streak: {self.max_streak}"
        st_surf = st_font.render(stats_str, True, TEXT_WHITE)
        screen.blit(st_surf, st_surf.get_rect(center=(mx + mw // 2, my + 185)))

        # Subtitle
        sub_font = get_font(16)
        sub_surf = sub_font.render("Great practice! Continue to sharpen your skills.", True, TEXT_MUTED)
        screen.blit(sub_surf, sub_surf.get_rect(center=(mx + mw // 2, my + 225)))

        # 3 Action Buttons: REPLAY, GENERATOR, LEVELS
        btn_font = get_font(16, bold=True)
        btn_y = my + 280
        btn_h = 52
        
        self.restart_rect = pygame.Rect(mx + 40, btn_y, 160, btn_h)
        draw_bevel_button(
            screen, self.restart_rect, "REPLAY",
            bg_color=CARD_BG, bevel_color=(32, 47, 54),
            text_color=TEXT_WHITE, font=btn_font, border_radius=14
        )

        self.menu_btn_rect = pygame.Rect(mx + 220, btn_y, 200, btn_h)
        draw_bevel_button(
            screen, self.menu_btn_rect, "GENERATOR MENU",
            bg_color=GREEN_CORRECT, bevel_color=GREEN_DARK,
            text_color=TEXT_WHITE, font=btn_font, border_radius=14
        )

        self.levels_btn_rect = pygame.Rect(mx + 440, btn_y, 140, btn_h)
        draw_bevel_button(
            screen, self.levels_btn_rect, "LEVELS",
            bg_color=ACCENT_BLUE, bevel_color=(20, 140, 200),
            text_color=TEXT_WHITE, font=btn_font, border_radius=14
        )

    def _handle_victory_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if hasattr(self, "restart_rect") and self.restart_rect.collidepoint(pos):
                sound_manager.play_click()
                self.correct_count = 0
                self.streak = 0
                self.jump_to_level(0)
            elif hasattr(self, "menu_btn_rect") and self.menu_btn_rect.collidepoint(pos):
                sound_manager.play_click()
                self.is_lesson_finished = False
                self.generator_menu.open()
            elif hasattr(self, "levels_btn_rect") and self.levels_btn_rect.collidepoint(pos):
                sound_manager.play_click()
                self.is_lesson_finished = False
                self.show_level_select = True
