import pandas as pd

# 1. ファイル名を定義します
# 読み込む元のファイル
input_filename = 'all_horses_race_data_appended.csv'
# 保存する新しいファイル
output_filename = 'cleaned_race_data.csv'

try:
    # 2. 元のCSVファイルを読み込みます
    print(f"元のファイル '{input_filename}' を読み込んでいます...")
    df = pd.read_csv(input_filename)
    print("読み込みが完了しました。")

    # 処理前の行数を確認
    rows_before = len(df)
    print(f"処理前の行数: {rows_before}")
    
    # 3. 欠損値を含む行をすべて削除します
    print("\n欠損値を含む行を削除しています...")
    df_cleaned = df.dropna()
    print("削除が完了しました。")

    # 処理後の行数を確認
    rows_after = len(df_cleaned)
    print(f"処理後の行数: {rows_after}")
    print(f"削除された行数: {rows_before - rows_after}")

    # 4. 処理後のデータを「新しいCSVファイル」として保存します
    # df_cleaned に格納された、欠損行がないデータだけを output_filename で指定したファイルに書き出します。
    # 元の input_filename のファイルが変更されることはありません。
    print(f"\n処理後のデータを新しいファイル '{output_filename}' に保存しています...")
    df_cleaned.to_csv(output_filename, index=False, encoding='utf-8-sig')
    print("保存が完了しました。")

except FileNotFoundError:
    print(f"エラー: ファイル '{input_filename}' が見つかりませんでした。")
except Exception as e:
    print(f"予期せぬエラーが発生しました: {e}")