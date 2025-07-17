# 1. Importação de bibliotecas
import backtrader as bt
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 2. Definição dos parâmetros de entrada do usuário
print("--- Configuração do Backtest DCA ---")
ticker = 'BTC-USD'
start_date = input("Digite a data de início (YYYY-MM-DD) [padrão: 2024-01-01]: ") or '2024-01-01'
end_date = input("Digite a data de fim (YYYY-MM-DD) [padrão: 2025-07-16]: ") or '2025-07-16'
price_step = float(input("Digite o espaçamento de preço para DCA em USD (ex: 500): ") or 500)
tax_profit = float(input("Digite o take profit em decimal (ex: 0.05 para 5%): ") or 0.05)
# --- ALTERADO: Parâmetro para valor fixo de compra ---
buy_amount_usd = float(input("Digite o valor fixo por compra em USD (ex: 100): ") or 100)
initial_price = float(input("Digite o preço inicial de referência para DCA em USD (ex: 65000): ") or 65000)
max_levels = int(input("Digite o número máximo de ordens DCA ativas (ex: 50): ") or 50)
initial_capital = float(input("Digite o capital inicial em USD (ex: 10000): ") or 10000)
interval = '1h'

# 3. Coleta e preparação dos dados
print("\n[INFO] Baixando dados históricos...")
try:
    df = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        interval=interval,
        auto_adjust=True
    )
    df.dropna(inplace=True)
    if df.empty:
        raise ValueError("Nenhum dado retornado para o período e ticker especificados.")
    print("[INFO] Dados baixados com sucesso.")
except Exception as e:
    print(f"[ERRO] Falha ao baixar dados: {e}")
    exit()

# Garante que as colunas estão no formato correto
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

# Converte o DataFrame para um feed do Backtrader
data = bt.feeds.PandasData(
    dataname=df,
    open='Open',
    high='High',
    low='Low',
    close='Close',
    volume='Volume',
    openinterest=None
)

# 4. Definição da classe da Estratégia (DcaStrategy)
class DcaStrategy(bt.Strategy):
    """
    Estratégia de DCA com valor de compra fixo em USD
    e take-profit por posição individual.
    """
    # --- ALTERADO: Parâmetros da estratégia para usar valor fixo ---
    params = (
        ('price_step', 500),
        ('tax_profit', 0.05),
        ('buy_amount', 100),  # Valor fixo em USD por compra
        ('initial_price', 65000),
        ('max_levels', 50),
    )

    def __init__(self):
        """Inicializador da estratégia."""
        self.dca_positions = []
        self.trade_log = []
        self.equity_curve = []
        self.buy_count = 0
        self.sell_count = 0

    def next(self):
        """Lógica executada a cada vela."""
        current_price = self.data.close[0]
        dt = self.data.datetime.datetime(0)

        # --- Lógica de Venda (Take-Profit) ---
        for pos in list(self.dca_positions):
            if not pos['sold']:
                tp_price = pos['price'] * (1 + self.p.tax_profit)
                if current_price >= tp_price:
                    self.sell(exectype=bt.Order.Market, size=pos['size'])
                    pos['sold'] = True

        self.dca_positions = [p for p in self.dca_positions if not p['sold']]

        # --- Lógica de Compra (DCA com Valor Fixo) ---
        active_positions_count = len(self.dca_positions)

        if active_positions_count < self.p.max_levels:
            for lvl in range(1, self.p.max_levels + 1):
                level_price = self.p.initial_price - lvl * self.p.price_step
                is_level_free = not any(abs(p['price'] - level_price) < 1e-6 for p in self.dca_positions)

                if current_price <= level_price and is_level_free:
                    # --- ALTERADO: Lógica de cálculo do tamanho e verificação de caixa ---
                    amount_to_spend = self.p.buy_amount
                    
                    # Verifica se há caixa suficiente para a compra de valor fixo
                    if self.broker.get_cash() >= amount_to_spend:
                        # Calcula o tamanho da ordem baseado no valor fixo
                        size_to_buy = amount_to_spend / level_price
                        
                        self.buy(exectype=bt.Order.Market, size=size_to_buy)
                        self.dca_positions.append({'price': level_price, 'size': size_to_buy, 'sold': False})
                        break 
        
        self.equity_curve.append({'datetime': dt, 'equity': self.broker.getvalue()})

    def notify_order(self, order):
        """Registra informações sobre ordens executadas."""
        if order.status == order.Completed:
            side = 'BUY' if order.isbuy() else 'SELL'
            if side == 'BUY':
                self.buy_count += 1
            else:
                self.sell_count += 1
            
            self.trade_log.append({
                'dt': self.data.datetime.datetime(0),
                'type': side,
                'price': order.executed.price,
                'size': order.executed.size
            })

    def stop(self):
        """Executado ao final do backtest para exibir os resultados."""
        if not self.equity_curve:
            print("\n[AVISO] Nenhuma operação foi realizada. Não há resultados para exibir.")
            return

        initial_equity = self.equity_curve[0]['equity']
        final_equity = self.equity_curve[-1]['equity']
        profit = final_equity - initial_equity
        roi = (final_equity / initial_equity - 1) * 100

        max_buy_price = None
        min_buy_price = None
        
        buy_trades = [t for t in self.trade_log if t['type'] == 'BUY']
        
        if buy_trades:
            buy_prices = [t['price'] for t in buy_trades]
            max_buy_price = max(buy_prices)
            min_buy_price = min(buy_prices)

        print("\n" + "="*40)
        print("====== Resumo Final da Estratégia ======")
        print("="*40)
        print(f"Período do Backtest: {start_date} a {end_date}")
        print(f"Capital Inicial: ${initial_capital:,.2f}")
        print(f"Equity Final: ${final_equity:,.2f}")
        print(f"Lucro Total: ${profit:,.2f}")
        print(f"Retorno sobre Investimento (ROI): {roi:.2f}%")
        print("-" * 40)
        print(f"Total de Compras Executadas: {self.buy_count}")
        print(f"Total de Vendas Executadas: {self.sell_count}")
        
        if max_buy_price is not None and min_buy_price is not None:
            print(f"Preço Máximo de Compra: ${max_buy_price:,.2f}")
            print(f"Preço Mínimo de Compra: ${min_buy_price:,.2f}")
        else:
            print("Nenhuma ordem de compra foi executada.")
        print("="*40)


