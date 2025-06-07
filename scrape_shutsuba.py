import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import time
import re

def scrape_race_card(url, common_data, driver):
    """
    指定されたURLの出馬表から各馬の情報をスクレイピングする関数

    Args:
        url (str): netkeibaの出馬表ページのURL
        common_data (dict): 全馬共通のレース情報
        driver: 使用するSeleniumのWebDriverインスタンス

    Returns:
        list: 各馬の情報を辞書として格納したリスト
    """
    try:
        driver.get(url)
        time.sleep(3)  # ページが完全に読み込まれるのを待つ
    except Exception as e:
        print(f"URLへのアクセスに失敗しました: {url} - エラー: {e}")
        return []

    horse_data_list = []

    try:
        # 出馬表のテーブル内の全行(tr)を取得
        # classに"RaceTable01"を含むtable要素をターゲットにする
        horse_table = driver.find_element(By.CLASS_NAME, 'RaceTable01')
        rows = horse_table.find_elements(By.TAG_NAME, 'tr')
    except NoSuchElementException:
        print(f"出馬表テーブルが見つかりませんでした: {url}")
        return []

    print(f"\n{len(rows)} 頭の馬情報が見つかりました。データの取得を開始します...")

    for i, row in enumerate(rows):
        try:
            # 各列(td)からデータを抽出
            cells = row.find_elements(By.TAG_NAME, 'td')
            if not cells:  # ヘッダー行などtdがない行はスキップ
                continue

            # 各情報をXPathや相対位置で取得
            waku_ban = cells[0].text.strip()
            uma_ban = cells[1].text.strip()
            horse_name = cells[3].find_element(By.CLASS_NAME, 'HorseName').text.strip()
            kinryo = cells[5].text.strip()
            jockey = cells[6].find_element(By.TAG_NAME, 'a').text.strip()
            
            # オッズと人気は別テーブルの場合があるが、多くは同じ行のtdに入っている
            # tdのインデックスは0から始まる
            odds = cells[9].text.strip()
            popularity = cells[10].text.strip()
            
            # 馬体重と増減の処理
            horse_weight_full = cells[8].text.strip()
            horse_weight = ""
            horse_weight_diff = ""
            # 正規表現で "体重(増減)" の形を抽出
            match = re.match(r'(\d+)\((.+)\)', horse_weight_full)
            if match:
                horse_weight = match.group(1)
                horse_weight_diff = match.group(2)
            elif horse_weight_full.isdigit(): # 増減がない場合
                horse_weight = horse_weight_full
                horse_weight_diff = "0"
            else: # "--"などの場合
                horse_weight = "計不" # 計測不能
                horse_weight_diff = ""

            # 1頭分のデータを辞書にまとめる
            horse_info = {
                "レース名": common_data["レース名"],
                "天気": common_data["天気"],
                "R": common_data["R"],
                "頭数": common_data["頭数"],
                "馬場": common_data["馬場"],
                "馬名": horse_name,
                "枠番": waku_ban,
                "馬番": uma_ban,
                "オッズ": odds,
                "人気": popularity,
                "騎手": jockey,
                "斤量": kinryo,
                "馬体重": horse_weight,
                "馬体重の増減": horse_weight_diff,
            }
            horse_data_list.append(horse_info)
            print(f"  > 取得成功: {uma_ban}番 {horse_name}")

        except Exception as e:
            # 広告行などでエラーが出てもスキップして処理を続ける
            # print(f"  > 行 {i+1} でデータ抽出エラー: {e}。この行をスキップします。")
            continue
            
    return horse_data_list

if __name__ == '__main__':
    # 1. 共通情報の入力
    print("--- 予測対象レースの共通情報を入力してください ---")
    race_url = input("netkeibaの出馬表URLを貼り付けてください: ")
    race_name_input = input("レース名（例: 日本ダービー(G1)）: ")
    weather_input = input("天気を入力してください（例: 晴）: ")
    round_input = input("レース番号を入力してください（例: 11）: ")
    num_horses_input = input("頭数を入力してください（例: 18）: ")
    track_condition_input = input("馬場状態を入力してください（例: 良）: ")

    common_race_data = {
        "レース名": race_name_input,
        "天気": weather_input,
        "R": round_input,
        "頭数": num_horses_input,
        "馬場": track_condition_input,
    }

    # 2. WebDriverのセットアップ
    print("\nWebDriverを初期化しています...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('window-size=1920x1080')
    driver = webdriver.Chrome(service=service, options=options)

    # 3. スクレイピングの実行
    all_horse_data = scrape_race_card(race_url, common_race_data, driver)

    # WebDriverを終了
    driver.quit()

    # 4. CSVファイルへの保存
    if all_horse_data:
        df = pd.DataFrame(all_horse_data)
        
        # ファイル名に使えない文字を置換
        safe_race_name = re.sub(r'[\\|/|:|?|.|"|<|>|\|]', '-', race_name_input)
        output_filename = f"predict_data_{safe_race_name}.csv"
        
        print(f"\nスクレイピングが完了しました。データを'{output_filename}'に保存します...")
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print("保存が完了しました。")
    else:
        print("\nデータを取得できませんでした。CSVファイルは作成されませんでした。")