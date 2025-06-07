import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib

def train_horse_racing_model(file_path):
    """
    競馬の着順予測モデルを学習し、保存する関数
    
    Args:
        file_path (str): データセットのCSVファイルへのパス
    """
    # 1. データの読み込み
    print("--- 1. データの読み込み ---")
    try:
        # DtypeWarningを避けるため、low_memory=Falseを指定
        df = pd.read_csv(file_path, low_memory=False)
        print(f"読み込み完了: {len(df)}件のレースデータ")
    except FileNotFoundError:
        print(f"エラー: ファイル '{file_path}' が見つかりません。")
        return

    # 2. 前処理
    print("\n--- 2. データの前処理 ---")

    # --- ★★★ 修正点1: データ型を強制し、追加で欠損値を削除 ★★★ ---
    print("数値列を強制的に数値型に変換し、変換不能な行を削除します...")
    numeric_cols = ['R', '頭数', '枠番', '馬番', 'オッズ', '人気', '着順', '斤量', '馬体重', '馬体重の増減']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 型変換によってNaNになった行を削除
    rows_before_dropna = len(df)
    df.dropna(inplace=True)
    rows_after_dropna = len(df)
    print(f"追加の欠損値処理完了。{rows_before_dropna - rows_after_dropna}件の行を削除しました。")

    # 着順を整数型に変換
    df['着順'] = df['着順'].astype(int)
    # --- ★★★ 修正ここまで ★★★ ---


    # --- ★★★ 修正点2: サンプル数が1つのクラスをデータセットから削除 ★★★ ---
    print("サンプル数が1つしかない着順データを削除します...")
    value_counts = df['着順'].value_counts()
    to_remove = value_counts[value_counts < 2].index
    
    rows_before_filter = len(df)
    df = df[~df['着順'].isin(to_remove)]
    rows_after_filter = len(df)
    print(f"少数クラスのフィルタリング完了。{rows_before_filter - rows_after_filter}件の行を削除しました。")
    # --- ★★★ 修正ここまで ★★★ ---


    # カテゴリ変数を数値に変換
    encoders = {}
    categorical_cols = ['レース名', '天気', '騎手', '馬場']
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encoders[col] = le
            print(f"'{col}'列を数値に変換しました。")

    # 3. 特徴量(X)と目的変数(y)の定義
    print("\n--- 3. 特徴量と目的変数の設定 ---")
    X = df.drop('着順', axis=1)
    y = df['着順']
    print("特徴量(X)と目的変数(y)を設定しました。")
    print(f"最終的な学習データ数: {len(df)}件")

    # 4. 訓練データとテストデータに分割
    print("\n--- 4. データの分割 ---")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"訓練データ: {len(X_train)}件, テストデータ: {len(X_test)}件")

    # 5. ランダムフォレストモデルの学習
    print("\n--- 5. モデルの学習開始 ---")
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
    print("モデルの学習が完了しました。")

    # 6. モデルの評価
    print("\n--- 6. モデルの性能評価 ---")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"テストデータに対する正解率 (Accuracy): {accuracy:.4f}")
    
    print("\n詳細レポート (Classification Report):")
    print(classification_report(y_test, y_pred, zero_division=0))

    print("\n--- 特徴量の重要度 ---")
    feature_importances = pd.Series(model.feature_importances_, index=X.columns)
    print(feature_importances.sort_values(ascending=False))

    # 7. モデルとエンコーダーの保存
    print("\n--- 7. 学習済みモデルとエンコーダーの保存 ---")
    joblib.dump(model, 'random_forest_model.joblib')
    joblib.dump(encoders, 'label_encoders.joblib')
    print("'random_forest_model.joblib' と 'label_encoders.joblib' を保存しました。")


if __name__ == '__main__':
    csv_file_path = 'cleaned_race_data.csv'
    train_horse_racing_model(csv_file_path)