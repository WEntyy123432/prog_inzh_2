import tkinter as tk
from tkinter import messagebox
import random

# ── Colors ──────────────────────────────────────────────────────────────
BG         = "#1e1e2e"
PANEL_BG   = "#2a2a3e"
BORDER     = "#3a3a5e"
WHITE      = "#e0e0f0"
MUTED      = "#8888aa"

A_COLOR    = "#4a9eff"   # blue  – player A
B_COLOR    = "#ff6b4a"   # coral – player B
MOVE_BG    = "#1a3a5e"   # dark blue – movable cell
MOVE_HOVER = "#254e7a"
ATK_BG     = "#5e1a1a"   # dark red – attackable cell
ATK_HOVER  = "#7a2525"
TELE_BG    = "#1a4a2a"   # dark green – teleport cell
TELE_HOVER = "#256635"
EMPTY_BG   = "#252538"
EMPTY_BDR  = "#33334a"

HP_A_BAR   = "#4a9eff"
HP_B_BAR   = "#ff6b4a"
HP_LOW     = "#ff4444"


# ── Game logic ───────────────────────────────────────────────────────────
class GameState:
    def __init__(self, rows, cols, name_a, atk_a, hp_a, name_b, atk_b, hp_b):
        self.rows = rows
        self.cols = cols
        self.players = {
            "A": {"name": name_a, "atk": atk_a, "hp": hp_a, "max_hp": hp_a, "row": 0, "col": 0},
            "B": {"name": name_b, "atk": atk_b, "hp": hp_b, "max_hp": hp_b, "row": 0, "col": 0},
        }
        self.turn = "A"
        self.teleports = set()
        self._place_players()
        self._gen_teleports()

    def _place_players(self):
        cells = [(r, c) for r in range(self.rows) for c in range(self.cols)]
        random.shuffle(cells)
        self.players["A"]["row"], self.players["A"]["col"] = cells[0]
        self.players["B"]["row"], self.players["B"]["col"] = cells[1]

    def _gen_teleports(self):
        occ = {(self.players["A"]["row"], self.players["A"]["col"]),
               (self.players["B"]["row"], self.players["B"]["col"])}
        free = [(r, c) for r in range(self.rows)
                for c in range(self.cols) if (r, c) not in occ]
        random.shuffle(free)
        self.teleports = set(tuple(x) for x in free[:3])

    def opponent(self):
        return "B" if self.turn == "A" else "A"

    def pos(self, key):
        p = self.players[key]
        return p["row"], p["col"]

    def is_adjacent(self, r1, c1, r2, c2):
        """Chebyshev distance == 1 means directly neighbouring (8 directions)."""
        return max(abs(r1 - r2), abs(c1 - c2)) == 1

    def movable_cells(self):
        """All 8 neighbours of current player that are NOT occupied by opponent."""
        pr, pc = self.pos(self.turn)
        opr, opc = self.pos(self.opponent())
        cells = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = pr + dr, pc + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if not (nr == opr and nc == opc):   # not occupied
                        cells.append((nr, nc))
        return cells

    def can_attack(self):
        """True if opponent is adjacent to current player."""
        pr, pc = self.pos(self.turn)
        opr, opc = self.pos(self.opponent())
        return self.is_adjacent(pr, pc, opr, opc)

    def do_move(self, r, c):
        p = self.players[self.turn]
        p["row"], p["col"] = r, c
        teleported = False
        if (r, c) in self.teleports:
            self._teleport_player()
            teleported = True
        return teleported

    def _teleport_player(self):
        opr, opc = self.pos(self.opponent())
        free = [(r, c) for r in range(self.rows)
                for c in range(self.cols)
                if not (r == opr and c == opc)]
        dest = random.choice(free)
        p = self.players[self.turn]
        p["row"], p["col"] = dest
        self._gen_teleports()
        return dest

    def do_attack(self):
        atk = self.players[self.turn]["atk"]
        opp = self.players[self.opponent()]
        opp["hp"] = max(0, opp["hp"] - atk)
        return opp["hp"]

    def end_turn(self):
        self.turn = self.opponent()

    def winner(self):
        for key in ("A", "B"):
            if self.players[key]["hp"] <= 0:
                opp = "B" if key == "A" else "A"
                return self.players[opp]["name"]
        return None


