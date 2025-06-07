import pandas as pd
import joblib
import sys
import os

def predict_race_outcome(prediction_file_path):
    """
    学習済みモデルを使い、出馬表データの着順を予測する関数

    Args:
        prediction_file_path (str): 予測したいレースのCSVファイルへのパス
    """
    # --- 1. モデルとデータの読み込み ---
    print("--- 1. モデル、エンコーダー、予測用データの読み込み ---")
    
    # モデルとエンコーダーのファイルパス
    model_path = 'random_forest_model.joblib'
    encoders_path = 'label_encoders.joblib'

    # ファイルの存在チェック
    if not os.path.exists(model_path) or not os.path.exists(encoders_path):
        print(f"エラー: '{model_path}' または '{encoders_path}' が見つかりません。")
        print("先に 'train_model.py' を実行して、モデルを学習・保存してください。")
        return

    try:
        model = joblib.load(model_path)
        encoders = joblib.load(encoders_path)
        predict_df = pd.read_csv(prediction_file_path)
        print("モデル、エンコーダー、予測用データの読み込みが完了しました。")
    except FileNotFoundError:
        print(f"エラー: 予測用ファイル '{prediction_file_path}' が見つかりません。")
        return
    except Exception as e:
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return

    # 馬名を後で使うために保持しておく
    horse_names = predict_df['馬名']
    # 予測に使う特徴量のデータフレームをコピー
    X_predict = predict_df.drop('馬名', axis=1).copy()


    # --- 2. 予測データの整形と前処理 ---
    print("\n--- 2. 予測用データの前処理 ---")
    
    # 'R'列を数値に変換
    if 'R' in X_predict.columns and X_predict['R'].dtype == 'object':
        X_predict['R'] = X_predict['R'].str.replace('R', '').astype(int)

    # 数値であるべき列を数値型に変換（変換できないものはNaNにする）
    numeric_cols = ['R', '頭数', '枠番', '馬番', 'オッズ', '人気', '斤量', '馬体重', '馬体重の増減']
    for col in numeric_cols:
        if col in X_predict.columns:
            X_predict[col] = pd.to_numeric(X_predict[col], errors='coerce')
    
    # もしNaNがあれば、中央値で補完（学習データがないため暫定的に予測データの中央値を使用）
    for col in X_predict.columns:
        if X_predict[col].isnull().any():
            median_val = X_predict[col].median()
            X_predict[col].fillna(median_val, inplace=True)
            print(f"'{col}'列の欠損値を中央値({median_val})で補完しました。")

    # カテゴリ変数を保存したエンコーダーで数値に変換
    categorical_cols = ['レース名', '天気', '騎手', '馬場']
    for col in categorical_cols:
        if col in encoders:
            le = encoders[col]
            
            # 学習時に存在しなかった新しいカテゴリ（例：初騎乗の騎手）に対応する処理
            # applyとlambdaを使い、知らないカテゴリは-1（不明な値）に変換する
            X_predict[col] = X_predict[col].apply(
                lambda x: le.transform([x])[0] if x in le.classes_ else -1
            )
            print(f"'{col}'列を保存済みルールで数値に変換しました。")

    # 学習時と同じ列の順番に並び替える
    # model.feature_names_in_ に学習時の特徴量の名前と順番が保存されている
    try:
        X_predict = X_predict[model.feature_names_in_]
        print("特徴量の列順を学習時と一致させました。")
    except Exception as e:
        print(f"エラー: 特徴量の列順を揃える際に問題が発生しました。{e}")
        print("学習時と予測時でCSVの列名が異なっている可能性があります。")
        return
    
    # --- 3. 着順の予測 ---
    print("\n--- 3. 着順の予測実行 ---")
    predictions = model.predict(X_predict)
    print("予測が完了しました。")

    # --- 4. 結果の表示 ---
    print("\n--- ★★★ 最終予測結果 ★★★ ---")
    results_df = pd.DataFrame({
        '馬名': horse_names,
        '予測着順': predictions
    })

    # 予測着順の昇順で並べ替え
    results_df_sorted = results_df.sort_values(by='予測着順')

    # 結果をきれいに表示
    print(results_df_sorted.to_string(index=False))


if __name__ == '__main__':
    # コマンドラインから予測用CSVファイル名を取得
    if len(sys.argv) > 1:
        prediction_csv_file = sys.argv[1]
        predict_race_outcome(prediction_csv_file)
    else:
        print("エラー: 予測対象のCSVファイルを指定してください。")
        print("使い方: python predict_race.py 'predict_data_日本ダービー(G1).csv'")