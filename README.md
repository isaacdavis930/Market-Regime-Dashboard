# QQQ Volatility Regime Detection & Automated Trading Alerts

  This is an automated system that monitors QQQ volatility regimes using Hidden Markov Models and machine learning. Every trading day at 4:30 PM ET, it analyzes market data, detects the current volatility regime, forecasts potential regime shifts, and emails you a formatted report with position sizing recommendations.

The system employs a two-model approach:

**Hidden Markov Model** - Identifies three distinct volatility regimes (Low, Normal, High) based on ATR patterns  
**Logistic Regression** - Predicts probability of high volatility in the next 10 trading days using 18 technical features  



**Performance Metrics:**
- Test Accuracy: 90.7%
- AUC Score: 0.944
- Precision: 87.8% | Recall: 79.3%
- Training Data: 2,485 days (2015-2025)



Note: This system does not execute any trades automatically.

---

## Disclaimer

This project is for educational and research purposes only.

- Not intended for real trading or investment
- No investment advice or guarantees provided
- Creator assumes no liability for financial losses
- Consult a financial advisor for investment decisions
- Past performance does not indicate future results

By using this software, you agree to use it solely for learning and research purposes.

---

## Table of Contents

- How It Works
- Model Performance
- How to Install
- How to Run
- Repository Structure
- Customization
- Tech Stack


---

## How It Works

###  Volatility Regime Detection (HMM)

The system uses a 3-state Gaussian Hidden Markov Model trained on ATR% to identify distinct market regimes:

- **Low Volatility:** ATR ~0.93% (mean), 97.8% persistence  
- **Normal Volatility:** ATR ~1.47% (mean), 95.3% persistence  
- **High Volatility:** ATR ~2.63% (mean), 98.2% persistence  

Key insight: Regimes cannot jump directly from Low to High. They must transition through Normal, which matches real market behavior and provides early warning signals.

###  Early Warning System (ML)

A logistic regression model predicts whether high volatility will occur within 10 days using 18 engineered features:

**Feature Categories:**
- **Compression Metrics:** Bollinger Band width, ATR percentiles, range contraction
- **Trend Indicators:** SMA distance, slope, channel position, distance from 52-week high
- **Volume Signals:** Volume ratio, z-score, dollar volume ratio
- **Price Action:** 20-day drawdown, 10-day and 20-day momentum
- **Regime Features:** Days in current regime, 5-day probability trends

The model outputs a probability score (0-100%) that maps to risk levels:
- Low Risk: <30% probability → Normal position sizing OK (100-150%)
- Medium Risk: 30-60% probability → Reduce to 50-75%
- High Risk: >60% probability → Reduce to 25-50%

###  Automation Pipeline

```
GitHub Actions (4:30 PM ET, Mon-Fri)
        ↓
Download QQQ data → yfinance API
        ↓
Calculate 18 technical features
        ↓
Load pre-trained models (HMM + Logistic Regression)
        ↓
Generate predictions → Current regime + 10-day forecast
        ↓
Format HTML email report
        ↓
Send via Gmail SMTP → Inbox
```

---

## Model Performance

### Test Set Results

Trained on 1,988 days, tested on 497 days (80/20 split)

**Classification Metrics:**
- Accuracy: 90.7%
- AUC: 0.944
- Precision: 87.8%
- Recall: 79.3%
- F1 Score: 0.833

**Confusion Matrix:**
- True Positives: 115 (correctly predicted high-vol episodes)
- False Positives: 16 (false alarms - 3.6% of predictions)
- False Negatives: 30 (missed warnings - 20.7% of actual events)
- True Negatives: 334 (correctly identified calm periods)

**What this means:**  
The system catches nearly 80% of high-volatility episodes while maintaining 88% precision. For every 100 warnings, 88 are correct. This balance makes it practical for real-world risk management.

---

## How to Install

### 1. Clone the Repository

```bash
git clone https://github.com/isaacdavis930/Market-Regime-Dashboard.git
cd Market-Regime-Dashboard
```

### 2. Set up Gmail App Password

The system sends email alerts via Gmail. You'll need to generate an App Password:

1. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
2. Create a new app password (name it "QQQ Alerts")
3. Copy the 16-character password (remove spaces)

**Important:** Do NOT use your regular Gmail password. Gmail requires App Passwords for third-party applications.

### 3. Configure GitHub Secrets

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret" and add:

**EMAIL_USER**
- Value: Your Gmail address (e.g., your-email@gmail.com)

**EMAIL_PASSWORD**  
- Value: Your 16-character App Password (no spaces)

These secrets are encrypted and never exposed in logs.

---

## How to Run

###  Automated Daily Execution

Once installed, the system runs automatically:

- **Schedule:** Monday-Friday at 4:30 PM ET (after market close)
- **Duration:** ~45 seconds per run
- **Cost:** $0.00 (GitHub free tier: 2,000 minutes/month)

