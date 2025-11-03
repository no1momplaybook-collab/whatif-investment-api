from flask import Flask, request, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route("/api/investment")
def investment():
    symbol = request.args.get("symbol", "F").upper()
    start_date = request.args.get("start_date", "2025-06-01")
    investment = float(request.args.get("investment", 100))

    # ---- Force a clean column structure ----
    data = yf.download(
    tickers=symbol,
    start=start_date,
    end=None,
    progress=False,
    auto_adjust=False,
    group_by="ticker",
    threads=False
)
    print("Columns returned from yfinance:", list(data.columns))

    if data.empty:
        return jsonify({"error": f"No data for {symbol}"}), 400

    # If yfinance returns multi-level columns like ('F','Close'), pick second level
    if isinstance(data.columns, pd.MultiIndex):
        try:
            data = data[symbol]        # get just this ticker's sub-frame
        except KeyError:
            data.columns = [c[-1] for c in data.columns.to_flat_index()]

    # Determine which column to use
    price_col = None
    for cand in ["Adj Close", "Close"]:
        if cand in data.columns:
            price_col = cand
            break
    if price_col is None:
        return jsonify({
            "error": f"No Close/Adj Close column. Columns: {list(data.columns)}"
        }), 500

    # Drop NAs and compute
    data = data.dropna(subset=[price_col])
    start_price = float(data[price_col].iloc[0])
    latest_price = float(data[price_col].iloc[-1])

    shares = investment / start_price
    current_value = shares * latest_price
    pct_change = (current_value - investment) / investment * 100

    return jsonify({
        "symbol": symbol,
        "start_date": start_date,
        "investment": investment,
        "start_price": round(start_price, 2),
        "latest_price": round(latest_price, 2),
        "current_value": round(current_value, 2),
        "return_pct": round(pct_change, 2)
    })

if __name__ == "__main__":
    app.run(debug=True)
