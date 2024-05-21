# 導入 tkinter 模組
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import csv

# 函數：從 CSV 文件中讀取地址


def read_csv(filename):
    addresses = []
    with open(filename, 'r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            addresses.extend(row)
    return addresses

# 函數：批量查詢 CSV 文件中的地址


def batch_query_csv(filename, addresses):
    data = read_csv(filename)
    results = {"Found": [], "Not Found": []}
    for address in addresses:
        if address in data:
            results["Found"].append(address)
        else:
            results["Not Found"].append(address)
    return results

# 函數：顯示查詢結果


def show_results(results):
    # 創建新的窗口來顯示結果
    result_window = tk.Toplevel(root)
    result_window.title("查詢結果")

    # 創建表格來顯示結果
    tree = ttk.Treeview(result_window, columns=("Address", "Status"))
    tree.heading("#0", text="Index", anchor="center")
    tree.heading("Address", text="Address", anchor="center")
    tree.heading("Status", text="Status", anchor="center")

    # 設定表格欄位寬度
    tree.column("#0", width=50, anchor="center")  # Index 欄位
    tree.column("Address", width=200, anchor="center")  # Address 欄位
    tree.column("Status", width=100, anchor="center")  # Status 欄位

    # 遍歷結果並將其添加到表格中
    index = 1
    for status, addresses in results.items():
        for address in addresses:
            tree.insert("", "end", text=index, values=(address, status))
            index += 1

    tree.pack(fill="both", expand=True)

    # 彈出消息框，顯示統計信息
    total_found = len(results["Found"])
    total_not_found = len(results["Not Found"])
    messagebox.showinfo(
        "統計", f"女巫名單中的地址數量：{total_found}\n不在名單中的地址數量：{total_not_found}")

# 函數：執行地址查詢


def query_addresses():
    addresses = address_text.get("1.0", tk.END).splitlines()
    addresses = [address.strip() for address in addresses if address.strip()]
    if not addresses:
        messagebox.showwarning("警告", "請輸入要查詢的地址")
        return
    results = batch_query_csv('initialList.csv', addresses)
    show_results(results)


# 創建主視窗
root = tk.Tk()
root.title("批量地址查詢")
root.geometry("400x300")

# 創建文字輸入框和捲軸
address_text = tk.Text(root, wrap="word", height=10)
address_text.pack(fill="both", expand=True, padx=10, pady=10)

scrollbar = tk.Scrollbar(root, orient="vertical", command=address_text.yview)
scrollbar.pack(side="right", fill="y")

address_text.config(yscrollcommand=scrollbar.set)

# 創建右鍵菜單


def make_right_click_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(
        label="剪切", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(
        label="複製", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(
        label="貼上", command=lambda: widget.event_generate("<<Paste>>"))
    return menu

# 綁定右鍵菜單


def show_right_click_menu(event):
    right_click_menu.tk_popup(event.x_root, event.y_root)


right_click_menu = make_right_click_menu(address_text)
address_text.bind("<Button-3>", show_right_click_menu)

# 創建查詢按鈕
query_button = tk.Button(root, text="查詢", command=query_addresses)
query_button.pack(pady=10)

# 啟動主視窗的主事件循環
root.mainloop()
