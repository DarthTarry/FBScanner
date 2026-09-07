"""
USCIS N-400 Civics Test Study Desktop App (2025 Official Version - 128 Questions)
Designed and Developed by DarthTarry® (https://github.com/DarthTarry)
Features:
 - 128 Official 2025 USCIS Civics Questions & Answers
 - Star-Spangled Banner Dark USA Theme
 - User Feedback Section sending email to arun.vijayaraghavan1982@gmail.com
 - 65/20 Special Consideration Indicator (20 Questions)
 - Rich Historical Context & Explanations for Every Answer
 - Flashcard Mode with Card Flip & Category Filters
 - Practice Quiz Mode (Multiple Choice & Type-In, Passing Score Tracker, Pass/Fail Result)
 - Flagged & Missed Questions Manager (Retry Missed Questions)
 - Persistent Study Progress & Flagged List
"""

import json
import os
import random
import re
import sys
import urllib.parse
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, font

def load_civics_questions():
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "n400_civics_questions.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading n400_civics_questions.json: {e}")
    return []

USCIS_QUESTIONS = load_civics_questions()


class USCISStudyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("USCIS Civics N-400 Study Assistant (2025 Version - 128 Questions)")
        self.root.geometry("840x840")
        self.root.minsize(520, 680)

        # File path for user progress & flagged questions
        self.progress_file = os.path.join(os.path.dirname(__file__), "uscis_user_progress.json")
        self.load_progress()

        # Data & state variables
        self.questions = USCIS_QUESTIONS if USCIS_QUESTIONS else []
        self.flashcard_index = 0
        self.flashcard_showing_answer = False
        self.filtered_flashcards = list(self.questions)

        # Quiz state
        self.quiz_queue = []
        self.quiz_index = 0
        self.quiz_score = 0
        self.quiz_mode_type = "mc"  # "mc" or "text"
        self.quiz_total = 20
        self.quiz_pass_mark = 12
        self.quiz_history = []  # tracks current quiz answers

        # Setup GUI styling
        self.setup_styles()
        self.create_widgets()

    def load_progress(self):
        """Loads persistent user progress and flagged questions."""
        self.flagged_ids = set()
        self.missed_history = {}  # {qid: miss_count}
        self.stats = {"quizzes_taken": 0, "quizzes_passed": 0, "total_correct": 0, "total_answered": 0}

        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.flagged_ids = set(data.get("flagged_ids", []))
                    self.missed_history = data.get("missed_history", {})
                    self.stats = data.get("stats", self.stats)
            except Exception as e:
                print(f"Error loading progress file: {e}")

    def save_progress(self):
        """Saves flagged questions and study stats to disk."""
        data = {
            "flagged_ids": list(self.flagged_ids),
            "missed_history": self.missed_history,
            "stats": self.stats
        }
        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving progress file: {e}")

    def setup_styles(self):
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")

        # Dark Star-Spangled Banner USA Color Palette
        self.BG_COLOR = "#0b132b"       # Deep Midnight Navy
        self.NAVY_HEADER = "#1c2541"   # Header Navy
        self.CARD_BG = "#1e293b"       # Dark Slate Card
        self.ACCENT_BLUE = "#3a86ff"   # Electric Star Blue
        self.ACCENT_RED = "#e63946"    # Banner Crimson Red
        self.ACCENT_GOLD = "#ffb703"   # Star Spangled Gold
        self.TEXT_WHITE = "#f8fafc"    # Bright White
        self.TEXT_MUTED = "#94a3b8"    # Muted Gray
        self.GREEN_SUCCESS = "#2a9d8f" # Emerald Success
        self.RED_FAIL = "#e63946"      # Crimson Fail
        self.AMBER_WARN = "#f4a261"     # Amber Warning
        self.INFO_BG = "#131c35"       # Dark Context Panel

        self.root.configure(bg=self.BG_COLOR)

        self.style.configure("TFrame", background=self.BG_COLOR)
        self.style.configure("Header.TFrame", background=self.NAVY_HEADER)
        self.style.configure("Header.TLabel", background=self.NAVY_HEADER, foreground=self.TEXT_WHITE, font=("Segoe UI", 16, "bold"))
        self.style.configure("SubHeader.TLabel", background=self.NAVY_HEADER, foreground=self.ACCENT_GOLD, font=("Segoe UI", 9, "bold"))

        self.style.configure("TNotebook", background=self.BG_COLOR, borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#1a233a", foreground=self.TEXT_MUTED, font=("Segoe UI", 10, "bold"), padding=[12, 6])
        self.style.map("TNotebook.Tab", background=[("selected", self.ACCENT_RED)], foreground=[("selected", self.TEXT_WHITE)])

        self.style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), background=self.ACCENT_RED, foreground="#ffffff", padding=6)
        self.style.map("Primary.TButton", background=[("active", "#c1121f")])

        self.style.configure("Success.TButton", font=("Segoe UI", 10, "bold"), background=self.GREEN_SUCCESS, foreground="#ffffff", padding=6)
        self.style.configure("Warn.TButton", font=("Segoe UI", 10, "bold"), background=self.ACCENT_GOLD, foreground="#000000", padding=6)

    def create_widgets(self):
        # 1. Top Header Banner
        header_frame = ttk.Frame(self.root, style="Header.TFrame", padding="15 12 15 12")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(header_frame, text=" USCIS Civics N-400 Study Assistant", style="Header.TLabel")
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = ttk.Label(header_frame, text="⭐ Star-Spangled Banner Dark Edition • Official 2025 Version (128 Questions)", style="SubHeader.TLabel")
        subtitle_lbl.pack(anchor=tk.W, pady=(2, 1))

        credit_lbl = tk.Label(
            header_frame,
            text="Designed and Developed by DarthTarry® (https://github.com/DarthTarry)",
            font=("Segoe UI", 8, "italic"),
            fg="#94a3b8", bg=self.NAVY_HEADER, cursor="hand2"
        )
        credit_lbl.pack(anchor=tk.W, pady=(2, 0))
        credit_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/DarthTarry"))

        # 2. Notebook Navigation Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab Frames
        self.tab_flashcards = ttk.Frame(self.notebook, padding=10)
        self.tab_quiz = ttk.Frame(self.notebook, padding=10)
        self.tab_flagged = ttk.Frame(self.notebook, padding=10)
        self.tab_feedback = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_flashcards, text=f"🎴 Flashcards ({len(self.questions)})")
        self.notebook.add(self.tab_quiz, text="📝 Practice Quiz")
        self.notebook.add(self.tab_flagged, text="⭐ Flagged & Missed")
        self.notebook.add(self.tab_feedback, text="✉️ Send Feedback")

        # Build each tab view
        self.build_flashcard_tab()
        self.build_quiz_tab()
        self.build_flagged_tab()
        self.build_feedback_tab()

        # Update tab titles with badges
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    # ---------------------------------------------------------------------------
    # TAB 1: FLASHCARDS MODE
    # ---------------------------------------------------------------------------
    def build_flashcard_tab(self):
        # Filter & Search Control Bar
        control_frame = ttk.Frame(self.tab_flashcards)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(control_frame, text="Category:").pack(side=tk.LEFT, padx=(0, 5))
        self.fc_cat_var = tk.StringVar(value="All Categories")
        cats = [
            "All Categories",
            "American Government",
            "American History",
            "Integrated Civics",
            "⭐ 65/20 Special Consideration (20 Questions)",
            "Flagged Only"
        ]
        self.fc_cat_cb = ttk.Combobox(control_frame, textvariable=self.fc_cat_var, values=cats, state="readonly", width=28)
        self.fc_cat_cb.pack(side=tk.LEFT, padx=(0, 12))
        self.fc_cat_cb.bind("<<ComboboxSelected>>", self.apply_flashcard_filter)

        ttk.Label(control_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.fc_search_var = tk.StringVar()
        self.fc_search_entry = ttk.Entry(control_frame, textvariable=self.fc_search_var, width=16)
        self.fc_search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.fc_search_entry.bind("<KeyRelease>", self.apply_flashcard_filter)

        btn_shuffle = ttk.Button(control_frame, text="🔀 Shuffle", command=self.shuffle_flashcards)
        btn_shuffle.pack(side=tk.RIGHT)

        # Main Flashcard Display Canvas Frame
        self.fc_card_frame = tk.Frame(self.tab_flashcards, bg=self.CARD_BG, highlightbackground="#334155", highlightthickness=2, bd=0)
        self.fc_card_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Card Header: Category & 65/20 Badge
        self.fc_header_frame = tk.Frame(self.fc_card_frame, bg=self.CARD_BG)
        self.fc_header_frame.pack(fill=tk.X, padx=18, pady=(12, 5))

        self.fc_header_label = tk.Label(self.fc_header_frame, text="Question 1 of 128 • American Government", bg=self.CARD_BG, fg=self.TEXT_MUTED, font=("Segoe UI", 9, "bold"))
        self.fc_header_label.pack(side=tk.LEFT)

        self.fc_badge_label = tk.Label(self.fc_header_frame, text="⭐ 65/20 Special", bg="#451a03", fg=self.ACCENT_GOLD, font=("Segoe UI", 8, "bold"), padx=6, pady=2)

        # Question Text Area
        self.fc_q_text = tk.Text(self.fc_card_frame, wrap=tk.WORD, bg=self.CARD_BG, fg=self.TEXT_WHITE, font=("Segoe UI", 12, "bold"), bd=0, highlightthickness=0, height=3)
        self.fc_q_text.pack(fill=tk.X, padx=18, pady=5)

        # Separator Line inside Card
        sep = tk.Frame(self.fc_card_frame, bg="#334155", height=1)
        sep.pack(fill=tk.X, padx=18, pady=5)

        # Answer & Context Frame Container
        self.fc_a_frame = tk.Frame(self.fc_card_frame, bg=self.CARD_BG)
        self.fc_a_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=5)

        self.fc_a_hint_label = tk.Label(self.fc_a_frame, text="💡 Click 'Flip Card / Reveal Answer' below to view acceptable answers & historical context.", bg=self.CARD_BG, fg=self.TEXT_MUTED, font=("Segoe UI", 10, "italic"))
        self.fc_a_hint_label.pack(expand=True)

        # Scrollable container for answer and explanation
        self.fc_answer_panel = tk.Frame(self.fc_a_frame, bg=self.CARD_BG)

        tk.Label(self.fc_answer_panel, text="Acceptable USCIS Answers:", font=("Segoe UI", 10, "bold"), fg=self.TEXT_WHITE, bg=self.CARD_BG).pack(anchor=tk.W, pady=(2, 2))
        
        self.fc_a_text = tk.Text(self.fc_answer_panel, wrap=tk.WORD, bg="#0f172a", fg="#4ade80", font=("Segoe UI", 11), bd=1, relief="solid", highlightthickness=0, height=4)
        self.fc_a_text.pack(fill=tk.X, pady=(0, 8))

        # Context & Explanation Panel
        tk.Label(self.fc_answer_panel, text="📚 Historical Context & Explanation:", font=("Segoe UI", 10, "bold"), fg=self.ACCENT_BLUE, bg=self.CARD_BG).pack(anchor=tk.W, pady=(2, 2))

        self.fc_exp_text = tk.Text(self.fc_answer_panel, wrap=tk.WORD, bg=self.INFO_BG, fg="#93c5fd", font=("Segoe UI", 10), bd=1, relief="solid", highlightthickness=0, height=5)
        self.fc_exp_text.pack(fill=tk.X, pady=(0, 5))

        # Bottom Card Controls
        btn_bar = ttk.Frame(self.tab_flashcards)
        btn_bar.pack(fill=tk.X, pady=(10, 0))

        self.btn_fc_prev = ttk.Button(btn_bar, text="◀ Previous", command=self.prev_flashcard)
        self.btn_fc_prev.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_fc_flip = ttk.Button(btn_bar, text="🔄 Flip Card / Reveal Answer", style="Primary.TButton", command=self.toggle_flashcard_flip)
        self.btn_fc_flip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.btn_fc_flag = ttk.Button(btn_bar, text="⭐ Flag Question", command=self.toggle_flag_current_flashcard)
        self.btn_fc_flag.pack(side=tk.LEFT, padx=5)

        self.btn_fc_next = ttk.Button(btn_bar, text="Next ▶", command=self.next_flashcard)
        self.btn_fc_next.pack(side=tk.RIGHT, padx=(5, 0))

        self.render_flashcard()

    def apply_flashcard_filter(self, event=None):
        cat = self.fc_cat_var.get()
        query = self.fc_search_var.get().strip().lower()

        filtered = []
        for q in self.questions:
            # Category match
            if cat == "Flagged Only" and q["id"] not in self.flagged_ids:
                continue
            elif cat.startswith("⭐ 65/20") and not q.get("special_65_20", False):
                continue
            elif cat not in ("All Categories", "Flagged Only") and not cat.startswith("⭐ 65/20") and q["category"] != cat:
                continue

            # Text query match
            if query:
                q_match = query in q["question"].lower()
                a_match = any(query in a.lower() for a in q["answers"])
                exp_match = query in q.get("explanation", "").lower()
                if not (q_match or a_match or exp_match):
                    continue

            filtered.append(q)

        self.filtered_flashcards = filtered if filtered else []
        self.flashcard_index = 0
        self.flashcard_showing_answer = False
        self.render_flashcard()

    def shuffle_flashcards(self):
        random.shuffle(self.filtered_flashcards)
        self.flashcard_index = 0
        self.flashcard_showing_answer = False
        self.render_flashcard()

    def render_flashcard(self):
        if not self.filtered_flashcards:
            self.fc_header_label.config(text="No matching questions found.")
            self.fc_badge_label.pack_forget()
            self.fc_q_text.config(state=tk.NORMAL)
            self.fc_q_text.delete("1.0", tk.END)
            self.fc_q_text.insert(tk.END, "Try clearing your search query or selecting 'All Categories'.")
            self.fc_q_text.config(state=tk.DISABLED)

            self.fc_answer_panel.pack_forget()
            self.fc_a_hint_label.pack(expand=True)
            self.fc_a_hint_label.config(text="No questions available.")
            self.btn_fc_flag.config(text="⭐ Flag Question")
            return

        curr = self.filtered_flashcards[self.flashcard_index]
        is_flagged = curr["id"] in self.flagged_ids
        is_65_20 = curr.get("special_65_20", False)

        # Header Info
        hdr = f"Question {self.flashcard_index + 1} of {len(self.filtered_flashcards)} (USCIS #{curr['id']}) • {curr['category']} > {curr.get('subcategory', '')}"
        self.fc_header_label.config(text=hdr)

        if is_65_20:
            self.fc_badge_label.pack(side=tk.RIGHT)
        else:
            self.fc_badge_label.pack_forget()

        # Question Text
        self.fc_q_text.config(state=tk.NORMAL)
        self.fc_q_text.delete("1.0", tk.END)
        self.fc_q_text.insert(tk.END, curr["question"])
        self.fc_q_text.config(state=tk.DISABLED)

        # Answer Text / Context
        if self.flashcard_showing_answer:
            self.fc_a_hint_label.pack_forget()
            self.fc_answer_panel.pack(fill=tk.BOTH, expand=True)

            self.fc_a_text.config(state=tk.NORMAL)
            self.fc_a_text.delete("1.0", tk.END)
            ans_text = "\n".join([f"• {a}" for a in curr["answers"]])
            self.fc_a_text.insert(tk.END, ans_text)
            self.fc_a_text.config(state=tk.DISABLED)

            self.fc_exp_text.config(state=tk.NORMAL)
            self.fc_exp_text.delete("1.0", tk.END)
            self.fc_exp_text.insert(tk.END, curr.get("explanation", "USCIS Naturalization Civics Study Material."))
            self.fc_exp_text.config(state=tk.DISABLED)
        else:
            self.fc_answer_panel.pack_forget()
            self.fc_a_hint_label.pack(expand=True)
            self.fc_a_hint_label.config(text="💡 Click 'Flip Card / Reveal Answer' below to view acceptable answers & historical context.")

        # Flag Button State
        self.btn_fc_flag.config(text="⭐ Flagged" if is_flagged else "☆ Flag Question")

    def toggle_flashcard_flip(self):
        self.flashcard_showing_answer = not self.flashcard_showing_answer
        self.render_flashcard()

    def prev_flashcard(self):
        if self.filtered_flashcards:
            self.flashcard_index = (self.flashcard_index - 1) % len(self.filtered_flashcards)
            self.flashcard_showing_answer = False
            self.render_flashcard()

    def next_flashcard(self):
        if self.filtered_flashcards:
            self.flashcard_index = (self.flashcard_index + 1) % len(self.filtered_flashcards)
            self.flashcard_showing_answer = False
            self.render_flashcard()

    def toggle_flag_current_flashcard(self):
        if not self.filtered_flashcards:
            return
        curr = self.filtered_flashcards[self.flashcard_index]
        qid = curr["id"]
        if qid in self.flagged_ids:
            self.flagged_ids.remove(qid)
        else:
            self.flagged_ids.add(qid)

        self.save_progress()
        self.render_flashcard()
        self.update_flagged_tab_badge()

    # ---------------------------------------------------------------------------
    # TAB 2: PRACTICE QUIZ MODE
    # ---------------------------------------------------------------------------
    def build_quiz_tab(self):
        # Top Quiz Setup Bar
        self.quiz_setup_frame = ttk.LabelFrame(self.tab_quiz, text=" Quiz Configuration ", padding=10)
        self.quiz_setup_frame.pack(fill=tk.X, pady=(0, 10))

        # Mode Selection
        ttk.Label(self.quiz_setup_frame, text="Quiz Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.quiz_type_var = tk.StringVar(value="mc")
        rb_mc = ttk.Radiobutton(self.quiz_setup_frame, text="Multiple Choice", variable=self.quiz_type_var, value="mc")
        rb_mc.grid(row=0, column=1, sticky=tk.W, padx=5)
        rb_text = ttk.Radiobutton(self.quiz_setup_frame, text="Type-In Answer", variable=self.quiz_type_var, value="text")
        rb_text.grid(row=0, column=2, sticky=tk.W, padx=5)

        # Question Count Selection
        ttk.Label(self.quiz_setup_frame, text="Question Pool:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.quiz_pool_var = tk.StringVar(value="20 Questions (2025 Official Format - 12 to pass)")
        pool_options = [
            "20 Questions (2025 Official Format - 12 to pass)",
            "10 Questions (65/20 Special Format - 6 to pass)",
            "50 Questions",
            "All 128 Questions",
            "Flagged Questions Only"
        ]
        self.quiz_pool_cb = ttk.Combobox(self.quiz_setup_frame, textvariable=self.quiz_pool_var, values=pool_options, state="readonly", width=42)
        self.quiz_pool_cb.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5)

        btn_start_quiz = ttk.Button(self.quiz_setup_frame, text="🚀 Start Practice Quiz", style="Primary.TButton", command=self.start_quiz)
        btn_start_quiz.grid(row=0, column=3, rowspan=2, padx=15, pady=5, sticky="NSEW")

        # Active Quiz Display Frame
        self.quiz_active_frame = ttk.Frame(self.tab_quiz)
        self.quiz_active_frame.pack(fill=tk.BOTH, expand=True)

        # Quiz Header Bar (Score, Progress, Passing Standard)
        q_hdr_frame = ttk.Frame(self.quiz_active_frame)
        q_hdr_frame.pack(fill=tk.X, pady=(0, 10))

        self.quiz_progress_lbl = ttk.Label(q_hdr_frame, text="Question 0 of 20", font=("Segoe UI", 11, "bold"))
        self.quiz_progress_lbl.pack(side=tk.LEFT)

        self.quiz_score_lbl = ttk.Label(q_hdr_frame, text="Score: 0/0 (0%)", font=("Segoe UI", 11, "bold"), foreground=self.ACCENT_BLUE)
        self.quiz_score_lbl.pack(side=tk.RIGHT)

        # Quiz Question Box
        self.quiz_q_box = tk.Frame(self.quiz_active_frame, bg=self.CARD_BG, highlightbackground="#334155", highlightthickness=1, bd=0)
        self.quiz_q_box.pack(fill=tk.X, pady=5)

        self.quiz_q_lbl = tk.Label(self.quiz_q_box, text="Click 'Start Practice Quiz' above to begin!", font=("Segoe UI", 12, "bold"), bg=self.CARD_BG, fg=self.TEXT_WHITE, wraplength=720, justify=tk.LEFT)
        self.quiz_q_lbl.pack(anchor=tk.W, padx=15, pady=12)

        # Answer Input Section Container
        self.quiz_ans_container = ttk.Frame(self.quiz_active_frame)
        self.quiz_ans_container.pack(fill=tk.BOTH, expand=True, pady=5)

        # Feedback & Explanation Banner
        self.quiz_feedback_frame = tk.Frame(self.quiz_active_frame, bg=self.INFO_BG, bd=1, relief="solid")
        self.quiz_feedback_lbl = tk.Label(self.quiz_feedback_frame, text="", font=("Segoe UI", 10, "bold"), bg=self.INFO_BG, justify=tk.LEFT, wraplength=720)
        self.quiz_feedback_lbl.pack(anchor=tk.W, padx=10, pady=5)

        self.quiz_exp_lbl = tk.Label(self.quiz_feedback_frame, text="", font=("Segoe UI", 9), bg=self.INFO_BG, fg="#93c5fd", justify=tk.LEFT, wraplength=720)
        self.quiz_exp_lbl.pack(anchor=tk.W, padx=10, pady=(0, 5))

        # Next Question Button
        self.btn_quiz_next = ttk.Button(self.quiz_active_frame, text="Next Question ▶", style="Primary.TButton", command=self.quiz_next_question)
        self.btn_quiz_next.pack(side=tk.RIGHT, pady=5)
        self.btn_quiz_next.pack_forget()

    def start_quiz(self, custom_list=None):
        # Setup question pool
        pool_sel = self.quiz_pool_var.get()
        if custom_list is not None:
            pool = list(custom_list)
        elif "Flagged" in pool_sel:
            pool = [q for q in self.questions if q["id"] in self.flagged_ids]
            if not pool:
                messagebox.showinfo("No Flagged Questions", "You currently have no flagged questions! Flag questions in Flashcards mode or take a quiz first.")
                return
        elif "65/20 Special" in pool_sel:
            pool = [q for q in self.questions if q.get("special_65_20", False)]
        else:
            pool = list(self.questions)

        random.shuffle(pool)

        # Determine count & pass mark
        if custom_list is not None:
            count = len(pool)
            self.quiz_pass_mark = int(count * 0.6)
        else:
            if "10 Questions" in pool_sel:
                count = min(10, len(pool))
                self.quiz_pass_mark = 6
            elif "20 Questions" in pool_sel:
                count = min(20, len(pool))
                self.quiz_pass_mark = 12
            elif "50 Questions" in pool_sel:
                count = min(50, len(pool))
                self.quiz_pass_mark = 30
            else:
                count = len(pool)
                self.quiz_pass_mark = int(count * 0.6)

        self.quiz_queue = pool[:count]
        self.quiz_index = 0
        self.quiz_score = 0
        self.quiz_mode_type = self.quiz_type_var.get()
        self.quiz_total = len(self.quiz_queue)
        self.quiz_history = []

        self.render_quiz_question()

    def render_quiz_question(self):
        self.btn_quiz_next.pack_forget()
        self.quiz_feedback_frame.pack_forget()

        # Clear answer container
        for w in self.quiz_ans_container.winfo_children():
            w.destroy()

        if self.quiz_index >= len(self.quiz_queue):
            self.show_quiz_results()
            return

        curr = self.quiz_queue[self.quiz_index]

        # Update Header
        badge_str = " ⭐ 65/20 Special" if curr.get("special_65_20", False) else ""
        self.quiz_progress_lbl.config(text=f"Question {self.quiz_index + 1} of {self.quiz_total} • (USCIS #{curr['id']}){badge_str}")
        pct = int((self.quiz_score / max(1, self.quiz_index)) * 100) if self.quiz_index > 0 else 0
        self.quiz_score_lbl.config(text=f"Score: {self.quiz_score}/{self.quiz_index} ({pct}%)")

        self.quiz_q_lbl.config(text=curr["question"])

        if self.quiz_mode_type == "mc":
            choices = list(curr.get("choices", []))
            if len(choices) < 4:
                all_distractors = [c for q in self.questions if q["id"] != curr["id"] for c in q.get("choices", [])]
                sampled = random.sample(all_distractors, min(4 - len(choices), len(all_distractors)))
                choices.extend(sampled)

            random.shuffle(choices)

            self.mc_var = tk.StringVar(value="___UNSELECTED___")
            self.mc_widgets = []
            for idx, choice_text in enumerate(choices):
                f = tk.Frame(self.quiz_ans_container, bg=self.CARD_BG, highlightbackground="#334155", highlightthickness=1, bd=0)
                f.pack(fill=tk.X, pady=3)

                rb = tk.Radiobutton(
                    f, text=choice_text, variable=self.mc_var, value=choice_text,
                    font=("Segoe UI", 10), bg=self.CARD_BG, fg=self.TEXT_WHITE, activebackground=self.CARD_BG, activeforeground=self.TEXT_WHITE,
                    anchor=tk.W, justify=tk.LEFT, wraplength=680, tristatevalue="___UNSELECTED___", selectcolor=self.CARD_BG
                )
                rb.pack(anchor=tk.W, padx=10, pady=8, fill=tk.X)
                self.mc_widgets.append((f, rb, choice_text))

            btn_sub = ttk.Button(self.quiz_ans_container, text="Submit Answer", style="Primary.TButton", command=self.submit_mc_answer)
            btn_sub.pack(anchor=tk.W, pady=8)

        else:  # Type-In Answer Mode
            lbl_type = ttk.Label(self.quiz_ans_container, text="Type your answer below:", font=("Segoe UI", 10))
            lbl_type.pack(anchor=tk.W, pady=(5, 5))

            self.quiz_entry_var = tk.StringVar()
            entry = ttk.Entry(self.quiz_ans_container, textvariable=self.quiz_entry_var, font=("Segoe UI", 11), width=50)
            entry.pack(anchor=tk.W, pady=5)
            entry.focus()
            entry.bind("<Return>", lambda e: self.submit_text_answer())

            btn_sub = ttk.Button(self.quiz_ans_container, text="Check Answer", style="Primary.TButton", command=self.submit_text_answer)
            btn_sub.pack(anchor=tk.W, pady=8)

    def submit_mc_answer(self):
        curr = self.quiz_queue[self.quiz_index]
        selected = self.mc_var.get()

        if not selected or selected == "___UNSELECTED___":
            messagebox.showwarning("Select an Option", "Please select an answer choice before submitting.")
            return

        is_correct = any(
            selected.strip().lower() in ans.strip().lower() or ans.strip().lower() in selected.strip().lower()
            for ans in curr["answers"]
        )

        for f, rb, choice_text in getattr(self, 'mc_widgets', []):
            rb.config(state=tk.DISABLED)
            btn_is_correct = any(
                choice_text.strip().lower() in ans.strip().lower() or ans.strip().lower() in choice_text.strip().lower()
                for ans in curr["answers"]
            )
            if choice_text == selected:
                if is_correct:
                    f.config(bg="#14532d", highlightbackground="#22c55e", highlightthickness=2)
                    rb.config(bg="#14532d", fg="#bbf7d0")
                else:
                    f.config(bg="#7f1d1d", highlightbackground="#ef4444", highlightthickness=2)
                    rb.config(bg="#7f1d1d", fg="#fecaca")
            elif btn_is_correct:
                f.config(bg="#14532d", highlightbackground="#22c55e", highlightthickness=2)
                rb.config(bg="#14532d", fg="#bbf7d0")
            else:
                rb.config(fg="#64748b")

        self.process_answer_result(curr, is_correct, selected, " / ".join(curr["answers"][:3]))

    def submit_text_answer(self):
        curr = self.quiz_queue[self.quiz_index]
        user_input = self.quiz_entry_var.get().strip().lower()

        if not user_input:
            messagebox.showwarning("Empty Answer", "Please type an answer before checking.")
            return

        is_correct = False
        for ans in curr["answers"]:
            clean_ans = re.sub(r'\(.*?\)', '', ans).strip().lower()
            if clean_ans in user_input or user_input in clean_ans:
                is_correct = True
                break
            words_ans = set(clean_ans.split())
            words_user = set(user_input.split())
            if words_ans and len(words_ans.intersection(words_user)) / len(words_ans) >= 0.5:
                is_correct = True
                break

        self.process_answer_result(curr, is_correct, user_input, " / ".join(curr["answers"]))

    def process_answer_result(self, question, is_correct, user_given, correct_str):
        self.quiz_feedback_frame.pack(fill=tk.X, pady=5)

        if is_correct:
            self.quiz_score += 1
            self.quiz_feedback_lbl.config(text="✅ Correct!", fg=self.GREEN_SUCCESS)
        else:
            self.quiz_feedback_lbl.config(text=f"❌ Incorrect.\nAcceptable Answer(s): {correct_str}", fg=self.RED_FAIL)
            self.flagged_ids.add(question["id"])
            self.missed_history[str(question["id"])] = self.missed_history.get(str(question["id"]), 0) + 1
            self.save_progress()
            self.update_flagged_tab_badge()

        exp = question.get("explanation", "USCIS Naturalization Civics Study Material.")
        self.quiz_exp_lbl.config(text=f"📚 Context & Explanation:\n{exp}")

        self.quiz_history.append({"question": question, "correct": is_correct, "given": user_given})

        # Disable input controls
        for w in self.quiz_ans_container.winfo_children():
            if isinstance(w, (ttk.Button, tk.Radiobutton, ttk.Entry)):
                w.config(state=tk.DISABLED)

        self.btn_quiz_next.pack(side=tk.RIGHT, pady=5)

    def quiz_next_question(self):
        self.quiz_index += 1
        self.render_quiz_question()

    def show_quiz_results(self):
        for w in self.quiz_ans_container.winfo_children():
            w.destroy()

        passed = self.quiz_score >= self.quiz_pass_mark
        pct = int((self.quiz_score / max(1, self.quiz_total)) * 100)

        # Update stats
        self.stats["quizzes_taken"] += 1
        if passed:
            self.stats["quizzes_passed"] += 1
        self.stats["total_correct"] += self.quiz_score
        self.stats["total_answered"] += self.quiz_total
        self.save_progress()

        res_frame = tk.Frame(self.quiz_ans_container, bg=self.CARD_BG, highlightbackground="#334155", highlightthickness=1, bd=0)
        res_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        status_str = "🎉 PASSED!" if passed else "⚠️ NEEDS MORE PRACTICE"
        status_color = self.GREEN_SUCCESS if passed else self.AMBER_WARN

        tk.Label(res_frame, text=status_str, font=("Segoe UI", 18, "bold"), fg=status_color, bg=self.CARD_BG).pack(pady=(20, 5))
        tk.Label(res_frame, text=f"Your Final Score: {self.quiz_score} / {self.quiz_total} ({pct}%)", font=("Segoe UI", 14, "bold"), fg=self.TEXT_WHITE, bg=self.CARD_BG).pack(pady=5)

        note = f"Passing Standard: {self.quiz_pass_mark} out of {self.quiz_total} correct answers required."
        tk.Label(res_frame, text=note, font=("Segoe UI", 10, "italic"), fg=self.TEXT_MUTED, bg=self.CARD_BG).pack(pady=5)

        missed_count = self.quiz_total - self.quiz_score
        if missed_count > 0:
            tk.Label(res_frame, text=f"📌 {missed_count} question(s) were added/kept in your Flagged Questions list.", font=("Segoe UI", 10), fg=self.RED_FAIL, bg=self.CARD_BG).pack(pady=10)

            btn_retry_missed = ttk.Button(res_frame, text="🔄 Retry Missed Questions Now", style="Warn.TButton", command=self.retry_quiz_missed)
            btn_retry_missed.pack(pady=5)

        btn_restart = ttk.Button(res_frame, text="🚀 Take Another Quiz", style="Primary.TButton", command=self.start_quiz)
        btn_restart.pack(pady=10)

    def retry_quiz_missed(self):
        missed = [item["question"] for item in self.quiz_history if not item["correct"]]
        if missed:
            self.start_quiz(custom_list=missed)

    # ---------------------------------------------------------------------------
    # TAB 3: FLAGGED & MISSED QUESTIONS MANAGER
    # ---------------------------------------------------------------------------
    def build_flagged_tab(self):
        hdr_frame = ttk.Frame(self.tab_flagged)
        hdr_frame.pack(fill=tk.X, pady=(0, 10))

        self.flagged_summary_lbl = ttk.Label(hdr_frame, text="0 Flagged Questions for Review", font=("Segoe UI", 12, "bold"))
        self.flagged_summary_lbl.pack(side=tk.LEFT)

        btn_quiz_flagged = ttk.Button(hdr_frame, text="🎯 Quiz on Flagged Only", style="Primary.TButton", command=self.quiz_flagged_only)
        btn_quiz_flagged.pack(side=tk.RIGHT)

        btn_clear_all = ttk.Button(hdr_frame, text="Clear All Flags", command=self.clear_all_flags)
        btn_clear_all.pack(side=tk.RIGHT, padx=5)

        # Treeview
        tree_frame = ttk.Frame(self.tab_flagged)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("id", "category", "question", "special_65_20", "miss_count")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID #")
        self.tree.heading("category", text="Category")
        self.tree.heading("question", text="Civics Question")
        self.tree.heading("special_65_20", text="65/20?")
        self.tree.heading("miss_count", text="Times Missed")

        self.tree.column("id", width=45, anchor=tk.CENTER)
        self.tree.column("category", width=150)
        self.tree.column("question", width=380)
        self.tree.column("special_65_20", width=65, anchor=tk.CENTER)
        self.tree.column("miss_count", width=85, anchor=tk.CENTER)

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # Detail Box Below List
        detail_frame = tk.LabelFrame(self.tab_flagged, text=" Selected Question Details & Explanation ", font=("Segoe UI", 9, "bold"), fg=self.ACCENT_GOLD, bg=self.CARD_BG, padx=10, pady=10)
        detail_frame.pack(fill=tk.X, pady=10)

        self.flagged_detail_lbl = tk.Label(detail_frame, text="Select a question above to preview its correct answer and historical context.", font=("Segoe UI", 10), fg=self.TEXT_WHITE, bg=self.CARD_BG, anchor=tk.W, justify=tk.LEFT, wraplength=720)
        self.flagged_detail_lbl.pack(fill=tk.X)

        btn_unflag = ttk.Button(detail_frame, text="✓ Remove Flag (Mastered)", command=self.unflag_selected_tree_item)
        btn_unflag.pack(anchor=tk.E, pady=(5, 0))

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def render_flagged_tab(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        flagged_list = [q for q in self.questions if q["id"] in self.flagged_ids]
        self.flagged_summary_lbl.config(text=f"{len(flagged_list)} Flagged / Missed Question(s) for Review")

        for q in flagged_list:
            misses = self.missed_history.get(str(q["id"]), 0)
            is_65 = "⭐ Yes" if q.get("special_65_20", False) else "No"
            self.tree.insert("", tk.END, values=(q["id"], q["category"], q["question"], is_65, misses))

        self.update_flagged_tab_badge()

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        qid = int(vals[0])

        q = next((item for item in self.questions if item["id"] == qid), None)
        if q:
            ans_str = "\n• ".join(q["answers"])
            exp_str = q.get("explanation", "USCIS Naturalization Civics Study Material.")
            txt = f"Question #{q['id']}: {q['question']}\n\nOfficial Answer(s):\n• {ans_str}\n\n📚 Historical Context & Explanation:\n{exp_str}"
            self.flagged_detail_lbl.config(text=txt)

    def unflag_selected_tree_item(self):
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        qid = int(vals[0])

        if qid in self.flagged_ids:
            self.flagged_ids.remove(qid)
            self.save_progress()
            self.render_flagged_tab()
            self.flagged_detail_lbl.config(text="Select a question above to preview its correct answer and historical context.")

    def clear_all_flags(self):
        if not self.flagged_ids:
            return
        if messagebox.askyesno("Clear All Flags", "Are you sure you want to unflag all questions?"):
            self.flagged_ids.clear()
            self.save_progress()
            self.render_flagged_tab()

    def quiz_flagged_only(self):
        if not self.flagged_ids:
            messagebox.showinfo("No Flagged Questions", "You have no flagged questions to review.")
            return
        self.notebook.select(self.tab_quiz)
        self.quiz_pool_var.set("Flagged Questions Only")
        self.start_quiz()

    def update_flagged_tab_badge(self):
        count = len(self.flagged_ids)
        self.notebook.tab(self.tab_flagged, text=f"⭐ Flagged & Missed ({count})")

    def on_tab_changed(self, event):
        selected_tab = self.notebook.select()
        if selected_tab == str(self.tab_flagged):
            self.render_flagged_tab()

    # ---------------------------------------------------------------------------
    # TAB 4: USER FEEDBACK SECTION
    # ---------------------------------------------------------------------------
    def build_feedback_tab(self):
        fb_frame = tk.LabelFrame(
            self.tab_feedback, text=" ✉️ User Feedback & Suggestions ",
            font=("Segoe UI", 11, "bold"), fg=self.ACCENT_GOLD, bg=self.CARD_BG, padx=15, pady=15
        )
        fb_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        tk.Label(
            fb_frame,
            text="Have questions, corrections, or study feature suggestions? Send your feedback directly to the developer!",
            font=("Segoe UI", 10), fg=self.TEXT_WHITE, bg=self.CARD_BG, wraplength=700, justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 12))

        # Subject Selection
        subj_frame = tk.Frame(fb_frame, bg=self.CARD_BG)
        subj_frame.pack(fill=tk.X, pady=5)

        tk.Label(subj_frame, text="Feedback Topic:", font=("Segoe UI", 9, "bold"), fg=self.TEXT_WHITE, bg=self.CARD_BG).pack(side=tk.LEFT, padx=(0, 10))
        self.fb_topic_var = tk.StringVar(value="USCIS N-400 Civics App - General Feedback")
        topics = [
            "USCIS N-400 Civics App - General Feedback",
            "USCIS N-400 Civics App - Question or Answer Correction",
            "USCIS N-400 Civics App - Feature Suggestion",
            "USCIS N-400 Civics App - Practice Quiz Feedback"
        ]
        topic_cb = ttk.Combobox(subj_frame, textvariable=self.fb_topic_var, values=topics, state="readonly", width=48)
        topic_cb.pack(side=tk.LEFT)

        # Message Body
        tk.Label(fb_frame, text="Your Message / Comments:", font=("Segoe UI", 9, "bold"), fg=self.TEXT_WHITE, bg=self.CARD_BG).pack(anchor=tk.W, pady=(12, 4))

        self.fb_text = tk.Text(
            fb_frame, wrap=tk.WORD, font=("Segoe UI", 10),
            bg="#0f172a", fg="#f8fafc", insertbackground="#f8fafc",
            bd=1, relief=tk.SOLID, height=12
        )
        self.fb_text.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        # Recipient Info
        tk.Label(
            fb_frame,
            text="Recipient: arun.vijayaraghavan1982@gmail.com",
            font=("Segoe UI", 8, "italic"), fg=self.TEXT_MUTED, bg=self.CARD_BG
        ).pack(anchor=tk.W, pady=(0, 10))

        # Send Button
        btn_send = ttk.Button(
            fb_frame,
            text="✉️ Send Feedback via Email Client",
            style="Warn.TButton",
            command=self.send_feedback_email
        )
        btn_send.pack(anchor=tk.E)

    def send_feedback_email(self):
        subject = self.fb_topic_var.get().strip()
        body = self.fb_text.get("1.0", tk.END).strip()

        if not body:
            messagebox.showwarning("Empty Message", "Please enter your message before sending feedback.")
            return

        recipient = "arun.vijayaraghavan1982@gmail.com"
        mailto_url = f"mailto:{recipient}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

        try:
            webbrowser.open(mailto_url)
            messagebox.showinfo("Email Client Opened", f"Opening your default email client to send feedback to {recipient}.")
        except Exception as e:
            messagebox.showerror("Error Opening Email", f"Could not launch email client automatically.\n\nPlease email your feedback directly to: {recipient}\nSubject: {subject}")


def main():
    root = tk.Tk()
    app = USCISStudyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