**To verify it's working:**
1. Go to your repository → Actions tab
2. You should see a green checkmark for successful runs
3. Check your email for the daily report

###  Manual Test Run

To test the system immediately:

1. Go to your repository → Actions tab
2. Click "Daily QQQ Volatility Update" in the left sidebar
3. Click "Run workflow" → "Run workflow" (green button)
4. Wait ~45 seconds
5. Check your email inbox

**Example Email Output:**

The system sends a formatted HTML email containing:
- Current volatility regime (Low/Normal/High)
- Regime probabilities with confidence levels
- Early warning signal (10-day forecast)
- Risk level assessment
- Key technical metrics (ATR, volume, momentum, SMA distance)
- Position sizing recommendation

---

## Repository Structure

```
├── pipeline.py              # Main analysis script (data fetch → predictions)
├── send_email.py            # Email formatting and SMTP delivery
├── hmm_model.pkl            # Pre-trained 3-state Hidden Markov Model
├── ml_model.pkl             # Pre-trained Logistic Regression + StandardScaler
├── requirements.txt         # Python dependencies (yfinance, sklearn, hmmlearn)
├── README.md                # This file
└── .github/
    └── workflows/
        └── daily-update.yml # GitHub Actions automation config (cron schedule)
```

---

## Customization

### Change Alert Schedule

Edit `.github/workflows/daily-update.yml`:

```yaml
schedule:
  - cron: '30 21 * * 1-5'  # 4:30 PM ET, Monday-Friday
```

Cron format: `minute hour day month weekday`

**Examples:**
- `0 14 * * 1-5` → 9:00 AM ET (pre-market)
- `0 22 * * 1-5` → 5:00 PM ET (after-hours)

### Modify Risk Thresholds

Edit the `get_recommendation()` function in `send_email.py`:

```python
def get_recommendation(regime, warning_prob):
    if regime == 'High':
        return "Reduce position size to 25-50% of normal"
    elif regime == 'Normal' and warning_prob > 0.6:
        return "Caution: High volatility likely coming, reduce to 50-75%"
    elif regime == 'Low':
        return "Normal position sizing OK, can use 100-150%"
    return "Normal position sizing OK"
```

Adjust the `warning_prob` threshold (currently 0.6) to make warnings more/less sensitive.

### Add New Features

Extend the `engineer_features()` function in `pipeline.py`:

```python
# Example: Add RSI indicator
df['RSI'] = calculate_rsi(df['Close'], periods=14)

# Example: Add MACD
df['MACD'] = calculate_macd(df['Close'])
```

Note: Adding new features requires retraining the ML model.

---

## Tech Stack

### Core Technologies

- **Python 3.10**
- **scikit-learn** - Logistic Regression, StandardScaler, model evaluation
- **hmmlearn** - Gaussian Hidden Markov Models
- **yfinance** - Real-time market data from Yahoo Finance
- **pandas/numpy** - Data processing and numerical computation

### Infrastructure

- **GitHub Actions** - Workflow automation and scheduling
- **Gmail SMTP** - Email delivery (smtp.gmail.com:465)
- **GitHub Secrets** - Encrypted credential storage

### Key Design Decisions

**Why HMM?**  
Hidden Markov Models naturally capture regime persistence and transition probabilities. Volatility regimes exhibit strong auto-correlation, making HMM an ideal choice over threshold-based methods.

**Why Logistic Regression?**  
Simple, interpretable, and effective for binary classification. The model's coefficients reveal which features drive volatility predictions, unlike black-box methods.

**Why GitHub Actions?**  
No server costs, built-in scheduling, secure secrets management, and 2,000 free minutes/month (only uses 150/month).

---

## Skills Demonstrated

**Machine Learning:**
- Hidden Markov Models for time series regime detection
- Feature engineering from financial data
- Handling class imbalance with balanced weights
- Model evaluation (ROC-AUC, precision-recall tradeoffs)
- Time-based train/test splits (avoiding lookahead bias)

**Software Engineering:**
- Production ML pipeline design
- Automated workflow orchestration (CI/CD)
- Secure credential management
- Error handling and logging
- Clean, modular code architecture

**Financial Analysis:**
- Volatility modeling and regime detection
- Technical indicator calculation (ATR, Bollinger Bands, momentum)
- Risk management frameworks
- Position sizing strategies

**DevOps & Infrastructure:**
- GitHub Actions automation
- RESTful API integration
- Cloud compute optimization
- Version control best practices

---




---

## Contact

**Isaac Davis**  
[LinkedIn](www.linkedin.com/in/
) | [Portfolio](#) | [GitHub](https://github.com/isaacdavis930)



---

**Note:** Replace placeholder links and add actual screenshots before publishing!
