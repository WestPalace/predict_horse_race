import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import time
import re
import os # osライブラリをインポート

def scrape_horse_race_data(url, driver):
    """
    指定されたURLから一頭の馬の全レース情報をスクレイピングする関数
    (この関数自体に変更はありません)
    """
    try:
        driver.get(url)
        time.sleep(3)
    except Exception as e:
        print(f"URLへのアクセスに失敗しました: {url} - エラー: {e}")
        return []

    race_data_list = []

    try:
        race_table_body = driver.find_element(By.XPATH, '//table[contains(@class, "db_h_race_results")]/tbody')
        rows = race_table_body.find_elements(By.XPATH, './tr')
    except NoSuchElementException:
        print(f"戦績テーブルが見つかりませんでした: {url}")
        return []

    print(f"  > {len(rows)} 件のレースが見つかりました。")

    for i, row in enumerate(rows):
        try:
            race_name = row.find_element(By.XPATH, './td[5]/a').text.strip()
            weather = row.find_element(By.XPATH, './td[3]').text.strip()
            round_num_text = row.find_element(By.XPATH, './td[4]').text.strip()
            num_horses = row.find_element(By.XPATH, './td[7]').text.strip()
            waku_ban = row.find_element(By.XPATH, './td[8]').text.strip()
            uma_ban = row.find_element(By.XPATH, './td[9]').text.strip()
            odds = row.find_element(By.XPATH, './td[10]').text.strip()
            popularity = row.find_element(By.XPATH, './td[11]').text.strip()
            arrival_order = row.find_element(By.XPATH, './td[12]').text.strip()
            jockey = row.find_element(By.XPATH, './td[13]/a').text.strip()
            kinryo = row.find_element(By.XPATH, './td[14]').text.strip()
            baba_condition = row.find_element(By.XPATH, './td[16]').text.strip()
            horse_weight_full = row.find_element(By.XPATH, './td[24]').text.strip()

            horse_weight = ""
            horse_weight_diff = ""
            match = re.match(r'(\d+)\((.*?)\)', horse_weight_full)
            if match:
                horse_weight = match.group(1)
                horse_weight_diff = match.group(2)
            elif horse_weight_full.isdigit():
                horse_weight = horse_weight_full
                horse_weight_diff = "0"

            race_info = {
                "レース名": race_name,
                "天気": weather,
                "R": round_num_text,
                "頭数": num_horses,
                "枠番": waku_ban,
                "馬番": uma_ban,
                "オッズ": odds,
                "人気": popularity,
                "着順": arrival_order,
                "騎手": jockey,
                "斤量": kinryo,
                "馬場": baba_condition,
                "馬体重": horse_weight,
                "馬体重の増減": horse_weight_diff,
            }
            race_data_list.append(race_info)

        except NoSuchElementException:
            continue
        except Exception as e:
            print(f"  > 行 {i+1} でデータ抽出エラー: {e}")
            continue

    return race_data_list

if __name__ == '__main__':
    # URLリストをファイルから読み込む
    try:
        with open('horse_urls_all_pages.txt', 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"ファイルから {len(urls)} 件のURLを読み込みました。")
    except FileNotFoundError:
        print("エラー: horse_urls_all_pages.txt が見つかりません。")
        exit()
        
    output_filename = "all_horses_race_data_appended.csv"
    
    # 列の順番を定義
    column_order = [
        "レース名", "天気", "R", "頭数", "枠番", "馬番", 
        "オッズ", "人気", "着順", "騎手", "斤量", "馬場", 
        "馬体重", "馬体重の増減"
    ]

    # --- 変更点 ---
    # スクリプト開始時にファイルが存在しない場合、ヘッダー行だけを持つCSVファイルを新規作成する
    if not os.path.exists(output_filename):
        pd.DataFrame(columns=column_order).to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"'{output_filename}'を新規作成しました。")
    # --- 変更点ここまで ---

    # Chromeドライバーのセットアップ
    print("WebDriverを初期化しています...")
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('window-size=1920x1080')
    driver = webdriver.Chrome(service=service, options=options)

    total_urls = len(urls)

    # 各URLに対してスクレイピングと追記を実行
    for i, url in enumerate(urls):
        print(f"\n処理中 ({i+1}/{total_urls}): {url}")
        races = scrape_horse_race_data(url, driver)
        
        # --- 変更点 ---
        # データを取得できた場合のみ追記処理を行う
        if races:
            df_one_horse = pd.DataFrame(races)
            
            # DataFrameの列順を固定
            df_one_horse = df_one_horse[column_order]

            # 'mode="a"' (append)で追記, 'header=False'でヘッダーは追記しない
            df_one_horse.to_csv(output_filename, mode='a', header=False, index=False, encoding='utf-8-sig')
            print(f"  > 完了: {len(races)} 件のレースデータを '{output_filename}' に追記しました。")
        else:
            print("  > このURLからはデータを取得できませんでした。スキップします。")
        # --- 変更点ここまで ---
    
    # WebDriverを終了
    driver.quit()
    print(f"\n全ての処理が完了しました。データは '{output_filename}' に保存されています。")