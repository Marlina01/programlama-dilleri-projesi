# model_egit.py
# fetal_health.csv dosyasından veriyi okuyacak, bir RandomForest modeli eğitecek
# ve modeli "tahmin_model.pkl" adıyla kaydedecek.
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (classification_report,
                             confusion_matrix)
from sklearn.inspection import permutation_importance
import joblib

def model_egit():
    # Veriyi oku
    veri = pd.read_csv("fetal_health.csv", encoding="utf-8")

    # Özellikler (X) ve hedef (y)
    hedef_etiket = "fetal_health"
    X = veri.drop(columns=[hedef_etiket])
    y = veri[hedef_etiket]

    # Eğitim / test ayır
    X_egitim, X_test, y_egitim, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # RandomForest modelini oluştur
    model = RandomForestClassifier(
        n_estimators=500,       # ağaç sayısını artırdık
        max_depth=15,          # aşırı dalmayı engelledik
        class_weight="balanced",  # sınıf dengesini sağladık
        random_state=42,
        n_jobs=-1
    )
    

    # Modeli eğit
    model.fit(X_egitim, y_egitim)

    # Test seti üzerinde rapor
    y_tahmin = model.predict(X_test)
    print("Sınıflandırma Raporu:")
    print(classification_report(y_test, y_tahmin))

    # Modeli kaydet
    joblib.dump(model, "tahmin_model.pkl")
    print("Model tahmin_model.pkl dosyasına kaydedildi.")


# --- 7) Feature Importance ---
    onem = model.feature_importances_
    isimler = X.columns

    importance_df = pd.DataFrame({
        "Ozellik": isimler,
        "Onem": onem
    }).sort_values(by="Onem", ascending=False)


    plt.figure(figsize=(10, 6))
    sns.barplot(data=importance_df, x="Onem", y="Ozellik", palette="viridis")
    plt.title("Feature Importance", fontsize=14)
    plt.tight_layout()
    plt.show()

    # --- 8) Permutation Importance ---
    perm = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42)
    perm_df = pd.DataFrame({
        "Ozellik": isimler,
        "PI": perm.importances_mean
    }).sort_values(by="PI", ascending=False)

    plt.figure(figsize=(10, 6))
    sns.barplot(data=perm_df.head(15), x="PI", y="Ozellik", palette="magma")
    plt.title("Permutation Importance (İlk 15)", fontsize=14)
    plt.tight_layout()
    plt.show()

    # --- 9) Probability Heatmap ---
    olasilik = model.predict_proba(X_test)
    heat = np.mean(olasilik, axis=0).reshape(1, -1)

    plt.figure(figsize=(6, 2))
    sns.heatmap(heat, annot=True, cmap="coolwarm", xticklabels=["Normal (1)", "Şüpheli (2)", "Patolojik (3)"])
    plt.title("Test Seti Ortalama Olasılık Heatmap")
    plt.yticks([])
    plt.tight_layout()
    plt.show()




if __name__ == "__main__":
    model_egit()
