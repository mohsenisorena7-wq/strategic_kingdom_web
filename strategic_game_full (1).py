import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import arabic_reshaper
from bidi.algorithm import get_display


# =========================
# Helper: reshape Persian text for UI/Charts
# =========================
def reshape_farsi(text):
    return get_display(arabic_reshaper.reshape(text))


# =========================
# Dummy game classes (for testing UI)
# =========================
class DummyCountry:
    def __init__(self):
        self.name = "کشور نمونه"
        self.resources = {"طلا": 100, "غذا": 80, "چوب": 60, "آهن": 40}
        self.population = 50
        self.soldiers = 10
        self.score = 0
        self.history = [
            {"سال": 1, "منابع": {"طلا": 100, "غذا": 80, "چوب": 60, "آهن": 40}, "جمعیت": 50, "سربازان": 10, "امتیاز": 0},
            {"سال": 2, "منابع": {"طلا": 120, "غذا": 85, "چوب": 70, "آهن": 55}, "جمعیت": 60, "سربازان": 15, "امتیاز": 10},
            {"سال": 3, "منابع": {"طلا": 150, "غذا": 90, "چوب": 75, "آهن": 65}, "جمعیت": 70, "سربازان": 20, "امتیاز": 20},
        ]


class DummyGame:
    def __init__(self):
        self.year = 1
        self.player = DummyCountry()

    def next_turn(self):
        self.year += 1
        self.player.score += 10
        self.player.population += 5
        self.player.resources["طلا"] += 20
        self.player.resources["غذا"] += 10
        self.player.soldiers += 2
        self.player.history.append({
            "سال": self.year,
            "منابع": self.player.resources.copy(),
            "جمعیت": self.player.population,
            "سربازان": self.player.soldiers,
            "امتیاز": self.player.score
        })


# =========================
# Interactive Chart Component
# =========================
class InteractiveChart:
    def __init__(self, master, history_data):
        self.master = master
        self.history = history_data
        self.metric_var = tk.StringVar(master, "طلا")
        self.fig = None
        self.canvas_widget = None
        self.create_widgets()
        self.update_chart()

    def create_widgets(self):
        chart_frame = tk.Frame(self.master)
        chart_frame.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Label(chart_frame, text=reshape_farsi("انتخاب متغیر نمودار:"), font=("Tahoma", 10)).pack(anchor="ne", padx=5, pady=2)
        options = ["طلا", "غذا", "چوب", "آهن", "جمعیت", "سربازان", "امتیاز"]
        ttk.OptionMenu(chart_frame, self.metric_var, self.metric_var.get(), *options, command=self.on_option_select).pack(anchor="ne", padx=5, pady=2)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True, padx=5, pady=5)

        self.annotation = self.ax.annotate("", xy=(0,0), xytext=(15,15),
                                           textcoords="offset points", bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.5),
                                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"))
        self.annotation.set_visible(False)
        self.canvas.mpl_connect("motion_notify_event", self.on_hover)

    def on_option_select(self, *args):
        self.update_chart()

    def update_history_data(self, new_history):
        self.history = new_history
        self.update_chart()

    def update_chart(self):
        self.ax.clear()
        if not self.history:
            self.ax.text(0.5, 0.5, reshape_farsi("تاریخچه‌ای برای نمایش وجود ندارد."),
                         horizontalalignment='center', verticalalignment='center',
                         transform=self.ax.transAxes, fontsize=12, color='gray')
            self.canvas.draw()
            return

        metric = self.metric_var.get()
        years = [h["سال"] for h in self.history]
        mapper = {
            "طلا": lambda h: h["منابع"]["طلا"],
            "غذا": lambda h: h["منابع"]["غذا"],
            "چوب": lambda h: h["منابع"]["چوب"],
            "آهن": lambda h: h["منابع"]["آهن"],
            "جمعیت": lambda h: h["جمعیت"],
            "سربازان": lambda h: h["سربازان"],
            "امتیاز": lambda h: h["امتیاز"]
        }

        self.yvals = [mapper[metric](h) for h in self.history]
        self.xvals = years
        self.line, = self.ax.plot(years, self.yvals, marker="o", color="blue", linewidth=2)

        self.ax.set_title(reshape_farsi(f"{metric} در طول زمان"), fontsize=14)
        self.ax.set_xlabel(reshape_farsi("سال"))
        self.ax.set_ylabel(reshape_farsi(metric))
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.tick_params(axis='x', rotation=45)
        self.fig.tight_layout()
        self.canvas.draw()
        self.annotation.set_visible(False)

    def on_hover(self, event):
        if not hasattr(self, "line"):
            return
        vis = self.annotation.get_visible()
        if event.inaxes == self.ax and self.line:
            contains, ind = self.line.contains(event)
            if contains:
                i = ind["ind"][0]
                x, y = self.xvals[i], self.yvals[i]
                self.annotation.xy = (x, y)
                self.annotation.set_text(reshape_farsi(f"سال: {x}\nمقدار: {y}"))
                self.annotation.set_visible(True)
                self.fig.canvas.draw_idle()
            else:
                if vis:
                    self.annotation.set_visible(False)
                    self.fig.canvas.draw_idle()


