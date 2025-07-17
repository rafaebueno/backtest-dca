
# Backtest para DCA em Bitcoin
Projeto elaborado para estudar novas estratégias compostas do DCA para um operacional de compra e venda de BITCOIN BTC.

# Por que eu desenvolvi meu próprio?
Hoje, eu opero futuros alavancado usando um bot próprio de DCA, fazendo preço-médio e entregando a posição com um takeprofit lucrativo. 

Eu desenvolvi o algoritmo para o meu propósito. Calculadoras de DCA são fáceis de encontrar na internet, porém um backtest em simulação real, não.

# Como funciona?
O algoritmo roda em python, fazendo uma requisição puxando pela api do YahooFinance o gráfico do BTC-USD, foi usado diversos modulos importados para fazer as requisições e complementações.

Scrape do preço do bitcoin em um espaço de tempo definido pelo usuário, ele faz a simulação seguindo os seus parâmetros inputados pelo usuário. Relevando situações externas, somente levando em consideração o preço do BTC.

Faz as análises considerando candles de 1H do gráfico, você pode alterar o timeframe para análise para visualizar a performance em mercado de queda, subida ou lateralização. Assim defininindo qual estratégia é a melhor para seu caso.






## Funcionalidades

- Scrape do preço em tempo real do BTCUSD via Yahoo Finance.
- Parâmetros do backtest todos alteráveis pelo usuário.
- Gráfico visual mostrando a evolução do Patrimônio Líquido.
- Gráfico visual mostrando o operacional, faixas de compras e venda.
- Relatório completo dos trades.


## Screenshots exemplos práticos do BackTest
Parâmetros

![Parâmetros](https://i.ibb.co/xqwzH86T/parametros.png)

Resumo Final

![ResumoFinal](https://i.ibb.co/4ZCm131Z/resumo-final.png)

Equity Operação
![Equity](https://i.ibb.co/mFYk9M9z/equity.png)

Relatório Gráfico de Operações
![Operacoes](https://i.ibb.co/ZR1rVvJ8/operacoes.png)



## Instalação 

Clone meu repositório

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

Instale todas as dependências, execute no terminal da pasta
```bash
pip install -r requirements.txt
```
Se este comando não estiver funcionando:
```bash
py -m pip install -r requirements.txt
```

Para rodar, você deve executar no terminal
```bash
py backtest_dca.py
```