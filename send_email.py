import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def load_results():
    with open('results.json', 'r') as f:
        return json.load(f)

def get_recommendation(regime, warning_prob):
    if regime == 'High':
        return "Reduce position size to 25-50% of normal"
    elif regime == 'Normal' and warning_prob > 0.6:
        return "Caution: High volatility likely coming, reduce to 50-75%"
    elif regime == 'Low':
        return "Normal position sizing OK, can use 100-150%"
    return "Normal position sizing OK"

def format_email(data):
    regime_colors = {'Low': '#28a745', 'Normal': '#ffc107', 'High': '#dc3545'}
    regime_color = regime_colors.get(data['regime'], '#6c757d')
    signal_status = 'WARNING' if data['warning_signal'] == 1 else 'CLEAR'
    signal_color = '#dc3545' if data['warning_signal'] == 1 else '#28a745'
    
    html = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #24292e;">
        <div style="border-bottom: 3px solid #0366d6; padding-bottom: 10px; margin-bottom: 20px;">
            <h2 style="margin: 0; color: #24292e;">QQQ Volatility Report</h2>
            <p style="margin: 5px 0 0 0; color: #586069;">{data['date']}</p>
        </div>
        
        <div style="background: #f6f8fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; color: {regime_color};">Current Regime: {data['regime'].upper()}</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 4px 0;">Low Volatility:</td><td style="text-align: right; font-weight: 600;">{data['p_low']:.1%}</td></tr>
                <tr><td style="padding: 4px 0;">Normal Volatility:</td><td style="text-align: right; font-weight: 600;">{data['p_normal']:.1%}</td></tr>
                <tr><td style="padding: 4px 0;">High Volatility:</td><td style="text-align: right; font-weight: 600;">{data['p_high']:.1%}</td></tr>
                <tr><td style="padding: 4px 0;">Days in Regime:</td><td style="text-align: right; font-weight: 600;">{data['days_in_regime']}</td></tr>
            </table>
        </div>
        
        <div style="background: #fff3cd; padding: 15px; border-radius: 6px; border-left: 4px solid {signal_color}; margin-bottom: 20px;">
            <h3 style="margin-top: 0;">Early Warning</h3>
            <p style="margin: 5px 0;">10-Day Forecast: <strong>{data['warning_prob']:.1%}</strong> probability of high volatility</p>
            <p style="margin: 5px 0;">Signal: <strong style="color: {signal_color};">{signal_status}</strong></p>
            <p style="margin: 5px 0;">Risk Level: <strong>{data['risk_level']}</strong></p>
        </div>
        
        <div style="margin-bottom: 20px;">
            <h3>Key Metrics</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 4px 0; border-bottom: 1px solid #e1e4e8;">ATR</td><td style="text-align: right; padding: 4px 0; border-bottom: 1px solid #e1e4e8;">{data['atr_pct']:.2f}%</td></tr>
                <tr><td style="padding: 4px 0; border-bottom: 1px solid #e1e4e8;">Volume Ratio</td><td style="text-align: right; padding: 4px 0; border-bottom: 1px solid #e1e4e8;">{data['volume_ratio']:.2f}x</td></tr>
                <tr><td style="padding: 4px 0; border-bottom: 1px solid #e1e4e8;">Distance from SMA</td><td style="text-align: right; padding: 4px 0; border-bottom: 1px solid #e1e4e8;">{data['distance_sma']:.2f}%</td></tr>
                <tr><td style="padding: 4px 0;">Momentum (10d)</td><td style="text-align: right; padding: 4px 0;">{data['momentum_10']:.2f}%</td></tr>
            </table>
        </div>
        
        <div style="background: #e8f5e9; padding: 15px; border-radius: 6px; border-left: 4px solid #4caf50;">
            <h3 style="margin-top: 0;">Recommendation</h3>
            <p style="margin: 0;">{get_recommendation(data['regime'], data['warning_prob'])}</p>
        </div>
        
        <div style="margin-top: 30px; padding-top: 15px; border-top: 1px solid #e1e4e8; color: #586069; font-size: 12px;">
            Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S ET')}
        </div>
    </body>
    </html>
    """
    return html

def send_email(to_email, subject, html_content):
    from_email = os.environ.get('EMAIL_USER')
    password = os.environ.get('EMAIL_PASSWORD')
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    msg.attach(MIMEText(html_content, 'html'))
    
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(from_email, password)
    server.send_message(msg)
    server.quit()
    
    print(f"Email sent to {to_email}")

def main():
    data = load_results()
    html = format_email(data)
    to_email = os.environ.get('EMAIL_USER')
    subject = f"QQQ Alert: {data['regime']} Regime - {data['risk_level']} Risk"
    send_email(to_email, subject, html)

if __name__ == "__main__":
    main()