# ── Setup screen ─────────────────────────────────────────────────────────
class SetupScreen(tk.Frame):
    def __init__(self, master, on_start):
        super().__init__(master, bg=BG)
        self.on_start = on_start
        self._build()

    def _build(self):
        tk.Label(self, text="⚔  БИТВА НА СЕТКЕ", font=("Helvetica", 20, "bold"),
                 bg=BG, fg=WHITE).pack(pady=(24, 4))
        tk.Label(self, text="Настройте параметры и начните игру",
                 font=("Helvetica", 11), bg=BG, fg=MUTED).pack(pady=(0, 20))

        # Field size
        f_frame = tk.Frame(self, bg=PANEL_BG, bd=0, highlightthickness=1,
                           highlightbackground=BORDER)
        f_frame.pack(fill="x", padx=40, pady=(0, 12))
        tk.Label(f_frame, text="Размер поля", font=("Helvetica", 12, "bold"),
                 bg=PANEL_BG, fg=WHITE).pack(pady=(10, 4))
        row = tk.Frame(f_frame, bg=PANEL_BG)
        row.pack(pady=(0, 10))
        self.rows_var = self._spinbox(row, "Строк", 6, 3, 12)
        tk.Label(row, text=" × ", font=("Helvetica", 14), bg=PANEL_BG, fg=MUTED).pack(side="left")
        self.cols_var = self._spinbox(row, "Столбцов", 6, 3, 12)

        # Players
        players_frame = tk.Frame(self, bg=BG)
        players_frame.pack(fill="x", padx=40, pady=(0, 12))
        self.fields_a = self._player_panel(players_frame, "Игрок A", A_COLOR, "Игрок A", 10, 100)
        self.fields_a.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.fields_b = self._player_panel(players_frame, "Игрок B", B_COLOR, "Игрок B", 10, 100)
        self.fields_b.pack(side="left", fill="both", expand=True)

        btn = tk.Button(self, text="▶  Начать игру", font=("Helvetica", 13, "bold"),
                        bg=A_COLOR, fg="white", relief="flat", cursor="hand2",
                        activebackground="#2a7acc", activeforeground="white",
                        padx=24, pady=10, command=self._start)
        btn.pack(pady=16)

    def _spinbox(self, parent, label, default, lo, hi):
        tk.Label(parent, text=label, font=("Helvetica", 10), bg=PANEL_BG, fg=MUTED).pack(side="left")
        var = tk.IntVar(value=default)
        sb = tk.Spinbox(parent, from_=lo, to=hi, textvariable=var, width=4,
                        font=("Helvetica", 12), bg=PANEL_BG, fg=WHITE,
                        buttonbackground=PANEL_BG, relief="flat",
                        highlightthickness=1, highlightbackground=BORDER)
        sb.pack(side="left", padx=4)
        return var

    def _player_panel(self, parent, title, color, def_name, def_atk, def_hp):
        frame = tk.Frame(parent, bg=PANEL_BG, bd=0,
                         highlightthickness=2, highlightbackground=color)
        tk.Label(frame, text=title, font=("Helvetica", 12, "bold"),
                 bg=PANEL_BG, fg=color).pack(pady=(10, 4))

        fields = {}
        for label, key, default in [("Имя", "name", def_name),
                                     ("Сила удара", "atk", def_atk),
                                     ("Здоровье", "hp", def_hp)]:
            row = tk.Frame(frame, bg=PANEL_BG)
            row.pack(fill="x", padx=14, pady=3)
            tk.Label(row, text=label, font=("Helvetica", 10), bg=PANEL_BG,
                     fg=MUTED, width=10, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(default))
            e = tk.Entry(row, textvariable=var, font=("Helvetica", 11),
                         bg=EMPTY_BG, fg=WHITE, insertbackground=WHITE,
                         relief="flat", highlightthickness=1,
                         highlightbackground=BORDER, width=10)
            e.pack(side="left", padx=4)
            fields[key] = var
        tk.Label(frame, bg=PANEL_BG).pack(pady=4)
        frame.fields = fields
        return frame

    def _start(self):
        def iv(frame, key, default, lo=1):
            try:
                v = int(frame.fields[key].get())
                return max(lo, v)
            except ValueError:
                return default

        rows = max(3, min(12, self.rows_var.get()))
        cols = max(3, min(12, self.cols_var.get()))
        name_a = self.fields_a.fields["name"].get() or "Игрок A"
        name_b = self.fields_b.fields["name"].get() or "Игрок B"
        atk_a  = iv(self.fields_a, "atk", 10)
        hp_a   = iv(self.fields_a, "hp", 100, 10)
        atk_b  = iv(self.fields_b, "atk", 10)
        hp_b   = iv(self.fields_b, "hp", 100, 10)
        self.on_start(rows, cols, name_a, atk_a, hp_a, name_b, atk_b, hp_b)


