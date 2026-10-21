import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'deps'))
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '60'
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from transcribe_core import identity, load_state, save_state, completed, convert_one, Stopped


class App:
    def __init__(self, root):
        self.root = root
        root.title('MP3 批量转 TXT · Nox-Ding')
        root.geometry('820x630')
        root.minsize(710, 540)
        self.paths = []
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.running = False
        self.controls = []
        style = ttk.Style()
        style.theme_use('vista')
        style.configure('.', font=('Microsoft YaHei UI', 10))
        frame = ttk.Frame(root, padding=18)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Nox-Ding', foreground='#667085', font=('Microsoft YaHei UI', 10)).pack(side='bottom', anchor='e', pady=(8, 0))
        header = ttk.Frame(frame)
        header.pack(fill='x')
        ttk.Label(header, text='MP3 批量转 TXT', font=('Microsoft YaHei UI', 18, 'bold')).pack(side='left')
        ttk.Label(header, text='Nox-Ding', foreground='#667085', font=('Microsoft YaHei UI', 12, 'bold')).pack(side='right')
        ttk.Label(frame, text='音频在本机识别，不上传。内置 small 模型；切换其他模型首次使用需联网下载。').pack(anchor='w', pady=(6, 12))
        row = ttk.Frame(frame); row.pack(fill='x')
        for label, command in [('添加音频', self.add_files), ('添加文件夹', self.add_folder), ('清空列表', self.clear)]:
            button = ttk.Button(row, text=label, command=command); button.pack(side='left', padx=(0, 8)); self.controls.append(button)
        self.listbox = tk.Listbox(frame, height=8, font=('Microsoft YaHei UI', 10))
        self.listbox.pack(fill='both', expand=True, pady=10)
        row = ttk.Frame(frame); row.pack(fill='x', pady=5)
        ttk.Label(row, text='TXT 保存目录：').pack(side='left')
        self.folder = tk.StringVar(value=str(ROOT / '转写结果'))
        entry = ttk.Entry(row, textvariable=self.folder); entry.pack(side='left', fill='x', expand=True); self.controls.append(entry)
        button = ttk.Button(row, text='选择', command=self.choose_folder); button.pack(side='left', padx=5); self.controls.append(button)
        row = ttk.Frame(frame); row.pack(fill='x', pady=5)
        ttk.Label(row, text='识别模型：').pack(side='left')
        self.model = tk.StringVar(value='small')
        self.models = ttk.Combobox(row, textvariable=self.model, values=['base', 'small', 'medium', 'large-v3'], state='readonly', width=12)
        self.models.pack(side='left'); self.controls.append(self.models)
        ttk.Label(row, text='small 均衡；base 较快；medium / large-v3 较慢、资源占用更高').pack(side='left', padx=8)
        self.skip = tk.BooleanVar(value=True)
        button = ttk.Checkbutton(frame, text='跳过本程序在此目录已完成的文件（再次打开可接续批量任务）', variable=self.skip)
        button.pack(anchor='w', pady=5); self.controls.append(button)
        row = ttk.Frame(frame); row.pack(fill='x', pady=8)
        self.start_button = ttk.Button(row, text='开始转换', command=self.start); self.start_button.pack(side='left')
        self.stop_button = ttk.Button(row, text='停止并保留已识别文字', command=self.stop, state='disabled'); self.stop_button.pack(side='left', padx=10)
        ttk.Button(row, text='打开结果目录', command=self.open_folder).pack(side='left')
        self.progress = ttk.Progressbar(frame, maximum=100); self.progress.pack(fill='x', pady=5)
        self.status = tk.StringVar(value='添加音频或文件夹，然后开始。已存在的 TXT 不会被覆盖。')
        ttk.Label(frame, textvariable=self.status, wraplength=760).pack(anchor='w')
        self.log = tk.Text(frame, height=6, font=('Microsoft YaHei UI', 9), state='disabled')
        self.log.pack(fill='x', pady=(8, 0))
        root.after(100, self.poll)
        root.protocol('WM_DELETE_WINDOW', self.close)

    def add(self, files):
        seen = {str(p).casefold() for p in self.paths}
        for value in files:
            path = Path(value).resolve()
            if path.suffix.lower() in {'.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma'} and str(path).casefold() not in seen:
                self.paths.append(path); seen.add(str(path).casefold()); self.listbox.insert('end', str(path))
        self.status.set('共选择 %s 个音频' % len(self.paths))

    def add_files(self):
        self.add(filedialog.askopenfilenames(filetypes=[('音频', '*.mp3 *.wav *.m4a *.flac *.aac *.ogg *.wma'), ('所有文件', '*.*')]))

    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.add(sorted(p for p in Path(folder).rglob('*') if p.is_file()))

    def clear(self):
        self.paths.clear(); self.listbox.delete(0, 'end')

    def choose_folder(self):
        value = filedialog.askdirectory()
        if value: self.folder.set(value)

    def open_folder(self):
        try:
            path = Path(self.folder.get()); path.mkdir(parents=True, exist_ok=True); os.startfile(path)
        except Exception as error: messagebox.showerror('无法打开目录', str(error))

    def start(self):
        if self.running: return
        if not self.paths:
            messagebox.showinfo('请先选择音频', '可添加多个文件，或添加整个文件夹。'); return
        if not self.folder.get().strip():
            messagebox.showinfo('请选择目录', '请设置 TXT 保存目录。'); return
        self.running = True; self.cancel.clear()
        self.start_button.configure(state='disabled'); self.stop_button.configure(state='normal')
        for control in self.controls: control.configure(state='disabled')
        self.progress['value'] = 0
        threading.Thread(target=self.work, args=(list(self.paths), self.folder.get(), self.model.get(), self.skip.get()), daemon=True).start()

    def stop(self):
        self.cancel.set()
        self.status.set('正在停止；等待当前识别片段或模型加载结束，已识别文字会保留。')

    def work(self, paths, folder, size, skip):
        done = failed = skipped = 0
        try:
            from faster_whisper import WhisperModel
            from opencc import OpenCC
            folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
            state = load_state(folder)
            model = None; converter = OpenCC('t2s')
            for index, path in enumerate(paths):
                if self.cancel.is_set(): raise Stopped()
                try:
                    token = identity(path, size)
                    if skip and completed(folder, state.get(token)):
                        skipped += 1; self.events.put(('log', '跳过已完成：' + path.name)); continue
                    if model is None:
                        self.events.put(('status', '正在加载 ' + size + ' 模型，请稍候…'))
                        options = dict(device='cpu', compute_type='int8', cpu_threads=min(8, max(1, (os.cpu_count() or 4)-1)), download_root=str(ROOT / 'models'))
                        try:
                            model = WhisperModel(size, local_files_only=True, **options)
                        except Exception:
                            self.events.put(('status', '正在下载或加载 ' + size + ' 模型，首次可能持续数分钟。请保持网络畅通…'))
                            model = WhisperModel(size, **options)
                    if self.cancel.is_set(): raise Stopped()
                    self.events.put(('log', '开始：' + path.name))
                    def report(percent):
                        self.events.put(('progress', percent))
                        self.events.put(('status', '%s/%s · %s · %s%%' % (index+1, len(paths), path.name, percent)))
                    name = convert_one(model, path, folder, token, self.cancel, report, converter)
                    state[token] = {'name': name, 'source': str(path), 'model': size}
                    save_state(folder, state)
                    done += 1; self.events.put(('log', '完成：' + name))
                except Stopped: raise
                except Exception as error:
                    failed += 1; self.events.put(('log', '失败：' + path.name + ' — ' + str(error)))
                    if model is None: raise
            self.events.put(('status', '处理完成：成功 %s，跳过 %s，失败 %s。' % (done, skipped, failed)))
        except Stopped:
            self.events.put(('status', '已停止。完成文件保留；当前文件保留为“未完成.txt”，下次会重新识别当前文件。'))
        except Exception as error:
            self.events.put(('status', '无法继续：' + str(error)))
            self.events.put(('log', '如果是模型下载失败，请检查网络后重试；已完成文件不会丢失。'))
        finally: self.events.put(('done', None))

    def poll(self):
        for _ in range(200):
            try: kind, value = self.events.get_nowait()
            except queue.Empty: break
            if kind == 'status': self.status.set(value)
            elif kind == 'progress': self.progress['value'] = value
            elif kind == 'log':
                self.log.configure(state='normal'); self.log.insert('end', value+'\n'); self.log.see('end'); self.log.configure(state='disabled')
            elif kind == 'done':
                self.running = False; self.start_button.configure(state='normal'); self.stop_button.configure(state='disabled')
                for control in self.controls: control.configure(state='normal')
                self.models.configure(state='readonly')
        self.root.after(100, self.poll)

    def close(self):
        if self.running:
            self.stop()
            messagebox.showinfo('正在停止', '请等状态显示“已停止”后再关闭，当前识别片段或模型下载可能需要一点时间。')
        else: self.root.destroy()


if __name__ == '__main__':
    window = tk.Tk()
    app = App(window)
    window.mainloop()
