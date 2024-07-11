from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from itertools import permutations

def get_feedback(response):
    a_index = response.index('A')
    b_index = response.index('B')
    a = int(response[a_index-1])
    b = int(response[b_index-1])
    return a, b

def filter_solutions(guess, a, b, solutions):
    def feedback(guess, solution):
        a_count = sum(1 for g, s in zip(guess, solution) if g == s)
        b_count = sum(1 for g in guess if g in solution) - a_count
        return a_count, b_count

    return [s for s in solutions if feedback(guess, s) == (a, b)]

def make_guess(guess):
    input_box = driver.find_element(By.ID, "guess")
    number_buttons = driver.find_element(By.ID, "numberButtons")
    for digit in guess:
        button = number_buttons.find_element(By.XPATH, f".//button[text()='{digit}']")
        button.click()
    time.sleep(1)  # 等待反應

def get_response():
    messages = driver.find_elements(By.CLASS_NAME, "message")
    for message in reversed(messages):
        if 'A' in message.text and 'B' in message.text:
            response = message.text
            return get_feedback(response)
    return 0, 0

# 初始化瀏覽器
options = Options()
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://s123104.github.io/az.tool/1A2B.html")

# 所有可能的數字組合
solutions = [''.join(p) for p in permutations('0123456789', 4)]

def play_game():
    global solutions
    guess = "1234"
    while True:
        make_guess(guess)
        a, b = get_response()
        print(f"Guess: {guess}, {a}A{b}B")

        if a == 4:
            print(f"找到答案: {guess}")
            break

        solutions = filter_solutions(guess, a, b, solutions)
        if solutions:
            guess = solutions[0]
        else:
            break  # 無法繼續猜測

while True:
    play_game()
    print("等待遊戲重新開始...")
    # 等待新的遊戲開始訊息
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'新遊戲開始了')]")))
    solutions = [''.join(p) for p in permutations('0123456789', 4)]  # 重置可能的數字組合

# 遊戲結束後繼續停留在畫面上
input("按下 Enter 鍵以結束程式...")
driver.quit()
