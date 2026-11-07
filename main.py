<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CS2 Winter Drop Hub</title>
    <!-- Підключаємо Telegram Web App JS SDK -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent: #38bdf8;
            --text-color: #f8fafc;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        h1 {
            font-size: 22px;
            margin-bottom: 8px;
            text-align: center;
        }
        .balance-card {
            background: var(--card-bg);
            padding: 12px 24px;
            border-radius: 12px;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            border: 1px solid #334155;
        }
        .cases-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
            width: 100%;
            max-width: 400px;
        }
        .case-card {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 16px;
            text-align: center;
            border: 1px solid #334155;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        }
        .case-title {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        .case-price {
            color: #38bdf8;
            margin-bottom: 12px;
            font-size: 14px;
        }
        .btn {
            background-color: var(--accent);
            color: #0f172a;
            border: none;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            transition: 0.2s;
        }
        .btn:active {
            transform: scale(0.96);
            background-color: #0ea5e9;
        }
    </style>
</head>
<body>

    <h1>❄️ CS2 Winter Hub Mini App</h1>
    <div class="balance-card">Баланс: <span id="user-balance">2000</span> 🪙</div>

    <div class="cases-grid">
        <div class="case-card">
            <div class="case-title">❄️ Новорічний Кеш із Ножами</div>
            <div class="case-price">Ціна: 600 🪙</div>
            <button class="btn" onclick="openCase('winter_knife_case', 600)">Відкрити кейс</button>
        </div>
        <div class="case-card">
            <div class="case-title">🎄 Святковий Оружейний Кейс</div>
            <div class="case-price">Ціна: 200 🪙</div>
            <button class="btn" onclick="openCase('new_year_weapon_case', 200)">Відкрити кейс</button>
        </div>
    </div>

    <script>
        // Ініціалізація Telegram Web App
        let tg = window.Telegram.WebApp;
        tg.expand(); // Розгортаємо на весь екран

        function openCase(caseId, price) {
            let currentBalance = parseInt(document.getElementById('user-balance').innerText);
            if (currentBalance < price) {
                tg.showAlert("❌ Недостатньо монет на балансі!");
                return;
            }
            currentBalance -= price;
            document.getElementById('user-balance').innerText = currentBalance;
            tg.showAlert(`🎉 Ви успішно відкрили кейс та вибили крутий скін!`);
        }
    </script>
</body>
</html>
