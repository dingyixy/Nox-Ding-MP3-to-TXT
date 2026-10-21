using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;
internal static class Launcher
{
    [STAThread] static void Main()
    {
        bool created;
        using(var mutex = new System.Threading.Mutex(true, "Local\\MP3BatchTranscriber", out created))
        {
            if (!created) { MessageBox.Show("程序已经运行，请使用已打开的窗口。"); return; }
            string root = AppDomain.CurrentDomain.BaseDirectory;
            try
            {
                var start = new ProcessStartInfo(Path.Combine(root, "runtime", "pythonw.exe"), "\"" + Path.Combine(root, "app.py") + "\"");
                start.WorkingDirectory = root; start.UseShellExecute = false; start.CreateNoWindow = true;
                start.RedirectStandardError = true;
                using(var process = Process.Start(start))
                {
                    string error = process.StandardError.ReadToEnd(); process.WaitForExit();
                    if(process.ExitCode != 0)
                    {
                        File.WriteAllText(Path.Combine(root,"启动错误.txt"),error);
                        MessageBox.Show("程序遇到错误，详情已保存到“启动错误.txt”。请确认已完整解压程序。", "MP3 批量转 TXT");
                    }
                }
            }
            catch(Exception error) { MessageBox.Show(error.Message + "\n请完整解压后再运行。", "无法启动"); }
        }
    }
}