# 5. Configuração e execução do Cerebro
min_buy_price_param = initial_price - (max_levels * price_step)
print("\n" + "="*40)
print("--- Parâmetros da Estratégia Definidos ---")
# --- ALTERADO: Exibir o valor fixo nos parâmetros ---
print(f"Valor Fixo por Compra: ${buy_amount_usd:,.2f}")
print(f"Preço inicial de referência: ${initial_price:,.2f}")
print(f"Preço mínimo de compra (calculado): ${min_buy_price_param:,.2f}")
print(f"Máximo de ordens DCA: {max_levels}")
print(f"Espaçamento entre as ordens: ${price_step:,.2f}")
print("="*40)

cerebro = bt.Cerebro()
cerebro.addstrategy(
    DcaStrategy,
    price_step=price_step,
    tax_profit=tax_profit,
    buy_amount=buy_amount_usd, # --- ALTERADO: Passar o novo parâmetro ---
    initial_price=initial_price,
    max_levels=max_levels
)
cerebro.adddata(data)
cerebro.broker.setcash(initial_capital)

print("\n[INFO] Executando o backtest...")
results = cerebro.run()
print("[INFO] Backtest concluído.")

# 6. Análise e plotagem dos resultados
strat = results[0]
trades_df = pd.DataFrame(strat.trade_log)
equity_df = pd.DataFrame(strat.equity_curve).set_index('datetime')

# Gráfico 1: Curva de Equity
plt.style.use('seaborn-v0_8-darkgrid')
plt.figure(figsize=(12, 6))
plt.plot(equity_df.index, equity_df['equity'], label='Curva de Equity', color='royalblue')
plt.title('Evolução do Equity da Carteira', fontsize=16)
plt.ylabel('Valor da Carteira (USD)', fontsize=12)
plt.xlabel('Data', fontsize=12)
plt.legend()
plt.tight_layout()
plt.show()

# Gráfico 2: Preço e Operações
plt.figure(figsize=(12, 8))
plt.plot(df.index, df['Close'], label='Preço BTC-USD', color='gray', alpha=0.7)

if not trades_df.empty:
    buys = trades_df[trades_df['type'] == 'BUY']
    sells = trades_df[trades_df['type'] == 'SELL']
    
    plt.scatter(buys['dt'], buys['price'], marker='^', color='green', s=50, label='Compras', zorder=5)
    plt.scatter(sells['dt'], sells['price'], marker='v', color='red', s=50, label='Vendas', zorder=5)

plt.title('Preço do Ativo e Operações de Compra/Venda', fontsize=16)
plt.ylabel('Preço (USD)', fontsize=12)
plt.xlabel('Data', fontsize=12)
plt.legend()
plt.tight_layout()
plt.show()