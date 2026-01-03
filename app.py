from utils.data_loader import get_data
from utils.forecaster import forecast_and_advice
from utils.telegram import send_telegram_message_with_photo
import matplotlib
matplotlib.use('Agg')  # Disattiva GUI
import matplotlib.pyplot as plt

BOT_TOKEN = ""
CHAT_ID = ""

def plot_forecast(forecast_df):
    plt.figure(figsize=(10,6))
    plt.plot(forecast_df['ds'], forecast_df['yhat'], label='Previsione')

    # Se yhat_lower e yhat_upper esistono, li uso per il fill_between
    if 'yhat_lower' in forecast_df.columns and 'yhat_upper' in forecast_df.columns:
        plt.fill_between(forecast_df['ds'], forecast_df['yhat_lower'], forecast_df['yhat_upper'], color='gray', alpha=0.2, label='Intervallo di confidenza')

    plt.xlabel('Data')
    plt.ylabel('Prezzo (€)')
    plt.title('Previsioni del prezzo')
    plt.legend()
    plt.savefig("forecast.png")
    plt.close()


def check_anomalies(forecast_df):
    anomalies = forecast_df[forecast_df['yhat'] < 0]
    if not anomalies.empty:
        print("Attenzione: previsione con valori negativi trovati!")
        print(anomalies)
    else:
        print("Nessuna anomalia rilevata nelle previsioni.")

def find_best_buy_sell_days(forecast_df):
    period_df = forecast_df.head(30)
    best_buy = period_df.loc[period_df['yhat'].idxmin()]
    sell_candidates = period_df[period_df['ds'] > best_buy['ds']]
    if not sell_candidates.empty:
        best_sell = sell_candidates.loc[sell_candidates['yhat'].idxmax()]
    else:
        best_sell = None
    return best_buy, best_sell

def send_alert_if_needed(forecast_df, threshold=300):
    if (forecast_df['yhat'] > threshold).any():
        message = f"⚠️ ALERT: previsione sopra soglia {threshold}€ rilevata!"
        send_telegram_message_with_photo(message)
        print("Alert Telegram inviato.")
    else:
        print("Nessun alert da inviare.")

def main():
    print("Inizio esecuzione")
    asset = "AAPL"
    data = get_data(asset)
    print("Dati caricati:")
    print(data.head())

    forecast_result, trading_advice = forecast_and_advice(data)
    print("Previsioni:")
    print(forecast_result.tail())

    check_anomalies(forecast_result)
    send_alert_if_needed(forecast_result)
    
    best_buy, best_sell = find_best_buy_sell_days(forecast_result)

    # Costruzione messaggio testo per Telegram (ultimi 5 giorni)
    message = f"📈 Previsioni prossimi 5 giorni per {asset} (in €):\n"
    for index, row in forecast_result.head(5).iterrows():
        data_str = row['ds'].strftime('%Y-%m-%d')
        prezzo = round(row['yhat'], 2)
        message += f"{data_str}: €{prezzo}\n"

    message += "\n💡 Consigli di trading:\n"
    message += f"Compra il {best_buy['ds'].strftime('%Y-%m-%d')} a circa €{round(best_buy['yhat'], 2)}\n"
    if best_sell is not None:
        message += f"Vendi il {best_sell['ds'].strftime('%Y-%m-%d')} a circa €{round(best_sell['yhat'], 2)}\n"
    else:
        message += "Nessun giorno di vendita consigliato dopo l'acquisto previsto.\n"

    print(message)

    plot_forecast(forecast_result)

    # Invio messaggio + foto tramite Telegram
    photo_path = "forecast.png"
    send_telegram_message_with_photo(BOT_TOKEN, CHAT_ID, forecast_result, {"buy": best_buy, "sell": best_sell}, photo_path)

if __name__ == "__main__":
    main()

