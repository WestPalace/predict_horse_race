from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException
import time

def scrape_horse_list_urls(url):
    """
    指定されたnetkeiba.comの馬リストページから各馬の詳細ページURLを抽出する関数

    Args:
        url (str): netkeiba.comの馬リストページのURL

    Returns:
        list: 抽出された馬詳細ページのURLのリスト
    """
    # Chromeドライバーのセットアップ
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # ブラウザを非表示で実行
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # headless実行時にウィンドウサイズを指定しないと要素が見つからない場合があるため追加
    options.add_argument('window-size=1920x1080')


    # driverの初期化はtry-exceptの外で行う
    driver = webdriver.Chrome(service=service, options=options)
    horse_detail_urls_on_page = [] # このページで抽出したURLを格納するリスト

    try:
        driver.get(url)
        # ページの読み込み状態を確認 (より堅牢な待機方法の例)
        # WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.XPATH, '//*[@id="result_form"]/table/tbody'))
        # )
        time.sleep(3)  # 簡易的な待機

        # テーブルのtbody要素を取得
        table_body = driver.find_element(By.XPATH, '//*[@id="result_form"]/table/tbody')
        # tbody内の全てのtr要素 (各馬の行) を取得
        rows = table_body.find_elements(By.XPATH, './tr')
        
        if not rows: # 行が見つからなかった場合
            print(f"URL: {url} で馬リストの行が見つかりませんでした。")
            driver.quit()
            return []

        print(f"URL: {url} で {len(rows)} 件の行が見つかりました。")

        for i, row in enumerate(rows):
            try:
                link_element = row.find_element(By.XPATH, './td[2]/a')
                horse_url = link_element.get_attribute('href')
                if horse_url:
                    horse_detail_urls_on_page.append(horse_url)
                else:
                    print(f"行 {i+1} (URL: {url}) でURLが見つかりませんでした（href属性が空）。")

            except NoSuchElementException:
                print(f"行 {i+1} (URL: {url}) には期待するリンク要素（./td[2]/a）が見つかりませんでした。この行をスキップします。")
                continue
            except Exception as e:
                print(f"行 {i+1} (URL: {url}) で予期せぬエラー: {e}")
                continue
    
    except NoSuchElementException:
        print(f"URL: {url} で馬リストのテーブルが見つかりませんでした。")
    except Exception as e:
        print(f"URL: {url} の処理中にエラーが発生しました: {e}")
    finally:
        driver.quit() # tryブロック内でエラーが発生しても必ずWebDriverを閉じる

    return horse_detail_urls_on_page

if __name__ == '__main__':
    base_target_list_url = "https://db.netkeiba.com/?pid=horse_list&word=&match=partial_match&sire=&keito=&mare=&bms=&trainer=&owner=&breeder=&sex%5B%5D=1&sex%5B%5D=2&under_age=3&over_age=none&under_birthmonth=1&over_birthmonth=12&under_birthday=1&over_birthday=31&grade%5B%5D=4&grade%5B%5D=3&prize_min=&prize_max=&sort=prize&list=100"
    
    all_extracted_urls = []
    max_page = 49  # ユーザーの指示通り49ページまで

    # 1ページ目 (元のURL、page=1相当)
    print(f"処理中: 1ページ目 - URL: {base_target_list_url}")
    urls_from_page = scrape_horse_list_urls(base_target_list_url)
    if urls_from_page:
        all_extracted_urls.extend(urls_from_page)
        print(f"1ページ目から {len(urls_from_page)} 件のURLを抽出しました。")
    else:
        print(f"1ページ目 ({base_target_list_url}) からURLは抽出されませんでした。")
    
    # 2ページ目から指定された最大ページまで
    for page_num in range(2, max_page + 1):
        target_url_with_page = f"{base_target_list_url}&page={page_num}"
        print(f"処理中: {page_num}ページ目 - URL: {target_url_with_page}")
        
        urls_from_page = scrape_horse_list_urls(target_url_with_page)
        if urls_from_page:
            all_extracted_urls.extend(urls_from_page)
            print(f"{page_num}ページ目から {len(urls_from_page)} 件のURLを抽出しました。")
        else:
            print(f"{page_num}ページ目 ({target_url_with_page}) からURLは抽出されませんでした。")
        
        # サーバーへの負荷を考慮して、リクエスト間に短い待機時間を設ける
        # scrape_horse_list_urls 関数内で既に3秒の待機があるため、
        # ここでの追加待機は任意ですが、長時間の連続アクセスでは推奨されます。
        # time.sleep(1) # 例: 1秒待機

    # 全ての抽出結果を表示・保存
    if all_extracted_urls:
        print(f"\n--- 全ページから抽出された馬詳細ページのURL (合計: {len(all_extracted_urls)}件) ---")
        # 全URLの表示は長くなる可能性があるため、必要に応じてコメントアウトを解除してください
        # for url in all_extracted_urls:
        #     print(url)
        
        # 重複を削除したい場合は以下のようにセットに変換してからリストに戻す
        # unique_urls = list(set(all_extracted_urls))
        # print(f"\n重複を除いたURLの件数: {len(unique_urls)}")

        # ファイルに保存する場合の例
        output_filename = "horse_urls_all_pages.txt"
        with open(output_filename, "w", encoding='utf-8') as f:
            for url in all_extracted_urls: # 重複を許す場合は all_extracted_urls, 除く場合は unique_urls
                f.write(url + "\n")
        print(f"\n抽出されたURLを '{output_filename}' に保存しました。")
    else:
        print("URLは一件も抽出されませんでした。")