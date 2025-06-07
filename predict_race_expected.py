import pandas as pd
import numpy as np
import joblib
import sys
import os

def predict_race_expected_value(prediction_file_path):
    """
    学習済みモデルを使い、予測着順の「期待値」を計算する関数

    Args:
        prediction_file_path (str): 予測したいレースのCSVファイルへのパス
    """
    # --- 1. モデルとデータの読み込み ---
    print("--- 1. モデル、エンコーダー、予測用データの読み込み ---")
    
    model_path = 'random_forest_model.joblib'
    encoders_path = 'label_encoders.joblib'

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

    horse_names = predict_df['馬名']
    X_predict = predict_df.drop('馬名', axis=1).copy()


    # --- 2. 予測データの整形と前処理 ---
    print("\n--- 2. 予測用データの前処理 ---")
    
    if 'R' in X_predict.columns and X_predict['R'].dtype == 'object':
        X_predict['R'] = X_predict['R'].str.replace('R', '').astype(int)

    numeric_cols = ['R', '頭数', '枠番', '馬番', 'オッズ', '人気', '斤量', '馬体重', '馬体重の増減']
    for col in numeric_cols:
        if col in X_predict.columns:
            X_predict[col] = pd.to_numeric(X_predict[col], errors='coerce')
    
    for col in X_predict.columns:
        if X_predict[col].isnull().any():
            median_val = X_predict[col].median()
            X_predict[col].fillna(median_val, inplace=True)
            print(f"'{col}'列の欠損値を中央値({median_val})で補完しました。")

    categorical_cols = ['レース名', '天気', '騎手', '馬場']
    for col in categorical_cols:
        if col in encoders:
            le = encoders[col]
            X_predict[col] = X_predict[col].apply(
                lambda x: le.transform([x])[0] if x in le.classes_ else -1
            )
            print(f"'{col}'列を保存済みルールで数値に変換しました。")

    try:
        X_predict = X_predict[model.feature_names_in_]
        print("特徴量の列順を学習時と一致させました。")
    except Exception as e:
        print(f"エラー: 特徴量の列順を揃える際に問題が発生しました。{e}")
        return
    
    # --- 3. 各着順の「確率」を予測 ---
    print("\n--- 3. 各着順の確率を予測実行 ---")
    # model.predict() の代わりに predict_proba() を使用
    predictions_proba = model.predict_proba(X_predict)
    print("確率の予測が完了しました。")

    # --- 4. 確率から期待値を計算 ---
    print("\n--- 4. 予測着順の期待値を計算 ---")
    # model.classes_ には、確率の各列がどの着順に対応するかが格納されている (例: [1, 2, 3, ...])
    expected_values = []
    for proba in predictions_proba:
        # 期待値 = Σ (着順 * その着順になる確率)
        expected_value = np.sum(model.classes_ * proba)
        expected_values.append(expected_value)
    
    print("期待値の計算が完了しました。")

    # --- 5. 結果の表示 ---
    print("\n--- ★★★ 最終予測結果 (期待値) ★★★ ---")
    results_df = pd.DataFrame({
        '馬名': horse_names,
        '予測着順 (期待値)': expected_values
    })

    results_df_sorted = results_df.sort_values(by='予測着順 (期待値)')

    # 小数点第2位まで表示するよう設定
    pd.options.display.float_format = '{:.2f}'.format
    print(results_df_sorted.to_string(index=False))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        prediction_csv_file = sys.argv[1]
        predict_race_expected_value(prediction_csv_file)
    else:
        print("エラー: 予測対象のCSVファイルを指定してください。")
        print("使い方: python predict_race_expected.py \"predict_data_日本ダービー(G1).csv\"")