import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import calendar, random, csv
from datetime import date

APP_TITLE = "随机日历标注器（精简版）"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("960x600")
        self.configure(padx=10, pady=10)

        # 状态
        today = date.today()
        self.year  = tk.IntVar(value=today.year)
        self.month = tk.IntVar(value=today.month)
        self.k_pick = tk.IntVar(value=5)  # 随机选择K天
        self.groups = { "女": ["是","否"] }  # 组名 -> 选项列表
        self.selected_days = set()        # 已选日期集合
        self.assignments = {}             # day -> { group: name }

        # UI
        self._build_left()
        self._build_right()
        self._draw_calendar()
        self._refresh_group_list()

    # ---------- 左侧 ----------
    def _build_left(self):
        left = ttk.Frame(self); left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))

        lf_cal = ttk.LabelFrame(left, text="年月与选日")
        lf_cal.pack(fill=tk.X, pady=6)

        r1 = ttk.Frame(lf_cal); r1.pack(fill=tk.X, pady=4)
        ttk.Label(r1, text="年").pack(side=tk.LEFT)
        ttk.Entry(r1, textvariable=self.year, width=6).pack(side=tk.LEFT, padx=4)
        ttk.Label(r1, text="月").pack(side=tk.LEFT)
        ttk.Combobox(r1, textvariable=self.month, values=list(range(1,13)),
                     width=4, state="readonly").pack(side=tk.LEFT, padx=4)
        ttk.Button(r1, text="切换", command=self._switch_month).pack(side=tk.LEFT, padx=6)

        r2 = ttk.Frame(lf_cal); r2.pack(fill=tk.X, pady=4)
        ttk.Label(r2, text="随机选择 K 天：").pack(side=tk.LEFT)
        ttk.Entry(r2, textvariable=self.k_pick, width=5).pack(side=tk.LEFT, padx=4)
        ttk.Button(r2, text="随机选择", command=self._random_pick_days).pack(side=tk.LEFT, padx=6)
        ttk.Button(lf_cal, text="清空已选", command=self._clear_selected).pack(fill=tk.X, pady=4)

        lf_grp = ttk.LabelFrame(left, text="编辑组与内容")
        lf_grp.pack(fill=tk.BOTH, expand=True, pady=6)

        r3 = ttk.Frame(lf_grp); r3.pack(fill=tk.X, pady=(6,2))
        ttk.Label(r3, text="组名：").pack(side=tk.LEFT)
        self.new_g = tk.StringVar()
        ttk.Entry(r3, textvariable=self.new_g, width=16).pack(side=tk.LEFT, padx=6)

        r4 = ttk.Frame(lf_grp); r4.pack(fill=tk.X, pady=2)
        ttk.Label(r4, text="内容（逗号分隔）：").pack(side=tk.LEFT)
        self.new_items = tk.StringVar()
        ttk.Entry(r4, textvariable=self.new_items, width=24).pack(side=tk.LEFT, padx=6)

        r5 = ttk.Frame(lf_grp); r5.pack(fill=tk.X, pady=4)
        ttk.Button(r5, text="添加/更新组", command=self._add_or_update_group).pack(side=tk.LEFT)
        ttk.Button(r5, text="删除选中组", command=self._delete_group).pack(side=tk.LEFT, padx=8)

        self.group_list = tk.Listbox(lf_grp, height=8)
        self.group_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        ttk.Button(lf_grp, text="把选中组随机分派到选中日期",
                   command=self._assign_group_to_days).pack(fill=tk.X, padx=6, pady=6)

        # 导出/复制（可选）
        ex = ttk.Frame(left); ex.pack(fill=tk.X, pady=6)
        ttk.Button(ex, text="导出 CSV", command=self._export_csv).pack(side=tk.LEFT)
        ttk.Button(ex, text="复制结果", command=self._copy_result).pack(side=tk.LEFT, padx=8)

    # ---------- 右侧 ----------
    def _build_right(self):
        right = ttk.Frame(self); right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cf = ttk.LabelFrame(right, text="日历（点击格子选/取消）")
        cf.pack(fill=tk.BOTH, expand=True)
        self.calendar_frame = ttk.Frame(cf); self.calendar_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        lf = ttk.LabelFrame(right, text="结果（日期 → 组 / 内容）")
        lf.pack(fill=tk.BOTH, expand=False, pady=(8,0))
        self.result_list = tk.Listbox(lf, height=10)
        self.result_list.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    # ---------- 日历 ----------
    def _draw_calendar(self):
        for w in self.calendar_frame.winfo_children(): w.destroy()

        self.day_labels = {}
        y, m = self.year.get(), self.month.get()
        cal = calendar.monthcalendar(y, m)
        week_days = ["一","二","三","四","五","六","日"]

        for c, wd in enumerate(week_days):
            ttk.Label(self.calendar_frame, text=f"周{wd}", anchor="center")\
                .grid(row=0, column=c, sticky="nsew", padx=2, pady=2)

        for r in range(len(cal)+1):
            self.calendar_frame.rowconfigure(r, weight=1)
        for c in range(7):
            self.calendar_frame.columnconfigure(c, weight=1)

        for r, week in enumerate(cal, start=1):
            for c, d in enumerate(week):
                if d == 0:
                    ttk.Label(self.calendar_frame, text="").grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                    continue
                lbl = tk.Label(self.calendar_frame, text=str(d), bd=1, relief="solid",
                               justify="center", padx=6, pady=6)
                lbl.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                lbl.bind("<Button-1>", lambda e, day=d: self._toggle_day(day))
                self.day_labels[d] = lbl

        self._refresh_calendar_text()

    def _refresh_calendar_text(self):
        for d, lbl in self.day_labels.items():
            lbl.configure(bg="#FFF1A8" if d in self.selected_days else self.cget("bg"))
            lines = [str(d)]
            if d in self.assignments and self.assignments[d]:
                for g in sorted(self.assignments[d].keys()):
                    lines.append(f"{g}:{self.assignments[d][g]}")
            lbl.configure(text="\n".join(lines))

    # ---------- 交互 ----------
    def _toggle_day(self, day):
        if day in self.selected_days:
            self.selected_days.remove(day)
        else:
            self.selected_days.add(day)
        self._refresh_calendar_text()
        self._refresh_result_list()

    def _switch_month(self):
        self.selected_days.clear()
        self.assignments.clear()
        self._draw_calendar()
        self._refresh_result_list()

    def _random_pick_days(self):
        y, m = self.year.get(), self.month.get()
        _, num_days = calendar.monthrange(y, m)
        k = max(1, min(self.k_pick.get(), num_days))
        all_days = list(range(1, num_days+1))
        self.selected_days = set(random.sample(all_days, k))
        self._refresh_calendar_text()
        self._refresh_result_list()

    def _clear_selected(self):
        self.selected_days.clear()
        self.assignments.clear()
        self._refresh_calendar_text()
        self._refresh_result_list()

    # ---------- 组操作 ----------
    def _refresh_group_list(self):
        self.group_list.delete(0, tk.END)
        for g, items in self.groups.items():
            self.group_list.insert(tk.END, f"{g}  ({len(items)} 项) -> {', '.join(items)}")

    def _add_or_update_group(self):
        g = self.new_g.get().strip()
        items = [x.strip() for x in self.new_items.get().split(",") if x.strip()]
        if not g:
            messagebox.showerror("错误","请填写组名"); return
        if not items:
            messagebox.showerror("错误","请填写至少一个内容"); return
        self.groups[g] = items
        self.new_g.set(""); self.new_items.set("")
        self._refresh_group_list()

    def _delete_group(self):
        sel = self.group_list.curselection()
        if not sel: return
        text = self.group_list.get(sel[0])
        g = text.split("  (",1)[0]
        if g in self.groups: del self.groups[g]
        # 同时把已分配里的这个组清掉
        for d in list(self.assignments.keys()):
            if g in self.assignments.get(d, {}):
                del self.assignments[d][g]
                if not self.assignments[d]: del self.assignments[d]
        self._refresh_group_list()
        self._refresh_calendar_text()
        self._refresh_result_list()

    def _assign_group_to_days(self):
        # 需要已选日期与选中组
        if not self.selected_days:
            messagebox.showwarning("提示","先在日历选一些日期或随机选择K天"); return
        sel = self.group_list.curselection()
        if not sel:
            messagebox.showwarning("提示","在左侧列表选中一个组"); return
        g_text = self.group_list.get(sel[0])
        g = g_text.split("  (",1)[0]
        options = self.groups.get(g, [])
        if not options:
            messagebox.showerror("错误", f"组“{g}”没有内容"); return

        # 对每个已选日期，给该组随机一个内容（同日同组只保留一条）
        for d in sorted(self.selected_days):
            if d not in self.assignments: self.assignments[d] = {}
            self.assignments[d][g] = random.choice(options)

        self._refresh_calendar_text()
        self._refresh_result_list()

    # ---------- 输出 ----------
    def _refresh_result_list(self):
        self.result_list.delete(0, tk.END)
        y, m = self.year.get(), self.month.get()
        rows = 0
        for d in sorted(self.assignments.keys()):
            for g, n in sorted(self.assignments[d].items()):
                self.result_list.insert(tk.END, f"{y}-{m:02d}-{d:02d}  →  {g} / {n}")
                rows += 1
        if rows:
            self.result_list.insert(0, f"共 {rows} 条（覆盖 {len(self.assignments)} 天）")

    def _export_csv(self):
        if not self.assignments:
            messagebox.showwarning("暂无数据","先分派再导出"); return
        fp = filedialog.asksaveasfilename(title="保存为 CSV", defaultextension=".csv",
                                          filetypes=[("CSV 文件","*.csv"),("所有文件","*.*")])
        if not fp: return
        y, m = self.year.get(), self.month.get()
        with open(fp, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f); w.writerow(["Date","Group","Content"])
            for d in sorted(self.assignments.keys()):
                for g, n in sorted(self.assignments[d].items()):
                    w.writerow([f"{y}-{m:02d}-{d:02d}", g, n])
        messagebox.showinfo("导出成功", fp)

    def _copy_result(self):
        if not self.assignments:
            messagebox.showwarning("暂无数据","先分派再复制"); return
        y, m = self.year.get(), self.month.get()
        lines = [f"{APP_TITLE}（{y}-{m:02d}）"]
        for d in sorted(self.assignments.keys()):
            for g, n in sorted(self.assignments[d].items()):
                lines.append(f"{y}-{m:02d}-{d:02d}\t{g}\t{n}")
        text = "\n".join(lines)
        self.clipboard_clear(); self.clipboard_append(text)
        messagebox.showinfo("已复制","结果已在剪贴板")

if __name__ == "__main__":
    App().mainloop()