# ── Game screen ───────────────────────────────────────────────────────────
CELL = 64   # pixel size of each cell

class GameScreen(tk.Frame):
    def __init__(self, master, gs: GameState, on_new_game):
        super().__init__(master, bg=BG)
        self.gs = gs
        self.on_new_game = on_new_game
        self.buttons = {}   # (r,c) -> tk.Button
        self._build()
        self._render()

    def _build(self):
        # ── Top HUD ──────────────────────────────────────────────────────
        hud = tk.Frame(self, bg=BG)
        hud.pack(fill="x", padx=16, pady=(12, 6))

        self.card_a = self._hp_card(hud, "A")
        self.card_a.pack(side="left", fill="both", expand=True, padx=(0, 6))

        mid = tk.Frame(hud, bg=PANEL_BG, highlightthickness=1,
                       highlightbackground=BORDER)
        mid.pack(side="left", padx=4, ipadx=10, ipady=6)
        tk.Label(mid, text="ХОД", font=("Helvetica", 9), bg=PANEL_BG, fg=MUTED).pack()
        self.turn_lbl = tk.Label(mid, text="", font=("Helvetica", 14, "bold"),
                                 bg=PANEL_BG, fg=WHITE)
        self.turn_lbl.pack()
        self.hint_lbl = tk.Label(mid, text="", font=("Helvetica", 9),
                                 bg=PANEL_BG, fg=MUTED, wraplength=90)
        self.hint_lbl.pack()

        self.card_b = self._hp_card(hud, "B")
        self.card_b.pack(side="left", fill="both", expand=True, padx=(6, 0))

        # ── Legend ───────────────────────────────────────────────────────
        leg = tk.Frame(self, bg=BG)
        leg.pack(fill="x", padx=16, pady=(0, 6))
        for color, text in [(A_COLOR, "Ты (ход)"),
                             (B_COLOR, "Противник"),
                             (MOVE_HOVER, "Перейти"),
                             (ATK_HOVER, "Атаковать!"),
                             (TELE_HOVER, "Телепорт")]:
            item = tk.Frame(leg, bg=BG)
            item.pack(side="left", padx=8)
            tk.Label(item, bg=color, width=2, height=1).pack(side="left")
            tk.Label(item, text=text, font=("Helvetica", 9),
                     bg=BG, fg=MUTED).pack(side="left", padx=3)

        # ── Board ─────────────────────────────────────────────────────────
        board_wrap = tk.Frame(self, bg=BG)
        board_wrap.pack(padx=16, pady=4)
        self.board_frame = tk.Frame(board_wrap, bg=BORDER)
        self.board_frame.pack()

        # ── Log ──────────────────────────────────────────────────────────
        log_frame = tk.Frame(self, bg=PANEL_BG, highlightthickness=1,
                             highlightbackground=BORDER)
        log_frame.pack(fill="x", padx=16, pady=(6, 4))
        tk.Label(log_frame, text="Журнал событий", font=("Helvetica", 9, "bold"),
                 bg=PANEL_BG, fg=MUTED).pack(anchor="w", padx=8, pady=(4, 0))
        self.log_text = tk.Text(log_frame, height=5, font=("Helvetica", 10),
                                bg=PANEL_BG, fg=WHITE, relief="flat",
                                state="disabled", wrap="word")
        self.log_text.pack(fill="x", padx=8, pady=(0, 6))
        self.log_text.tag_config("a",   foreground=A_COLOR)
        self.log_text.tag_config("b",   foreground=B_COLOR)
        self.log_text.tag_config("tele", foreground="#66cc88")
        self.log_text.tag_config("sys", foreground=MUTED)

        # ── New game button ───────────────────────────────────────────────
        tk.Button(self, text="Новая игра", font=("Helvetica", 10),
                  bg=PANEL_BG, fg=WHITE, relief="flat", cursor="hand2",
                  highlightthickness=1, highlightbackground=BORDER,
                  command=self.on_new_game).pack(pady=(2, 12))

    def _hp_card(self, parent, key):
        color = A_COLOR if key == "A" else B_COLOR
        frame = tk.Frame(parent, bg=PANEL_BG, highlightthickness=2,
                         highlightbackground=color)
        p = self.gs.players[key]

        lbl_name = tk.Label(frame, text=p["name"], font=("Helvetica", 11, "bold"),
                            bg=PANEL_BG, fg=color)
        lbl_name.pack(pady=(6, 0))

        lbl_hp = tk.Label(frame, text=f"{p['hp']} HP",
                          font=("Helvetica", 13, "bold"), bg=PANEL_BG, fg=WHITE)
        lbl_hp.pack()

        lbl_atk = tk.Label(frame, text=f"Атака: {p['atk']}",
                           font=("Helvetica", 9), bg=PANEL_BG, fg=MUTED)
        lbl_atk.pack()

        bar_bg = tk.Frame(frame, bg=EMPTY_BG, height=6)
        bar_bg.pack(fill="x", padx=10, pady=(4, 8))
        bar_fg = tk.Frame(bar_bg, bg=color, height=6)
        bar_fg.place(relx=0, rely=0, relwidth=1.0, relheight=1.0)

        frame.lbl_hp  = lbl_hp
        frame.bar_fg  = bar_fg
        frame.bar_color = color
        frame.key     = key
        return frame

    def _update_hp_card(self, card):
        p = self.gs.players[card.key]
        card.lbl_hp.config(text=f"{p['hp']} HP")
        ratio = p["hp"] / p["max_hp"]
        color = HP_LOW if ratio < 0.3 else card.bar_color
        card.bar_fg.config(bg=color)
        card.bar_fg.place(relwidth=max(0, ratio))

    # ── Board rendering ───────────────────────────────────────────────────
    def _render(self):
        gs = self.gs
        turn = gs.turn
        opp  = gs.opponent()

        # Compute valid actions
        movable  = set(gs.movable_cells())
        can_atk  = gs.can_attack()
        opp_pos  = gs.pos(opp)
        cur_pos  = gs.pos(turn)

        # Destroy old buttons and rebuild
        for w in self.board_frame.winfo_children():
            w.destroy()
        self.buttons = {}

        for r in range(gs.rows):
            for c in range(gs.cols):
                pos = (r, c)
                is_current  = pos == cur_pos
                is_opponent = pos == opp_pos
                is_tele     = pos in gs.teleports
                is_movable  = pos in movable
                is_attack   = is_opponent and can_atk

                # Determine cell appearance
                if is_current:
                    bg    = A_COLOR if turn == "A" else B_COLOR
                    fg    = "white"
                    text  = turn
                    hover = bg
                    cmd   = None
                elif is_attack:
                    bg    = ATK_BG
                    fg    = "#ff9999"
                    text  = "✕\nАТАКА"
                    hover = ATK_HOVER
                    cmd   = self._make_attack_cmd()
                elif is_opponent:
                    bg    = B_COLOR if opp == "B" else A_COLOR
                    fg    = "white"
                    text  = opp
                    hover = bg
                    cmd   = None
                elif is_movable and is_tele:
                    bg    = TELE_BG
                    fg    = "#88ffaa"
                    text  = "T\nТЕЛЕП."
                    hover = TELE_HOVER
                    cmd   = self._make_move_cmd(r, c)
                elif is_movable:
                    bg    = MOVE_BG
                    fg    = "#88bbff"
                    text  = "·"
                    hover = MOVE_HOVER
                    cmd   = self._make_move_cmd(r, c)
                elif is_tele:
                    bg    = "#162a1e"
                    fg    = "#446655"
                    text  = "T"
                    hover = bg
                    cmd   = None
                else:
                    bg    = EMPTY_BG
                    fg    = EMPTY_BDR
                    text  = ""
                    hover = EMPTY_BG
                    cmd   = None

                btn = tk.Button(
                    self.board_frame,
                    text=text,
                    font=("Helvetica", 11, "bold"),
                    width=4, height=2,
                    bg=bg, fg=fg,
                    activebackground=hover,
                    activeforeground=fg,
                    relief="flat",
                    highlightthickness=1,
                    highlightbackground=BORDER,
                    cursor="hand2" if cmd else "arrow",
                    command=cmd if cmd else lambda: None,
                    state="normal" if cmd else "disabled",
                    disabledforeground=fg,
                )
                btn.grid(row=r, column=c, padx=1, pady=1)
                self.buttons[pos] = btn

        # Update HUD
        self._update_hp_card(self.card_a)
        self._update_hp_card(self.card_b)
        p = gs.players[turn]
        self.turn_lbl.config(text=p["name"],
                             fg=A_COLOR if turn == "A" else B_COLOR)
        if can_atk:
            self.hint_lbl.config(text="Противник рядом!\nНажми ✕ для атаки")
        else:
            self.hint_lbl.config(text="Нажми синюю клетку\nдля хода")

    def _make_move_cmd(self, r, c):
        def cmd():
            gs = self.gs
            name = gs.players[gs.turn]["name"]
            old  = gs.pos(gs.turn)
            teleported = gs.do_move(r, c)
            if teleported:
                new = gs.pos(gs.turn)
                self._log(f"{name} перешёл → ({r+1},{c+1}) и телепортировался на ({new[0]+1},{new[1]+1})!", "tele")
            else:
                self._log(f"{name}: ({old[0]+1},{old[1]+1}) → ({r+1},{c+1})", gs.turn.lower())
            gs.end_turn()
            self._render()
        return cmd

    def _make_attack_cmd(self):
        def cmd():
            gs = self.gs
            atk_name = gs.players[gs.turn]["name"]
            def_name = gs.players[gs.opponent()]["name"]
            dmg      = gs.players[gs.turn]["atk"]
            rem_hp   = gs.do_attack()
            tag = gs.turn.lower()
            self._log(f"{atk_name} бьёт {def_name}! -{dmg} HP. Осталось: {rem_hp} HP", tag)
            self._update_hp_card(self.card_a)
            self._update_hp_card(self.card_b)
            winner = gs.winner()
            if winner:
                self._log(f"*** {winner} ПОБЕДИЛ! ***", "sys")
                self._render()
                messagebox.showinfo("Игра окончена", f"🏆  {winner} победил!")
                self.on_new_game()
                return
            gs.end_turn()
            self._render()
        return cmd

    def _log(self, msg, tag="sys"):
        self.log_text.config(state="normal")
        self.log_text.insert("1.0", msg + "\n", tag)
        self.log_text.config(state="disabled")


# ── Main application ──────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚔  Битва на сетке")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._show_setup()

    def _show_setup(self):
        for w in self.winfo_children():
            w.destroy()
        SetupScreen(self, self._start_game).pack(fill="both", expand=True)
        self.update_idletasks()
        self.minsize(460, 480)

    def _start_game(self, rows, cols, name_a, atk_a, hp_a, name_b, atk_b, hp_b):
        gs = GameState(rows, cols, name_a, atk_a, hp_a, name_b, atk_b, hp_b)
        for w in self.winfo_children():
            w.destroy()
        GameScreen(self, gs, self._show_setup).pack(fill="both", expand=True)
        self.update_idletasks()
        w = cols * (CELL + 2) + 48
        h = rows * (CELL + 2) + 340
        self.geometry(f"{w}x{h}")
        self.minsize(w, h)


if __name__ == "__main__":
    App().mainloop()
