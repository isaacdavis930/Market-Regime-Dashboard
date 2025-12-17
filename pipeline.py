import yfinance as yf
import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

TICKER = "QQQ"
LOOKBACK_YEARS = 10
ATR_WINDOW = 14
FORECAST_HORIZON = 10

def fetch_data():
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=LOOKBACK_YEARS*365)).strftime('%Y-%m-%d')
    df = yf.download(TICKER, start=start_date, end=end_date, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df

def calculate_atr(df):
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    df['ATR'] = df['TR'].rolling(window=ATR_WINDOW).mean()
    df['ATR_pct'] = (df['ATR'] / df['Close']) * 100
    df = df.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1)
    return df.dropna()

def engineer_features(df):
    df['SMA_10'] = df['Close'].rolling(10).mean()
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['Distance_from_SMA_20'] = ((df['Close'] - df['SMA_20']) / df['SMA_20']) * 100
    df['SMA_20_Slope'] = ((df['SMA_20'] - df['SMA_20'].shift(5)) / df['SMA_20'].shift(5)) * 100
    
    df['High_20'] = df['High'].rolling(20).max()
    df['Low_20'] = df['Low'].rolling(20).min()
    df['Channel_Position'] = ((df['Close'] - df['Low_20']) / (df['High_20'] - df['Low_20']) * 100)
    df['High_252'] = df['High'].rolling(252).max()
    df['Distance_from_High'] = ((df['Close'] - df['High_252']) / df['High_252']) * 100
    
    df['BB_Mid'] = df['Close'].rolling(20).mean()
    df['BB_Std'] = df['Close'].rolling(20).std()
    df['BB_Width'] = (4 * df['BB_Std'] / df['BB_Mid']) * 100
    
    df['ATR_Percentile_20'] = df['ATR_pct'].rolling(20).apply(
        lambda x: (x.rank(pct=True).iloc[-1] * 100) if len(x) > 0 else np.nan
    )
    df['ATR_Percentile_50'] = df['ATR_pct'].rolling(50).apply(
        lambda x: (x.rank(pct=True).iloc[-1] * 100) if len(x) > 0 else np.nan
    )
    
    df['Range_pct'] = ((df['High'] - df['Low']) / df['Close']) * 100
    df['Avg_Range_10'] = df['Range_pct'].rolling(10).mean()
    df['Avg_Range_50'] = df['Range_pct'].rolling(50).mean()
    df['Range_Contraction'] = (df['Avg_Range_10'] / df['Avg_Range_50']) * 100
    
    df['Vol_MA_20'] = df['Volume'].rolling(20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Vol_MA_20']
    df['Vol_Std_20'] = df['Volume'].rolling(20).std()
    df['Volume_ZScore'] = (df['Volume'] - df['Vol_MA_20']) / df['Vol_Std_20']
    df['Dollar_Vol'] = df['Close'] * df['Volume']
    df['Dollar_Vol_MA'] = df['Dollar_Vol'].rolling(20).mean()
    df['Dollar_Volume_Ratio'] = df['Dollar_Vol'] / df['Dollar_Vol_MA']
    
    df['Peak_20'] = df['Close'].rolling(20).max()
    df['Drawdown_20'] = ((df['Close'] - df['Peak_20']) / df['Peak_20']) * 100
    df['Momentum_10'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
    df['Momentum_20'] = ((df['Close'] - df['Close'].shift(20)) / df['Close'].shift(20)) * 100
    
    df = df.drop(['SMA_10', 'SMA_50', 'High_20', 'Low_20', 'High_252', 
                  'BB_Mid', 'BB_Std', 'Range_pct', 'Avg_Range_10', 'Avg_Range_50',
                  'Vol_MA_20', 'Vol_Std_20', 'Dollar_Vol', 'Dollar_Vol_MA', 'Peak_20'], axis=1)
    
    return df.dropna()

def add_regime_probabilities(df, hmm_data):
    X_hmm = df['ATR_pct'].values.reshape(-1, 1)
    probabilities = hmm_data['model'].predict_proba(X_hmm)
    state_order = hmm_data['state_order']
    state_mapping = hmm_data['state_mapping']
    
    df['P_Low'] = probabilities[:, state_order[0]]
    df['P_Normal'] = probabilities[:, state_order[1]]
    df['P_High'] = probabilities[:, state_order[2]]
    
    regime_labels = [state_mapping[np.argmax(probabilities[i])] for i in range(len(probabilities))]
    df['Regime'] = regime_labels
    
    df['Days_in_Regime'] = 0
    current_regime = None
    days_count = 0
    for i in range(len(df)):
        regime = df.iloc[i]['Regime']
        if regime == current_regime:
            days_count += 1
        else:
            days_count = 1
            current_regime = regime
        df.iloc[i, df.columns.get_loc('Days_in_Regime')] = days_count
    
    df['P_High_MA_5'] = df['P_High'].rolling(5).mean()
    df['P_High_Trend'] = df['P_High_MA_5'].diff(5)
    
    return df.dropna()

def generate_prediction(latest_data, ml_data):
    feature_cols = ml_data['feature_cols']
    features = latest_data[feature_cols].values.reshape(1, -1)
    features_scaled = ml_data['scaler'].transform(features)
    
    warning_prob = ml_data['model'].predict_proba(features_scaled)[0, 1]
    warning_signal = 1 if warning_prob > 0.5 else 0
    
    if warning_prob < 0.3:
        risk_level = "Low"
    elif warning_prob < 0.6:
        risk_level = "Medium"
    else:
        risk_level = "High"
    
    return {
        'date': latest_data.name.strftime('%Y-%m-%d'),
        'regime': latest_data['Regime'],
        'p_low': float(latest_data['P_Low']),
        'p_normal': float(latest_data['P_Normal']),
        'p_high': float(latest_data['P_High']),
        'days_in_regime': int(latest_data['Days_in_Regime']),
        'atr_pct': float(latest_data['ATR_pct']),
        'warning_prob': float(warning_prob),
        'warning_signal': int(warning_signal),
        'risk_level': risk_level,
        'volume_ratio': float(latest_data['Volume_Ratio']),
        'distance_sma': float(latest_data['Distance_from_SMA_20']),
        'momentum_10': float(latest_data['Momentum_10']),
        'close': float(latest_data['Close'])
    }

def main():
    print(f"Running QQQ volatility analysis for {datetime.now().strftime('%Y-%m-%d')}")
    
    with open('hmm_model.pkl', 'rb') as f:
        hmm_data = pickle.load(f)
    
    with open('ml_model.pkl', 'rb') as f:
        ml_data = pickle.load(f)
    
    df = fetch_data()
    df = calculate_atr(df)
    df = engineer_features(df)
    df = add_regime_probabilities(df, hmm_data)
    
    latest = df.iloc[-1]
    prediction = generate_prediction(latest, ml_data)
    
    with open('results.json', 'w') as f:
        json.dump(prediction, f, indent=2)
    
    print(f"Analysis complete. Regime: {prediction['regime']}, Risk: {prediction['risk_level']}")
    return prediction

if __name__ == "__main__":
    main()