# =========================
# Main Game UI
# =========================
class GameUI:
    def __init__(self, root):
        self.root = root
        self.root.title("بازی استراتژیک - نسخه آزمایشی")
        self.game = DummyGame()

        self.create_main_ui()

    def create_main_ui(self):
        # --- اطلاعات اصلی
        info_frame = ttk.LabelFrame(self.root, text=reshape_farsi("اطلاعات کشور"))
        info_frame.pack(fill="x", padx=10, pady=5)

        self.lbl_year = tk.Label(info_frame, text=reshape_farsi(f"سال: {self.game.year}"), font=("Tahoma", 12))
        self.lbl_year.pack(anchor="w", padx=5, pady=2)

        self.lbl_resources = tk.Label(info_frame, text="", font=("Tahoma", 10))
        self.lbl_resources.pack(anchor="w", padx=5, pady=2)

        self.lbl_population = tk.Label(info_frame, text="", font=("Tahoma", 10))
        self.lbl_population.pack(anchor="w", padx=5, pady=2)

        self.lbl_soldiers = tk.Label(info_frame, text="", font=("Tahoma", 10))
        self.lbl_soldiers.pack(anchor="w", padx=5, pady=2)

        self.lbl_score = tk.Label(info_frame, text="", font=("Tahoma", 10))
        self.lbl_score.pack(anchor="w", padx=5, pady=2)

        # --- دکمه‌ها
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)

        tk.Button(btn_frame, text=reshape_farsi("دور بعدی"), command=self.next_turn).pack(side="right", padx=5)
        tk.Button(btn_frame, text=reshape_farsi("خروج"), command=self.root.quit).pack(side="right", padx=5)

        # --- نمودار
        self.chart = InteractiveChart(self.root, self.game.player.history)

        self.update_labels()

    def update_labels(self):
        p = self.game.player
        self.lbl_year.config(text=reshape_farsi(f"سال: {self.game.year}"))
        self.lbl_resources.config(text=reshape_farsi(f"منابع: طلا {p.resources['طلا']}, غذا {p.resources['غذا']}, چوب {p.resources['چوب']}, آهن {p.resources['آهن']}"))
        self.lbl_population.config(text=reshape_farsi(f"جمعیت: {p.population}"))
        self.lbl_soldiers.config(text=reshape_farsi(f"سربازان: {p.soldiers}"))
        self.lbl_score.config(text=reshape_farsi(f"امتیاز: {p.score}"))

    def next_turn(self):
        self.game.next_turn()
        self.update_labels()
        self.chart.update_history_data(self.game.player.history)


# =========================
# Run
# =========================
if __name__ == "__main__":
    root = tk.Tk()
    app = GameUI(root)
    root.mainloop()
