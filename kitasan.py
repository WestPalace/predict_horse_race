from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import time
import re

def scrape_kitasan_black_races(url):
    """
    指定されたURLからキタサンブラックのレース情報をスクレイピングする関数

    Args:
        url (str): netkeiba.comのキタサンブラックの馬詳細ページのURL

    Returns:
        list: 各レース情報を辞書として格納したリスト
    """
    # Chromeドライバーのセットアップ
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # ブラウザを非表示で実行
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    time.sleep(3)  # ページが完全に読み込まれるのを待つ

    race_data_list = []

    # 戦績テーブルの行を取得
    # XPathのベース: //*[@id="contents"]/div[5]/div/table/tbody
    # 各行: tr
    try:
        race_table_body = driver.find_element(By.XPATH, '//*[@id="contents"]/div[5]/div/table/tbody')
        rows = race_table_body.find_elements(By.XPATH, './tr')
    except NoSuchElementException:
        print("戦績テーブルが見つかりませんでした。")
        driver.quit()
        return []

    print(f"{len(rows)} 件のレースが見つかりました。")

    for i, row in enumerate(rows):
        try:
            # 各列からデータを抽出 (XPathは0ベースではなく1ベースなので注意)
            # 提供されたXPathは tr[1] を基準にしているので、ここでは相対パス ./td[index] を使用
            race_name_element = row.find_element(By.XPATH, './td[5]/a')
            race_name = race_name_element.text.strip()
            race_url = race_name_element.get_attribute('href') # 参考情報としてレース詳細URLも取得

            weather = row.find_element(By.XPATH, './td[3]').text.strip()
            round_num_text = row.find_element(By.XPATH, './td[4]').text.strip() # "11R"など
            num_horses = row.find_element(By.XPATH, './td[7]').text.strip()
            waku_ban = row.find_element(By.XPATH, './td[8]').text.strip()
            uma_ban = row.find_element(By.XPATH, './td[9]').text.strip()
            odds = row.find_element(By.XPATH, './td[10]').text.strip()
            popularity = row.find_element(By.XPATH, './td[11]').text.strip()
            arrival_order = row.find_element(By.XPATH, './td[12]').text.strip()
            jockey = row.find_element(By.XPATH, './td[13]/a').text.strip()
            kinryo = row.find_element(By.XPATH, './td[14]').text.strip()
            baba_condition = row.find_element(By.XPATH, './td[16]').text.strip()
            horse_weight_full = row.find_element(By.XPATH, './td[24]').text.strip() # "534(+4)"など

            # 馬体重と増減を分割
            horse_weight = ""
            horse_weight_diff = ""
            match = re.match(r'(\d+)\((.*?)\)', horse_weight_full)
            if match:
                horse_weight = match.group(1)
                horse_weight_diff = match.group(2)
            elif horse_weight_full.isdigit(): # 増減がない場合 (例: "500")
                horse_weight = horse_weight_full
                horse_weight_diff = "0"


            race_info = {
                "レース名": race_name,
                "天気": weather,
                "R": round_num_text, # Rを抽出 (例: "11R" -> "11") する場合は re.sub(r'\D', '', round_num_text)
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
                # "レース詳細URL": race_url # 参考
            }
            race_data_list.append(race_info)
            print(f"取得成功: {race_name}")

        except NoSuchElementException as e:
            # １つのレースで一部の要素が見つからない場合（通常はありえないが念のため）
            # テーブルの構造が異なる行（例：ヘッダーがtbody内にあるなど特殊な場合）はスキップ
            print(f"行 {i+1} のデータ取得中にエラー: {e}. この行をスキップします。")
            # ページの構造によっては、特定の行が広告や異なる情報を含んでいる場合があるので、
            # その場合はより詳細な条件でtrをフィルタリングする必要があるかもしれません。
            # 今回のnetkeibaの馬詳細ページでは、tbody内のtrは基本的にレース結果のはずです。
            continue
        except Exception as e:
            print(f"行 {i+1} で予期せぬエラー: {e}")
            continue

    driver.quit()
    return race_data_list

if __name__ == '__main__':
    target_url = "https://db.netkeiba.com/horse/2012102013/"
    kitasan_races = scrape_kitasan_black_races(target_url)

    if kitasan_races:
        print("\n--- 取得したレースデータ ---")
        for race in kitasan_races:
            print(race)

        # CSVファイルとして保存する場合の例 (pandasが必要)
        # import pandas as pd
        # df = pd.DataFrame(kitasan_races)
        # df.to_csv("kitasan_black_race_data.csv", index=False, encoding='utf-8-sig')
        # print("\nCSVファイル 'kitasan_black_race_data.csv' に保存しました。")