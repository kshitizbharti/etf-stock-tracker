import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
import re
import yfinance as yf

logger = logging.getLogger(__name__)

class ETFScraper:
    """Scraper to fetch ETF data from multiple sources"""
    
    def __init__(self):
        self.upstox_url = "https://upstox.com/etfs/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # Comprehensive NSE ETF symbols list (100+ ETFs)
        # Using Yahoo Finance .NS suffix for NSE
        self.nse_etf_symbols = [
            # === NIFTY 50 INDEX ETFs ===
            'NIFTYBEES.NS', 'SETFNIF50.NS', 'NIFTYETF.NS', 'NETF.NS',
            'HDFCNIF50.NS', 'ICICIM150.NS', 'ICICIBANKETF.NS',
            
            # === BANK SECTOR ETFs ===
            'BANKBEES.NS', 'SETFNIFBK.NS', 'PSUBNKBEES.NS', 'NPBET.NS',
            'EDELBANKETF.NS', 'LICNETFBAN.NS', 'SBIETFBANK.NS',
            
            # === NEXT 50 & MID/SMALL CAP ===
            'JUNIORBEES.NS', 'NV20BEES.NS', 'MID150BEES.NS', 'MIDCAPETF.NS',
            'LICNMFET.NS', 'SBIETFMID.NS',
            
            # === SECTOR ETFs ===
            'ITBEES.NS', 'INFRABEES.NS', 'CONSUMBEES.NS', 'PHARMABEES.NS',
            'AUTOBEES.NS', 'ENERGYBEES.NS', 'FMCGBEES.NS', 'REALTYBEES.NS',
            'LICNETFIT.NS', 'SBIETFIT.NS', 'SBIETFPHAR.NS', 'SBIETFCON.NS',
            
            # === STRATEGY/THEMATIC ETFs ===
            'MOM30IETF.NS', 'DIVOPPBEES.NS', 'LOWVOLIETF.NS', 'QUAL30IETF.NS',
            'EQUAL50BES.NS', 'ALPHAETF.NS', 'VALUEIETF.NS', 'GROWTHIETF.NS',
            'ESG.NS', 'LICNETFGSC.NS', 'LICNETFSEN.NS',
            
            # === CPSE & PSU ===
            'CPSEETF.NS', 'CPSEBANKETF.NS', 'SETFPSUBK.NS',
            
            # === GLOBAL/INTERNATIONAL ===
            'HNGSNGBEES.NS', 'MASPTOP50.NS', 'MON100.NS', 'MOSESETFs.NS',
            'LIQUIDCASE.NS', 'LICNETFN50.NS',
            
            # === COMMODITY ETFs (GOLD/SILVER) ===
            'GOLDBEES.NS', 'SETFGOLD.NS', 'GOLDSHARE.NS', 'KOTAKGOLD.NS',
            'HDFCGOLD.NS', 'GOLDIETF.NS', 'AXISGOLD.NS', 'SBIGOLD.NS',
            'SILVERBEES.NS', 'SILVER.NS', 'SILVERETF.NS',
            
            # === DEBT/BOND ETFs ===
            'LIQUIDBEES.NS', 'LIQUIDETF.NS', 'SETFLIQ.NS', 
            'GILTETF.NS', 'SETFNN50.NS', 'EBBETF0423.NS', 'EBBETF0425.NS',
            'EBBETF0430.NS', 'EBBETF0432.NS',
            
            # === DIVIDEND/VALUE ETFs ===
            'DIVOPPBEES.NS', 'LICNETFGSC.NS', 'LICNETFSEN.NS',
            
            # === ADDITIONAL POPULAR ETFs ===
            'MNC.NS', 'ITETF.NS', 'DEFENCEETF.NS', 'HEALTHIETF.NS',
            'MANUFACTURING.NS', 'INFRAIETF.NS', 'AUTOIETF.NS',
            'SETFNEXT50.NS', 'LICNFNHGP.NS',
            
            # === SMART BETA ETFs ===
            'SMARTETF.NS', 'FACTORIETF.NS', 'MOMENTUMETF.NS',
            
            # === RECENTLY LISTED ===
            'SBIETFQLTY.NS', 'SBIETFMOM.NS', 'SBIETFALPH.NS',
            'LICMFETF.NS', 'HDFCMOMENT.NS', 'HDFCLOWVOL.NS'
        ]
    
    def fetch_etf_data(self) -> List[Dict[str, any]]:
        """Fetch NSE ETF data using yfinance for reliable price data
        
        Returns:
            List of dicts with keys: name, symbol, price, change_percent
        """
        try:
            logger.info("Fetching ETF data from Yahoo Finance")
            etf_data = []
            
            for symbol in self.nse_etf_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    hist = ticker.history(period='2d')
                    
                    if hist.empty or len(hist) < 2:
                        logger.debug(f"No price data for {symbol}")
                        continue
                    
                    current_price = hist['Close'].iloc[-1]
                    previous_close = hist['Close'].iloc[-2]
                    change_percent = ((current_price - previous_close) / previous_close) * 100
                    
                    etf_name = info.get('longName', symbol.replace('.NS', ''))
                    
                    etf_data.append({
                        'name': etf_name,
                        'symbol': symbol,
                        'price': float(current_price),
                        'change_percent': float(change_percent)
                    })
                    logger.debug(f"{etf_name}: {change_percent:.2f}%")
                    
                except Exception as e:
                    logger.debug(f"Error fetching {symbol}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(etf_data)} ETFs")
            return etf_data
            
        except Exception as e:
            logger.error(f"Error fetching ETF data: {e}")
            return []
    
    def fetch_etf_data_from_upstox(self) -> List[Dict[str, any]]:
        """Fallback method: Scrape ETF data from upstox.com/etfs
        
        Returns:
            List of dicts with keys: name, price, change_percent
        """
        try:
            logger.info(f"Fetching ETF data from {self.upstox_url}")
            response = requests.get(self.upstox_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            etf_data = []
            
            # Find tbody and iterate through rows
            tbody = soup.find('tbody')
            if not tbody:
                logger.warning("No tbody found in HTML")
                return []
            
            rows = tbody.find_all('tr')
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 5:
                        continue
                    
                    # Column 0: ETF Name
                    name_cell = cells[0]
                    name_text = name_cell.get_text(strip=True)
                    
                    # Column 3: Market Price
                    price_text = cells[3].get_text(strip=True)
                    price_match = re.search(r'[₹]?([\d,]+\.?\d*)', price_text)
                    price = float(price_match.group(1).replace(',', '')) if price_match else None
                    
                    # Column 4: 1D Change (%)
                    change_cell = cells[4]
                    change_text = change_cell.get_text(strip=True)
                    change_match = re.search(r'([+-]?\d+\.?\d*)', change_text)
                    
                    if change_match:
                        change_percent = float(change_match.group(1))
                        # If the cell has class 'text-table-negative', make it negative
                        if 'text-table-negative' in str(change_cell):
                            change_percent = -abs(change_percent)
                    else:
                        continue
                    
                    if name_text:
                        etf_data.append({
                            'name': name_text,
                            'price': price,
                            'change_percent': change_percent
                        })
                        
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(etf_data)} ETFs from Upstox")
            return etf_data
            
        except Exception as e:
            logger.error(f"Error fetching ETF data from Upstox: {e}")
            return []

    
    def fetch_stock_data(self) -> List[Dict[str, any]]:
        """Fetch NSE stock data using yfinance for -5% threshold monitoring
        
        Returns:
            List of dicts with keys: name, symbol, price, change_percent
        """
        # NSE Stock symbols (250 top stocks)
        nse_stock_symbols = [
            'DEEPAKNTR.NS', 'NIACL.NS', 'IRB.NS', 'SYNGENE.NS', 'IGL.NS',
            'TATATECH.NS', 'GUJGASLTD.NS', 'AWL.NS', 'SONACOMS.NS', 'KPRMILL.NS',
            'EXIDEIND.NS', 'APARINDS.NS', 'SJVN.NS', 'LICHSGFIN.NS', 'MEDANTA.NS',
            'HONAUT.NS', 'KPITTECH.NS', 'ACC.NS', 'TATAINVEST.NS', 'APOLLOTYRE.NS',
            'GODFRYPHLP.NS', 'PREMIERENE.NS', 'JUBLFOOD.NS', 'AJANTPHARM.NS', 'TATAELXSI.NS',
            'GODREJIND.NS', 'CRISIL.NS', 'ENDURANCE.NS', 'THERMAX.NS', 'AIAENG.NS',
            'NLCINDIA.NS', 'FLUOROCHEM.NS', 'BLUESTARCO.NS', 'UCOBANK.NS', 'IREDA.NS',
            'PAGEIND.NS', 'ASTRAL.NS', 'ITCHOTELS.NS', '3MINDIA.NS', 'IPCALAB.NS',
            'COCHINSHIP.NS', 'CONCOR.NS', 'GLAXO.NS', 'UBL.NS', 'ESCORTS.NS',
            'PGHH.NS', 'KEI.NS', 'LTTS.NS', 'PETRONET.NS', 'HUDCO.NS',
            'DALBHARAT.NS', 'SUPREMEIND.NS', 'HEXT.NS', 'VOLTAS.NS', 'TIINDIA.NS',
            'JKCEMENT.NS', '360ONE.NS', 'KALYANKJIL.NS', 'BALKRISIND.NS', 'PIIND.NS',
            'MOTILALOFS.NS', 'M&MFIN.NS', 'TATACOMM.NS', 'IRCTC.NS', 'MAHABANK.NS',
            'LINDEINDIA.NS', 'GODREJPROP.NS', 'FACT.NS', 'APLAPOLLO.NS', 'BDL.NS',
            'MPHASIS.NS', 'NAM-INDIA.NS', 'GLENMARK.NS', 'PATANJALI.NS', 'JSWINFRA.NS',
            'OBEROIRLTY.NS', 'SUNDARMFIN.NS', 'MFSL.NS', 'SCHAEFFLER.NS', 'COFORGE.NS',
            'COLPAL.NS', 'ABBOTINDIA.NS', 'VMM.NS', 'ATGL.NS', 'BIOCON.NS',
            'BERGEPAINT.NS', 'SAIL.NS', 'MRF.NS', 'UPL.NS', 'PRESTIGE.NS',
            'LLOYDSME.NS', 'JSL.NS', 'SUZLON.NS', 'PHOENIXLTD.NS', 'GICRE.NS',
            'UNOMINDA.NS', 'FORTIS.NS', 'DIXON.NS', 'NATIONALUM.NS', 'AUROPHARMA.NS',
            'GVTD.NS', 'FEDERALBNK.NS', 'BHARATFORG.NS', 'TORNTPOWER.NS', 'RVNL.NS',
            'IOB.NS', 'COROMANDEL.NS', 'YESBANK.NS', 'OFSS.NS', 'ALKEM.NS',
            'NMDC.NS', 'NYKAA.NS', 'OIL.NS', 'INDUSINDBK.NS', 'IDFCFIRSTB.NS',
            'WAAREEENER.NS', 'BANKINDIA.NS', 'LTF.NS', 'POWERINDIA.NS', 'AUBANK.NS',
            'BAJAJHFL.NS', 'NTPCGREEN.NS', 'POLICYBZR.NS', 'SBICARD.NS', 'NHPC.NS',
            'BHARTIHEXA.NS', 'ENRIN.NS', 'PAYTM.NS', 'JSWENERGY.NS', 'HAVELLS.NS',
            'NAUKRI.NS', 'SRF.NS', 'BHEL.NS', 'MANKIND.NS', 'ZYDUSLIFE.NS',
            'DABUR.NS', 'SWIGGY.NS', 'CGPOWER.NS', 'INDHOTEL.NS', 'ICICIGI.NS',
            'ABCAPITAL.NS', 'HINDPETRO.NS', 'MAZDOCK.NS', 'ICICIPRULI.NS', 'RECLTD.NS',
            'UNITDSPR.NS', 'MAXHEALTH.NS', 'DRREDDY.NS', 'LODHA.NS', 'MARICO.NS',
            'SHREECEM.NS', 'LUPIN.NS', 'APOLLOHOSP.NS', 'ABB.NS', 'PERSISTENT.NS',
            'GMRAIRPORT.NS', 'SIEMENS.NS', 'IDBI.NS', 'BOSCHLTD.NS', 'GAIL.NS',
            'JINDALSTEL.NS', 'ASHOKLEY.NS', 'ADANIENSOL.NS', 'POLYCAB.NS', 'BSE.NS',
            'HDFCAMC.NS', 'INDUSTOWER.NS', 'IDEA.NS', 'CUMMINSIND.NS', 'CIPLA.NS',
            'HEROMOTOCO.NS', 'TATAPOWER.NS', 'MOTHERSON.NS', 'SOLARINDS.NS', 'INDIANB.NS',
            'TATACONSUM.NS', 'BAJAJHLDNG.NS', 'PFC.NS', 'TMPV.NS', 'GODREJCP.NS',
            'AMBUJACEM.NS', 'UNIONBANK.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'CHOLAFIN.NS',
            'CANBK.NS', 'BRITANNIA.NS', 'PNB.NS', 'ADANIGREEN.NS', 'PIDILITIND.NS',
            'DLF.NS', 'IRFC.NS', 'BPCL.NS', 'BANKBARODA.NS', 'MUTHOOTFIN.NS',
            'HDFCLIFE.NS', 'DIVISLAB.NS', 'TECHM.NS', 'VBL.NS', 'JIOFIN.NS',
            'TVSMOTOR.NS', 'LTIM.NS', 'GRASIM.NS', 'INDIGO.NS', 'SHRIRAMFIN.NS',
            'HYUNDAI.NS', 'EICHERMOT.NS', 'SBILIFE.NS', 'HINDALCO.NS', 'IOC.NS',
            'TATASTEEL.NS', 'POWERGRID.NS', 'DMART.NS', 'NESTLEIND.NS', 'WIPRO.NS',
            'COALINDIA.NS', 'BAJAJ-AUTO.NS', 'ASIANPAINT.NS', 'ETERNAL.NS', 'VEDL.NS',
            'ADANIPOWER.NS', 'ADANIENT.NS', 'JSWSTEEL.NS', 'HINDZINC.NS', 'HAL.NS',
            'ADANIPORTS.NS', 'BEL.NS', 'ONGC.NS', 'BAJAJFINSV.NS', 'NTPC.NS',
            'ULTRACEMCO.NS', 'TITAN.NS', 'SUNPHARMA.NS', 'AXISBANK.NS', 'ITC.NS',
            'KOTAKBANK.NS', 'M&M.NS', 'HCLTECH.NS', 'MARUTI.NS', 'LICI.NS',
            'LT.NS', 'HINDUNILVR.NS', 'BAJFINANCE.NS', 'INFY.NS', 'SBIN.NS',
            'ICICIBANK.NS', 'TCS.NS', 'BHARTIARTL.NS', 'HDFCBANK.NS', 'RELIANCE.NS'
        ]
        
        try:
            logger.info(f"Fetching stock data for {len(nse_stock_symbols)} stocks")
            stock_data = []
            
            for symbol in nse_stock_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='2d')
                    
                    if hist.empty or len(hist) < 2:
                        continue
                    
                    current_price = hist['Close'].iloc[-1]
                    previous_close = hist['Close'].iloc[-2]
                    change_percent = ((current_price - previous_close) / previous_close) * 100
                    
                    # Get stock name
                    info = ticker.info
                    stock_name = info.get('longName', symbol.replace('.NS', ''))
                    
                    stock_data.append({
                        'name': stock_name,
                        'symbol': symbol.replace('.NS', ''),  # Remove .NS for display
                        'price': float(current_price),
                        'change_percent': float(change_percent)
                    })
                    
                except Exception as e:
                    logger.debug(f"Error fetching {symbol}: {e}")
                    continue
            
            logger.info(f"Successfully fetched {len(stock_data)} stocks")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching stock data: {e}")
            return []

    
    def get_etfs_below_threshold(self, threshold: float) -> List[Dict[str, any]]:
        """Get ETFs that are down by more than the threshold percentage
        
        Args:
            threshold: Negative percentage threshold (e.g., -2.5)
        
        Returns:
            List of ETFs below the threshold
        """
        all_etfs = self.fetch_etf_data()
        return [etf for etf in all_etfs if etf['change_percent'] <= threshold]
